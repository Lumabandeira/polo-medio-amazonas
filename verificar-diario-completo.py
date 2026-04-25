#!/usr/bin/env python3
"""
Verificador completo do Diário Oficial da DPE/AM — Projeto 2
Detecta TODAS as portarias relevantes ao Polo Médio Amazonas (defensores,
servidores, cidades) e atualiza docs/diario-oficial-completo-2026.json.
Executa diariamente via GitHub Actions às 04:00 de Manaus (08:00 UTC).

Diferente do Projeto 1 (verificar-diario-oficial.py), este script:
  - Tem escopo amplo: defensores + servidores + cidades do polo
  - Grava em docs/diario-oficial-completo-2026.json (não no Firestore)
  - Usa prompt Claude diferente: categoriza portarias, não extrai afastamentos
"""

import os
import io
import re
import json
import logging
import smtplib
import requests
import pdfplumber
from datetime import datetime, date
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from anthropic import Anthropic

# ─── Configuração ────────────────────────────────────────────────────────────

PROJECT_DIR  = Path(__file__).parent
STATE_FILE   = PROJECT_DIR / "docs" / ".estado-diario-completo.json"
CONFIG_FILE  = PROJECT_DIR / "docs" / "config.json"
LOGS_DIR     = PROJECT_DIR / "docs" / "logs"
DIARIO_URL   = "https://diario.defensoria.am.def.br/"
JSON_PATH    = PROJECT_DIR / "docs" / "diario-oficial-completo-2026.json"
DESIGNACOES_JSON = PROJECT_DIR / "docs" / "designacoes-2026.json"

LIMITE_CUSTO_USD = 5.00  # Limite mensal independente do Projeto 1

PRECO_ENTRADA_POR_TOKEN = 1.00 / 1_000_000
PRECO_SAIDA_POR_TOKEN   = 5.00 / 1_000_000

# Servidores do polo a monitorar (nome completo — regex usará primeiro+segundo nome)
SERVIDORES_POLO = [
    "Luma Karolyne Pantoja Bandeira",
    "Fábio Bastos de Souza",
    "Natália Cristina de Moraes",
    "Arnoud Lucas Andrade da Silva",
    "Larice Bruce Pereira",
]

# Cidades do polo
CIDADES_POLO = [
    r"Itacoatiara",
    r"S[aã]o\s+Sebasti[aã]o\s+do\s+Uatum[aã]",
    r"Itapiranga",
    r"Urucurituba",
    r"Urucar[aá]",
    r"Silves",
]

# Base fixa — expandida dinamicamente com titulares e servidores
TERMOS_GATILHO: list = []

# ─── Logging ─────────────────────────────────────────────────────────────────

LOGS_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOGS_DIR / f"diario-completo-{datetime.now().strftime('%Y-%m-%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ─── Configuração de E-mail ───────────────────────────────────────────────────

def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {
        "email": {
            "remetente": "",
            "senha_app": "",
            "destinatario": "lumabandeira@defensoria.am.def.br",
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
        }
    }


def send_email(assunto: str, corpo: str):
    config = load_config()
    cfg = config.get("email", {})
    remetente    = cfg.get("remetente", "").strip()
    senha        = cfg.get("senha_app", "").strip()
    destinatario = cfg.get("destinatario", "").strip()
    smtp_server  = cfg.get("smtp_server", "smtp.gmail.com")
    smtp_port    = int(cfg.get("smtp_port", 587))

    if not remetente or not senha or not destinatario:
        log.warning(f"E-mail não configurado. Mensagem não enviada: {assunto}")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"]    = remetente
        msg["To"]      = destinatario
        msg["Subject"] = f"[Polo Médio — DO] {assunto}"
        msg.attach(MIMEText(corpo, "plain", "utf-8"))
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(remetente, senha)
            server.send_message(msg)
        log.info(f"E-mail enviado para {destinatario}: {assunto}")
        return True
    except Exception as e:
        log.warning(f"Erro ao enviar e-mail: {e}")
        return False

# ─── Controle de custo ────────────────────────────────────────────────────────

