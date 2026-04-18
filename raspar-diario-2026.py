#!/usr/bin/env python3
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
Raspa TODOS os Diários Oficiais da DPE/AM de 01/01/2026 a 08/04/2026.
Extrai portarias completas que mencionam "Polo Médio Amazonas".
Saída: docs/diario-oficial-polo-medio-2026.json  (dados)
       docs/diario-oficial-polo-medio-2026.md    (leitura humana)
"""

import io
import re
import json
import time
import requests
import pdfplumber
from pathlib import Path
from datetime import date, timedelta

# ─── Configuração ─────────────────────────────────────────────────────────────

PROJECT_DIR = Path(__file__).parent
SAIDA_JSON  = PROJECT_DIR / "docs" / "diario-oficial-polo-medio-2026.json"
SAIDA_MD    = PROJECT_DIR / "docs" / "diario-oficial-polo-medio-2026.md"
BASE_URL    = "https://diario.defensoria.am.def.br/wp-content/uploads"

MESES_PT = {
    1:"janeiro", 2:"fevereiro", 3:"marco", 4:"abril",
    5:"maio", 6:"junho", 7:"julho", 8:"agosto",
    9:"setembro", 10:"outubro", 11:"novembro", 12:"dezembro",
}

# Âncoras conhecidas (edição → data exata)
ANCORAS = {
    2564: date(2026, 1,  2),
    2620: date(2026, 3, 26),
    2621: date(2026, 3, 27),
    2622: date(2026, 3, 30),
    2623: date(2026, 3, 31),
    2624: date(2026, 4,  1),
    2625: date(2026, 4,  6),  # corrigido: real = 06/04
    2626: date(2026, 4,  7),  # corrigido: real = 07/04
    2627: date(2026, 4,  8),
    2628: date(2026, 4,  9),
    2629: date(2026, 4, 10),
    2630: date(2026, 4, 13),
    2631: date(2026, 4, 14),
    2632: date(2026, 4, 15),
    2633: date(2026, 4, 16),
    2634: date(2026, 4, 17),
}

EDICAO_MIN  = 2627
EDICAO_MAX  = 2636
TERMO_BUSCA = "polo médio"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0"})

# ─── URL e verificação ────────────────────────────────────────────────────────

def construir_url(edicao: int, d: date) -> str:
    return (
        f"{BASE_URL}/{d.year}/{d.month:02d}/"
        f"Edicao_{edicao}-{d.year}__publicada_em_"
        f"{d.day:02d}_{MESES_PT[d.month]}_de_{d.year}.pdf"
    )


def url_existe(url: str) -> bool:
    try:
        r = SESSION.head(url, timeout=8, allow_redirects=True)
        return r.status_code == 200
    except Exception:
        return False


def estimar_data(edicao: int) -> date:
    """
    Interpola linearmente entre as âncoras conhecidas
    para estimar a data de uma edição.
    """
    # Encontra âncoras vizinhas
    antes = {n: d for n, d in ANCORAS.items() if n <= edicao}
    depois = {n: d for n, d in ANCORAS.items() if n >= edicao}

    if edicao in ANCORAS:
        return ANCORAS[edicao]

    if antes and depois:
        n_ant, d_ant = max(antes.items(), key=lambda x: x[0])
        n_dep, d_dep = min(depois.items(), key=lambda x: x[0])
        frac = (edicao - n_ant) / (n_dep - n_ant)
        delta_dias = (d_dep - d_ant).days
        return d_ant + timedelta(days=round(frac * delta_dias))

    # Extrapolação simples (1,5 dias/edição)
    ref_n, ref_d = min(ANCORAS.items(), key=lambda x: abs(x[0] - edicao))
    return ref_d + timedelta(days=round((edicao - ref_n) * 1.5))


def encontrar_url(edicao: int) -> tuple[str, date] | tuple[None, None]:
    """
    Para uma edição, busca a URL correta testando datas em torno da estimativa.
    Janela: estimativa ± 7 dias.
    """
    base = estimar_data(edicao)
    # Testa primeiro a data exata estimada, depois expande
    candidatas = sorted(
        [base + timedelta(days=d) for d in range(-7, 8)],
        key=lambda d: abs((d - base).days)
    )
    for d in candidatas:
        if d.year != 2026:
            continue
        url = construir_url(edicao, d)
        if url_existe(url):
            return url, d
    return None, None

# ─── PDF ─────────────────────────────────────────────────────────────────────

def baixar_pdf(url: str) -> bytes | None:
    try:
        r = SESSION.get(url, timeout=60)
        r.raise_for_status()
        return r.content
    except Exception as e:
        print(f"    Erro download: {e}")
        return None


def extrair_texto(pdf_bytes: bytes) -> str:
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        print(f"    Erro extração: {e}")
        return ""

# ─── Extração de portarias ────────────────────────────────────────────────────

def extrair_portarias_polo_medio(texto: str) -> list[str]:
    """
    Divide o texto em blocos de portaria/ato e retorna
    os que contêm 'Polo Médio Amazonas'.
    """
    if not texto:
        return []

    # Tenta dividir nos cabeçalhos de ato (PORTARIA Nº X, RESOLUÇÃO Nº X, etc.)
    padrao = r"(?=(?:PORTARIA|RESOLU[ÇC][ÃA]O|DESIGNA[ÇC][ÃA]O|ATO|ORDEM\s+DE\s+SERVI[ÇC]O|EXTRATO)\s+N[ºo°]?\s*[\d/])"
    blocos = re.split(padrao, texto, flags=re.IGNORECASE)

    com_polo = [b.strip() for b in blocos if TERMO_BUSCA in b.lower() and len(b.strip()) > 50]

    # Fallback: retorna parágrafos com o termo
    if not com_polo:
        paragrafos = [p.strip() for p in texto.split("\n\n")]
        com_polo = [p for p in paragrafos if TERMO_BUSCA in p.lower() and len(p) > 50]

    return com_polo

# ─── Geração de relatório ─────────────────────────────────────────────────────

def salvar_json(resultados: list):
    existentes = {}
    if SAIDA_JSON.exists():
        with open(SAIDA_JSON, encoding="utf-8") as f:
            existentes = {e["edicao"]: e for e in json.load(f)}
    for r in resultados:
        existentes[r["edicao"]] = r
    merged = sorted(existentes.values(), key=lambda e: e["edicao"])
    with open(SAIDA_JSON, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print(f"  → JSON: {SAIDA_JSON} ({len(merged)} edições total)")


def salvar_markdown(resultados: list):
    com_polo = [r for r in resultados if r.get("portarias")]
    total_portarias = sum(len(r["portarias"]) for r in com_polo)

    linhas = [
        "# Diário Oficial DPE/AM — Polo Médio Amazonas 2026",
        "",
        f"**Período:** 01/01/2026 a 08/04/2026",
        f"**Edições verificadas:** {len(resultados)}",
        f"**Edições com menção ao Polo Médio:** {len(com_polo)}",
        f"**Total de portarias/atos transcritos:** {total_portarias}",
        "",
        "---",
        "",
    ]

    for r in com_polo:
        linhas += [
            f"## Edição {r['edicao']} — {r['data_formatada']}",
            "",
            f"**Link:** [{r['url'].split('/')[-1]}]({r['url']})",
            "",
        ]
        for i, portaria in enumerate(r["portarias"], 1):
            linhas += [
                f"### Ato {i}",
                "",
                portaria,
                "",
                "---",
                "",
            ]

    with open(SAIDA_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    print(f"  → Markdown: {SAIDA_MD}")

# ─── Principal ────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Raspagem Diário Oficial DPE/AM — Polo Médio 2026")
    print("=" * 60)

    resultados = []
    total_edicoes = EDICAO_MAX - EDICAO_MIN + 1

    for i, edicao in enumerate(range(EDICAO_MIN, EDICAO_MAX + 1), 1):
        print(f"\n[{i:2d}/{total_edicoes}] Edição {edicao}", end="  ")

        url, data_pub = encontrar_url(edicao)
        if not url:
            print("— URL não encontrada (provavelmente não publicada)")
            continue

        data_fmt = data_pub.strftime("%d/%m/%Y")
        print(f"→ {data_fmt}")

        pdf_bytes = baixar_pdf(url)
        if not pdf_bytes:
            resultados.append({
                "edicao": edicao, "data": data_pub.isoformat(),
                "data_formatada": data_fmt, "url": url,
                "portarias": [], "erro": "Falha no download"
            })
            continue

        texto = extrair_texto(pdf_bytes)
        if not texto.strip():
            print("    PDF sem texto extraível")
            resultados.append({
                "edicao": edicao, "data": data_pub.isoformat(),
                "data_formatada": data_fmt, "url": url,
                "portarias": [], "erro": "PDF sem texto"
            })
            continue

        portarias = extrair_portarias_polo_medio(texto)
        if portarias:
            print(f"    ✅ {len(portarias)} portaria(s) com 'Polo Médio' encontrada(s)")
            for p in portarias:
                print(f"       → {p[:90].replace(chr(10),' ')}…")
        else:
            print(f"    — sem menção ao Polo Médio")

        resultados.append({
            "edicao": edicao, "data": data_pub.isoformat(),
            "data_formatada": data_fmt, "url": url,
            "portarias": portarias
        })

        time.sleep(0.4)

    # ─── Resumo ───────────────────────────────────────────────────────────────
    com_polo = [r for r in resultados if r.get("portarias")]
    print("\n" + "=" * 60)
    print(f"Concluído!")
    print(f"  Edições processadas : {len(resultados)}")
    print(f"  Com Polo Médio      : {len(com_polo)}")
    print(f"  Total de portarias  : {sum(len(r['portarias']) for r in com_polo)}")
    print("=" * 60)

    salvar_json(resultados)
    salvar_markdown(resultados)


if __name__ == "__main__":
    main()