def _mes_atual() -> str:
    return datetime.now().strftime("%Y-%m")


def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {
        "ultima_edicao": 0,
        "edicoes_processadas": [],
        "custo": {
            "mes": _mes_atual(),
            "tokens_entrada": 0,
            "tokens_saida": 0,
            "total_usd": 0.0,
            "pausada": False,
        },
    }


def save_state(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def registrar_uso(state: dict, tokens_entrada: int, tokens_saida: int) -> float:
    custo = state.setdefault("custo", {
        "mes": _mes_atual(),
        "tokens_entrada": 0,
        "tokens_saida": 0,
        "total_usd": 0.0,
        "pausada": False,
    })
    if custo.get("mes") != _mes_atual():
        log.info("Novo mês detectado. Reiniciando contadores de custo.")
        custo.update({
            "mes": _mes_atual(),
            "tokens_entrada": 0,
            "tokens_saida": 0,
            "total_usd": 0.0,
            "pausada": False,
        })
    custo["tokens_entrada"] += tokens_entrada
    custo["tokens_saida"]   += tokens_saida
    custo_chamada = (
        tokens_entrada * PRECO_ENTRADA_POR_TOKEN +
        tokens_saida   * PRECO_SAIDA_POR_TOKEN
    )
    custo["total_usd"] = round(custo["total_usd"] + custo_chamada, 6)
    log.info(
        f"Uso: +{tokens_entrada} entrada / +{tokens_saida} saída "
        f"| Chamada: ${custo_chamada:.4f} | Mês: ${custo['total_usd']:.4f}"
    )
    return custo["total_usd"]


def verificar_limite_custo(state: dict) -> bool:
    custo = state.get("custo", {})
    if custo.get("pausada"):
        log.warning(
            f"Automação (P2) pausada por limite de custo. "
            f"Acumulado: ${custo.get('total_usd', 0):.4f} / ${LIMITE_CUSTO_USD:.2f}"
        )
        return True
    total = custo.get("total_usd", 0.0)
    if total >= LIMITE_CUSTO_USD:
        log.warning(f"Limite de custo atingido: ${total:.4f}. Pausando.")
        send_email(
            assunto="AUTOMAÇÃO P2 PAUSADA — Limite de custo atingido",
            corpo=(
                f"O verificador completo do Diário Oficial foi pausado.\n\n"
                f"Custo acumulado: ${total:.4f}\n"
                f"Limite: ${LIMITE_CUSTO_USD:.2f}\n"
                f"Mês: {custo.get('mes', _mes_atual())}\n\n"
                f"Retomará automaticamente no próximo mês."
            ),
        )
        custo["pausada"] = True
        save_state(state)
        return True
    return False

# ─── Termos-gatilho ───────────────────────────────────────────────────────────

def _termo_nome(nome: str) -> str:
    """
    Gera regex de primeiro+segundo nome (adjacentes) com tolerância a acentos.
    Ex: 'Fábio Bastos de Souza' → r'F[aá]bio\s+Bastos'
    Usa primeiro+segundo porque no DO os nomes aparecem em ordem, e palavras
    como 'de'/'da' (len<=2) são descartadas antes de indexar.
    """
    partes = [p for p in nome.split() if len(p) > 2]
    if not partes:
        return re.escape(nome)
    if len(partes) == 1:
        return re.escape(partes[0])
    primeiro = re.escape(partes[0])
    segundo  = re.escape(partes[1])
    for orig, alt in [("á", "[aá]"), ("â", "[aâ]"), ("ã", "[aã]"),
                      ("é", "[eé]"), ("ê", "[eê]"), ("í", "[ií]"),
                      ("ó", "[oó]"), ("ô", "[oô]"), ("ú", "[uú]"),
                      ("ç", "[cç]")]:
        primeiro = primeiro.replace(re.escape(orig), alt)
        segundo  = segundo.replace(re.escape(orig), alt)
    return primeiro + r"\s+" + segundo


def _carregar_titulares_do_json() -> list:
    """Lê designacoes-2026.json e retorna lista de nomes de titulares vigentes."""
    if not DESIGNACOES_JSON.exists():
        return []
    try:
        with open(DESIGNACOES_JSON, encoding="utf-8") as f:
            data = json.load(f)
        defensores  = data.get("defensores", {})
        defensorias = data.get("defensorias", {})
        nomes = []
        for dp_info in defensorias.values():
            hist = dp_info.get("historico_titulares", []) or []
            vigente = next((h for h in hist if h.get("fim") is None), None)
            if not vigente:
                continue
            def_key = (vigente.get("defensor") or "").strip()
            if not def_key:
                continue
            info = defensores.get(def_key, {})
            if info.get("ativo") is False:
                continue
            nome = (info.get("nome") or def_key).strip()
            if nome and nome not in nomes:
                nomes.append(nome)
        return nomes
    except Exception as e:
        log.warning(f"Falha ao ler titulares do JSON: {e}")
        return []


def inicializar_termos():
    """Monta TERMOS_GATILHO: frase fixa + cidades + servidores + titulares vigentes."""
    global TERMOS_GATILHO

    termos = [r"Polo\s+(?:do\s+)?M[eé]dio\s+Amazonas"]

    # Cidades do polo
    termos.extend(CIDADES_POLO)

    # Servidores fixos
    for nome in SERVIDORES_POLO:
        termos.append(_termo_nome(nome))

    # Titulares vigentes (do JSON local)
    titulares = _carregar_titulares_do_json()
    vistos = set()
    for nome in titulares:
        partes = [p for p in nome.split() if len(p) > 2]
        if len(partes) < 2:
            continue
        chave = (partes[0].lower(), partes[-1].lower())
        if chave not in vistos:
            vistos.add(chave)
            termos.append(_termo_nome(nome))

    TERMOS_GATILHO = termos
    log.info(f"Termos-gatilho ativos ({len(TERMOS_GATILHO)}): {TERMOS_GATILHO}")

# ─── Busca de edições ─────────────────────────────────────────────────────────

def get_latest_editions() -> list:
    log.info(f"Buscando edições em {DIARIO_URL}")
    r = requests.get(DIARIO_URL, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "html.parser")

    _MESES_PT = {
        "janeiro": "01", "fevereiro": "02", "março": "03", "marco": "03",
        "abril": "04", "maio": "05", "junho": "06", "julho": "07",
        "agosto": "08", "setembro": "09", "outubro": "10",
        "novembro": "11", "dezembro": "12",
    }

    editions = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".pdf" in href.lower() and "Edicao_" in href:
            m = re.search(r"Edicao_(\d+)-(\d{4})(?:_(\d{8}))?", href)
            if m:
                num = int(m.group(1))
                ano = m.group(2)
                url = href if href.startswith("http") else f"https://diario.defensoria.am.def.br{href}"
                data_pub = ""
                if m.group(3):
                    # Formato antigo: Edicao_NNNN-AAAA_DDMMAAAA
                    d_str = m.group(3)
                    data_pub = f"{ano}-{d_str[2:4]}-{d_str[:2]}"
                else:
                    # Formato novo: Edicao_NNNN-AAAA__publicada_em_DD_mes_de_AAAA
                    m2 = re.search(r"publicada_em_(\d{1,2})_([a-zA-Z\u00c0-\u00ff]+)_de_(\d{4})", href, re.IGNORECASE)
                    if m2:
                        dia = m2.group(1).zfill(2)
                        mes = _MESES_PT.get(m2.group(2).lower(), "")
                        ano2 = m2.group(3)
                        if mes:
                            data_pub = f"{ano2}-{mes}-{dia}"
                if num not in editions:
                    editions[num] = {"url": url, "data_publicacao": data_pub}

    return sorted(
        [{"numero": n, "url": d["url"], "data_publicacao": d["data_publicacao"]}
         for n, d in editions.items()],
        key=lambda x: x["numero"],
        reverse=True,
    )

# ─── PDF ─────────────────────────────────────────────────────────────────────

def download_pdf(url: str) -> bytes:
    log.info(f"Baixando PDF: {url}")
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.content


def extract_pdf_text(pdf_bytes: bytes) -> str:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n".join(pages)

# ─── Pré-filtro ───────────────────────────────────────────────────────────────

def _extrair_trechos_relevantes(text: str, janela: int = 1500) -> str:
    """
    Encontra todas as menções aos termos-gatilho e devolve janelas de ±janela
    chars em volta de cada menção, com intervalos sobrepostos mesclados.
    """
    posicoes = set()
    for termo in TERMOS_GATILHO:
        for m in re.finditer(termo, text, re.IGNORECASE):
            posicoes.add(m.start())
    if not posicoes:
        return ""
    intervalos = sorted(
        (max(0, p - janela), min(len(text), p + janela)) for p in posicoes
    )
    merged = []
    for ini, fim in intervalos:
        if merged and ini <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], fim))
        else:
            merged.append([ini, fim])
    return "\n\n[...corte...]\n\n".join(text[i:f] for i, f in merged)

# ─── Análise com Claude ───────────────────────────────────────────────────────

def parse_portarias(text: str, state: dict) -> dict:
    """
    Usa Claude Haiku para identificar e categorizar todas as portarias relevantes
    ao Polo Médio no texto do PDF. Retorna lista no formato portarias_estruturadas.
    """
    trechos = _extrair_trechos_relevantes(text)
    if not trechos:
        log.info("PDF sem menção a termos do Polo Médio/servidores/cidades. Pulando Claude.")
        return {"tem_portarias": False, "portarias": []}

    log.info(
        f"Trechos relevantes: {len(trechos)} chars (de {len(text)} totais). "
        f"Analisando com Claude…"
    )
    # Usa chave dedicada ao Projeto 2 se disponível, senão cai na chave padrão
    api_key = os.environ.get("ANTHROPIC_API_KEY_COMPLETO") or os.environ.get("ANTHROPIC_API_KEY")
    client = Anthropic(api_key=api_key)

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": f"""Analise este texto do Diário Oficial da Defensoria Pública do Estado do Amazonas.

Identifique TODAS as portarias que mencionam o Polo Médio Amazonas ou qualquer de seus integrantes (defensores, servidores, estagiários) ou cidades do polo (Itacoatiara, São Sebastião do Uatumã, Itapiranga, Urucurituba, Urucará, Silves).

Para cada portaria relevante, extraia:
- "numero": número completo da portaria (ex: "Portaria Nº 123/2026-GSPG/DPE/AM")
- "sei": número SEI no formato XX.X.XXXXXXX-X, ou null se ausente
- "sgi": número SGI, ou null se ausente
- "categorias": lista com todas as categorias aplicáveis (ver abaixo)
- "trechos": lista com os incisos/parágrafos relevantes, em texto exato (não parafraseie)
- "resumo": frase curta (1-2 linhas) descrevendo o ato em linguagem simples

Categorias disponíveis (use quantas se aplicarem):
- "polo_medio": menciona o Polo Médio Amazonas pelo nome
- "defensor": envolve defensor público (designação, afastamento, substituição)
- "servidor": envolve servidor administrativo
- "substituicao": designação de substituto para cobrir ausência
- "nomeacao_diretoria": nomeação/cessação de cargo de direção ou coordenação (FGD, etc.)
- "comarca": menciona comarca ou cidade do polo
- "projeto": envolve projeto social ou de atendimento à população
- "plantao": escala de plantão (fins de semana, feriados)
- "coordenacao": ato de coordenação regional do polo
- "designacoes": designação de atuação cumulativa

Retorne SOMENTE um JSON válido com esta estrutura:
{{
  "tem_portarias": true,
  "portarias": [
    {{
      "numero": "Portaria Nº 123/2026-GSPG/DPE/AM",
      "sei": "26.0.000123-4",
      "sgi": null,
      "categorias": ["polo_medio", "defensor", "substituicao"],
      "trechos": ["I - DESIGNAR, cumulativamente, a Defensora..."],
      "resumo": "Designa fulano para atuar na Xª DP do Polo Médio em DD-DD/MM/AAAA"
    }}
  ]
}}

Se não houver portarias relevantes ao Polo Médio:
{{"tem_portarias": false, "portarias": []}}

REGRAS:
- Inclua os trechos em texto exato, não parafraseie
- O resumo deve ser conciso e informativo (quem, o quê, quando)
- Se não identificar o número SEI/SGI, use null (não use string vazia)
- Inclua apenas portarias genuinamente relacionadas ao polo ou seus integrantes

TRECHOS DO DIÁRIO OFICIAL (janelas de contexto em volta das menções):
{trechos}""",
        }],
    )

    total = registrar_uso(state, msg.usage.input_tokens, msg.usage.output_tokens)
    save_state(state)

    raw = msg.content[0].text
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            log.warning("Resposta do Claude não é JSON válido")
    return {"tem_portarias": False, "portarias": []}

# ─── Atualização do JSON ──────────────────────────────────────────────────────

def _formatar_data(data_iso: str) -> str:
    """'2026-01-05' → '05/01/2026'"""
    try:
        d = date.fromisoformat(data_iso)
        return d.strftime("%d/%m/%Y")
    except Exception:
        return data_iso


def load_json_diario() -> list:
    if JSON_PATH.exists():
        with open(JSON_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_json_diario(data: list):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log.info(f"JSON atualizado: {JSON_PATH} ({len(data)} edições)")


def atualizar_json_diario(
    portarias: list,
    edition: dict,
) -> int:
    """
    Adiciona ou mescla portarias_estruturadas da edição no JSON.
    Retorna o número de portarias novas inseridas.
    """
    data = load_json_diario()
    num  = edition["numero"]
    url  = edition["url"]
    data_pub = edition.get("data_publicacao", "")

    # Procura entrada existente
    entry = next((e for e in data if e.get("edicao") == num), None)
    if entry is None:
        entry = {
            "edicao":         num,
            "data":           data_pub,
            "data_formatada": _formatar_data(data_pub),
            "url":            url,
            "portarias":      [],
            "portarias_estruturadas": [],
        }
        data.append(entry)
        log.info(f"Edição {num} criada no JSON.")
    else:
        log.info(f"Edição {num} já existe no JSON. Mesclando portarias.")
        if not entry.get("data") and data_pub:
            entry["data"] = data_pub
            entry["data_formatada"] = _formatar_data(data_pub)
            log.info(f"Edição {num}: data preenchida retroativamente → {data_pub}")

    # Dedup por número de portaria
    existentes = {p.get("numero", "").strip() for p in entry.get("portarias_estruturadas", [])}
    novas = 0
    for p in portarias:
        numero = (p.get("numero") or "").strip()
        if numero and numero not in existentes:
            entry.setdefault("portarias_estruturadas", []).append(p)
            existentes.add(numero)
            novas += 1
            log.info(f"  + Portaria nova: {numero}")
        elif numero:
            log.info(f"  = Portaria já existe, pulando: {numero}")

    # Mantém ordenado por número de edição
    data.sort(key=lambda e: e.get("edicao", 0))
    save_json_diario(data)
    return novas

# ─── Inicialização do estado a partir do JSON existente ──────────────────────

def _ultima_edicao_do_json() -> int:
    """Retorna o maior número de edição presente no JSON atual."""
    data = load_json_diario()
    if not data:
        return 0
    return max(e.get("edicao", 0) for e in data)

# ─── Principal ────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("Verificador Completo — Diário Oficial DPE/AM (Projeto 2)")
    log.info(f"Data/hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    log.info("=" * 60)

    state = load_state()

    # Na primeira execução, inicializa ultima_edicao a partir do JSON existente
    # para não reprocessar edições que já foram inseridas pelo backfill.
    if state.get("ultima_edicao", 0) == 0:
        ultima_do_json = _ultima_edicao_do_json()
        if ultima_do_json > 0:
            state["ultima_edicao"] = ultima_do_json
            save_state(state)
            log.info(
                f"Primeira execução: ultima_edicao inicializado em {ultima_do_json} "
                f"(maior edição presente no JSON)."
            )

    log.info(f"Última edição processada: {state.get('ultima_edicao', 0)}")
    custo_atual = state.get("custo", {}).get("total_usd", 0.0)
    log.info(f"Custo acumulado ({_mes_atual()}): ${custo_atual:.4f} / ${LIMITE_CUSTO_USD:.2f}")

    if verificar_limite_custo(state):
        return

    inicializar_termos()

    try:
        editions = get_latest_editions()
        if not editions:
            log.warning("Nenhuma edição encontrada no site.")
            return

        log.info(f"Edições disponíveis (recentes): {[e['numero'] for e in editions[:5]]}")

        new_editions = [e for e in editions if e["numero"] > state.get("ultima_edicao", 0)]
        if not new_editions:
            log.info("Nenhuma edição nova. Tudo em dia.")
            return

        log.info(f"{len(new_editions)} edição(ões) nova(s): {[e['numero'] for e in new_editions]}")

        total_novas = 0

        for edition in reversed(new_editions):  # Mais antiga primeiro
            num = edition["numero"]
            log.info(f"─── Edição {num} ───────────────────────────────")

            if verificar_limite_custo(state):
                log.warning("Processamento interrompido por limite de custo.")
                break

            try:
                pdf_bytes = download_pdf(edition["url"])
                text = extract_pdf_text(pdf_bytes)

                if not text.strip():
                    log.warning(f"Edição {num}: PDF sem texto extraível.")
                    state["ultima_edicao"] = max(state.get("ultima_edicao", 0), num)
                    save_state(state)
                    continue

                log.info(f"Edição {num}: {len(text)} chars extraídos do PDF.")
                result = parse_portarias(text, state)

                if verificar_limite_custo(state):
                    break

                if result.get("tem_portarias"):
                    portarias = result.get("portarias", [])
                    log.info(f"Edição {num}: {len(portarias)} portaria(s) detectada(s).")
                    for p in portarias:
                        log.info(
                            f"  → {p.get('numero')} | {p.get('categorias')} | {p.get('resumo', '')[:80]}"
                        )
                    novas = atualizar_json_diario(portarias, edition)
                    total_novas += novas
                else:
                    log.info(f"Edição {num}: sem portarias relevantes ao polo.")

                state["ultima_edicao"] = max(state.get("ultima_edicao", 0), num)
                if num not in state.get("edicoes_processadas", []):
                    state.setdefault("edicoes_processadas", []).append(num)
                save_state(state)

            except Exception as e:
                log.error(f"Erro ao processar edição {num}: {e}", exc_info=True)
                send_email(
                    assunto=f"ERRO — Falha ao processar edição {num} (P2)",
                    corpo=(
                        f"O verificador completo (Projeto 2) falhou na edição {num}.\n\n"
                        f"Erro: {str(e)}\n\n"
                        f"Verifique o log em: docs/logs/"
                    ),
                )

        if total_novas:
            log.info(f"🎉 {total_novas} portaria(s) nova(s) adicionada(s) ao JSON.")
            send_email(
                assunto=f"{total_novas} portaria(s) nova(s) no Diário Oficial",
                corpo=(
                    f"O verificador completo detectou {total_novas} portaria(s) nova(s) "
                    f"e atualizou docs/diario-oficial-completo-2026.json.\n\n"
                    f"O site refletirá as mudanças após o commit do GitHub Actions.\n"
                    f"Acesse: https://lumabandeira.github.io/polo-medio-amazonas/\n\n"
                    f"Custo acumulado no mês: ${state.get('custo', {}).get('total_usd', 0):.4f} "
                    f"/ ${LIMITE_CUSTO_USD:.2f}"
                ),
            )
        else:
            log.info("Nenhuma portaria nova para adicionar.")

    except Exception as e:
        log.error(f"Erro geral: {e}", exc_info=True)
        send_email(
            assunto="ERRO GERAL — Automação Diário Oficial Completo (P2)",
            corpo=f"A automação (Projeto 2) falhou com erro inesperado.\n\nErro: {str(e)}\n\nVerifique docs/logs/",
        )

    log.info("=" * 60)
    log.info("Verificação completa concluída")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
