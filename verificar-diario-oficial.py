#!/usr/bin/env python3
"""
Verificador automático do Diário Oficial da DPE/AM
Detecta novas designações do Polo Médio Amazonas e atualiza o site.
Executa diariamente às 6h via Agendador de Tarefas do Windows.
"""

import os
import io
import re
import json
import logging
import smtplib
import requests
import pdfplumber
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from anthropic import Anthropic

# ─── Configuração ────────────────────────────────────────────────────────────

PROJECT_DIR = Path(__file__).parent
INDEX_HTML  = PROJECT_DIR / "index.html"
STATE_FILE  = PROJECT_DIR / "docs" / ".estado-diario.json"
CONFIG_FILE = PROJECT_DIR / "docs" / "config.json"
LOGS_DIR    = PROJECT_DIR / "docs" / "logs"
DIARIO_URL  = "https://diario.defensoria.am.def.br/"

LIMITE_CUSTO_USD = 2.00  # Automação para se o custo mensal atingir este valor

# Preço do modelo Haiku 4.5 por token (conservador para não subestimar)
PRECO_ENTRADA_POR_TOKEN = 1.00 / 1_000_000   # $1.00 por milhão de tokens de entrada
PRECO_SAIDA_POR_TOKEN   = 5.00 / 1_000_000   # $5.00 por milhão de tokens de saída

DEFENSORES_POLO = {
    "José Antônio Pereira da Silva":  {"abrev": "jose",     "dps": ["2ª DP", "8ª DP", "10ª DP"]},
    "Ícaro Oliveira Avelar Costa":    {"abrev": "icaro",    "dps": ["1ª DP", "3ª DP", "11ª DP"]},
    "Eliaquim Antunes de Souza":      {"abrev": "eliaquim", "dps": ["4ª DP", "9ª DP"]},
    "Elton Dariva Staub":             {"abrev": "elton",    "dps": ["5ª DP", "12ª DP"]},
    "Elaine Maria Sousa Frota":       {"abrev": "elaine",   "dps": ["6ª DP", "7ª DP"]},
}

# ─── Logging ─────────────────────────────────────────────────────────────────

LOGS_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOGS_DIR / f"diario-{datetime.now().strftime('%Y-%m-%d')}.log"
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
    """Carrega configurações do arquivo config.json."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    config = {
        "email": {
            "remetente": "",
            "senha_app": "",
            "destinatario": "lumabandeira@defensoria.am.def.br",
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587
        }
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    return config


def send_email(assunto: str, corpo: str):
    """
    Envia e-mail via SMTP.
    Configurar remetente e senha_app em: docs/config.json
    """
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
        msg["Subject"] = f"[Polo Médio] {assunto}"
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
        }
    }


def save_state(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def registrar_uso(state: dict, tokens_entrada: int, tokens_saida: int) -> float:
    """
    Registra uso de tokens e retorna o custo total acumulado no mês.
    Reinicia contadores se mudou o mês.
    """
    custo = state.setdefault("custo", {
        "mes": _mes_atual(),
        "tokens_entrada": 0,
        "tokens_saida": 0,
        "total_usd": 0.0,
        "pausada": False,
    })

    # Reinicia se mudou o mês
    if custo.get("mes") != _mes_atual():
        log.info(f"Novo mês detectado. Reiniciando contadores de custo.")
        custo["mes"]           = _mes_atual()
        custo["tokens_entrada"] = 0
        custo["tokens_saida"]  = 0
        custo["total_usd"]     = 0.0
        custo["pausada"]       = False

    custo["tokens_entrada"] += tokens_entrada
    custo["tokens_saida"]   += tokens_saida
    custo_chamada = (
        tokens_entrada * PRECO_ENTRADA_POR_TOKEN +
        tokens_saida   * PRECO_SAIDA_POR_TOKEN
    )
    custo["total_usd"] = round(custo["total_usd"] + custo_chamada, 6)

    log.info(
        f"Uso registrado: +{tokens_entrada} entrada / +{tokens_saida} saída "
        f"| Custo desta chamada: ${custo_chamada:.4f} "
        f"| Acumulado no mês: ${custo['total_usd']:.4f}"
    )
    return custo["total_usd"]


def verificar_limite_custo(state: dict) -> bool:
    """
    Retorna True se o limite de custo foi atingido (automação deve parar).
    Envia WhatsApp e marca como pausada se necessário.
    """
    custo = state.get("custo", {})

    # Verifica se já estava pausada
    if custo.get("pausada"):
        log.warning(
            f"Automação pausada por limite de custo. "
            f"Custo acumulado: ${custo.get('total_usd', 0):.4f} "
            f"(limite: ${LIMITE_CUSTO_USD:.2f})"
        )
        return True

    total = custo.get("total_usd", 0.0)
    if total >= LIMITE_CUSTO_USD:
        log.warning(
            f"Limite de custo atingido: ${total:.4f} / ${LIMITE_CUSTO_USD:.2f}. Automação pausada."
        )
        send_email(
            assunto="AUTOMAÇÃO PAUSADA — Limite de custo atingido",
            corpo=(
                f"A automação de verificação do Diário Oficial DPE/AM foi pausada.\n\n"
                f"Motivo: limite de custo mensal atingido.\n"
                f"Custo acumulado: ${total:.4f}\n"
                f"Limite configurado: ${LIMITE_CUSTO_USD:.2f}\n"
                f"Mês: {custo.get('mes', _mes_atual())}\n\n"
                f"A automação retomará automaticamente no início do próximo mês."
            )
        )
        custo["pausada"] = True
        save_state(state)
        return True

    return False

# ─── Busca de edições ─────────────────────────────────────────────────────────

def get_latest_editions() -> list:
    """Scrapa o site do Diário Oficial e retorna lista de edições com URL."""
    log.info(f"Buscando edições em {DIARIO_URL}")
    r = requests.get(DIARIO_URL, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "html.parser")

    editions = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".pdf" in href.lower() and "Edicao_" in href:
            m = re.search(r"Edicao_(\d+)-(\d{4})", href)
            if m:
                num = int(m.group(1))
                url = href if href.startswith("http") else f"https://diario.defensoria.am.def.br{href}"
                if num not in editions:
                    editions[num] = url

    return sorted(
        [{"numero": n, "url": u} for n, u in editions.items()],
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

# ─── Análise com Claude ───────────────────────────────────────────────────────

def parse_designations(text: str, state: dict) -> dict:
    """Usa Claude para identificar designações do Polo Médio no texto do PDF."""
    log.info("Analisando texto com Claude API…")
    client = Anthropic()

    defensores_str = "\n".join(
        f"- {nome} ({', '.join(d['dps'])})"
        for nome, d in DEFENSORES_POLO.items()
    )

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Analise este texto do Diário Oficial da Defensoria Pública do Estado do Amazonas.

Identifique APENAS designações/substituições do **Polo Médio Amazonas** (também chamado "Polo do Médio Amazonas").

Defensores titulares do Polo Médio e suas DPs:
{defensores_str}

Retorne SOMENTE um JSON válido com esta estrutura:
{{
  "tem_designacoes": true,
  "designacoes": [
    {{
      "defensor_ausente": "Nome completo do titular ausente",
      "defensor_substituto": "Nome completo do substituto",
      "dp_numero": "2",
      "dp_nome": "2ª Defensoria Pública do Polo Médio Amazonas",
      "periodo_inicio": "DD/MM/AAAA",
      "periodo_fim": "DD/MM/AAAA",
      "tipo": "Férias|Folga|Licença Especial",
      "processo_sei": "número ou null"
    }}
  ]
}}

Se não houver designações do Polo Médio, retorne:
{{"tem_designacoes": false, "designacoes": []}}

TEXTO DO DIÁRIO OFICIAL:
{text[:15000]}""",
        }],
    )

    # Registrar uso
    total = registrar_uso(state, msg.usage.input_tokens, msg.usage.output_tokens)
    save_state(state)

    raw = msg.content[0].text
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            log.warning("Resposta do Claude não é JSON válido")
    return {"tem_designacoes": False, "designacoes": []}

# ─── Atualização do index.html ────────────────────────────────────────────────

def update_index_html(designacoes: list, edition_url: str, state: dict):
    """Usa Claude para inserir as novas designações no index.html."""
    if not designacoes:
        return

    log.info(f"Atualizando index.html com {len(designacoes)} designação(ões)…")
    client = Anthropic()

    with open(INDEX_HTML, encoding="utf-8") as f:
        html = f.read()

    # Backup
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = PROJECT_DIR / f"index.backup-{ts}.html"
    backup.write_text(html, encoding="utf-8")
    log.info(f"Backup criado: {backup.name}")

    designacoes_json = json.dumps(designacoes, ensure_ascii=False, indent=2)
    nomes_curtos = {n: d["abrev"] for n, d in DEFENSORES_POLO.items()}

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=8192,
        messages=[{
            "role": "user",
            "content": f"""Você deve inserir novas designações no index.html do site Polo Médio Amazonas 2026.

NOVAS DESIGNAÇÕES (publicadas em {edition_url}):
{designacoes_json}

Nomes curtos dos defensores no JavaScript:
{json.dumps(nomes_curtos, ensure_ascii=False)}

REGRAS DE ATUALIZAÇÃO:
1. Aba "Tabela Completa": adicione linhas HTML na tabela do mês correspondente (siga o formato das linhas existentes)
2. Objeto `detalhesAfastamentosRaw` no JS: adicione entrada no array do mês correto
3. Objeto `afastamentos` no JS: adicione o nome curto do defensor nos dias do período
4. Tabela individual do defensor (aba "Detalhes"): adicione a linha correspondente

REGRAS GERAIS:
- Não altere NADA além do necessário para inserir as novas designações
- Mantenha a formatação e indentação existentes
- Insira datas em ordem cronológica

HTML ATUAL DO SITE:
{html}

Retorne APENAS o HTML completo atualizado, sem explicações, sem blocos de código markdown.""",
        }],
    )

    # Registrar uso
    total = registrar_uso(state, msg.usage.input_tokens, msg.usage.output_tokens)
    save_state(state)

    result = msg.content[0].text.strip()
    result = re.sub(r"^```html?\n?", "", result)
    result = re.sub(r"\n?```$", "", result)

    if "<!DOCTYPE" in result or "<html" in result:
        INDEX_HTML.write_text(result, encoding="utf-8")
        log.info("✅ index.html atualizado com sucesso")

        # Notificação e-mail — site atualizado
        resumo = "\n".join(
            f"  • {d['defensor_ausente']} ({d['tipo']}) — {d['dp_nome']} "
            f"de {d['periodo_inicio']} a {d['periodo_fim']}"
            for d in designacoes
        )
        send_email(
            assunto="Site atualizado — novas designações detectadas",
            corpo=(
                f"O site do Polo Médio Amazonas foi atualizado automaticamente.\n\n"
                f"Edição do Diário Oficial: {edition_url.split('/')[-1]}\n\n"
                f"Designações encontradas:\n{resumo}\n\n"
                f"Custo acumulado no mês: ${total:.4f} / ${LIMITE_CUSTO_USD:.2f}"
            )
        )
    else:
        log.error("❌ Resposta inválida do Claude. index.html não foi alterado.")
        log.error(f"   Primeiros 300 chars: {result[:300]}")
        send_email(
            assunto="ERRO — Falha ao atualizar o site",
            corpo=(
                f"Designações foram detectadas no Diário Oficial, "
                f"mas houve falha ao atualizar o site.\n\n"
                f"Edição: {edition_url.split('/')[-1]}\n"
                f"Verifique o log em: docs/logs/"
            )
        )

# ─── Principal ────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("Verificador Diário Oficial DPE/AM — Polo Médio Amazonas")
    log.info(f"Data/hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    log.info("=" * 60)

    state = load_state()
    log.info(f"Última edição processada: {state.get('ultima_edicao', 0)}")

    custo_atual = state.get("custo", {}).get("total_usd", 0.0)
    log.info(f"Custo acumulado no mês ({_mes_atual()}): ${custo_atual:.4f} / ${LIMITE_CUSTO_USD:.2f}")

    # ── Verificar limite de custo antes de qualquer coisa ──
    if verificar_limite_custo(state):
        return

    try:
        editions = get_latest_editions()
        if not editions:
            log.warning("Nenhuma edição encontrada no site")
            return

        log.info(f"Edições disponíveis (mais recentes): {[e['numero'] for e in editions[:5]]}")

        new_editions = [e for e in editions if e["numero"] > state.get("ultima_edicao", 0)]

        if not new_editions:
            log.info("Nenhuma edição nova desde a última verificação. Tudo em dia.")
            return

        log.info(f"{len(new_editions)} edição(ões) nova(s): {[e['numero'] for e in new_editions]}")

        any_updated = False

        for edition in reversed(new_editions):  # Mais antiga primeiro
            num = edition["numero"]
            log.info(f"─── Edição {num} ───────────────────────────────")

            # Verificar custo antes de cada chamada à API
            if verificar_limite_custo(state):
                log.warning("Processamento interrompido por limite de custo.")
                break

            try:
                pdf_bytes = download_pdf(edition["url"])
                text = extract_pdf_text(pdf_bytes)

                if not text.strip():
                    log.warning(f"Edição {num}: PDF sem texto extraível (pode ser imagem)")
                    state["ultima_edicao"] = max(state.get("ultima_edicao", 0), num)
                    save_state(state)
                    continue

                log.info(f"Edição {num}: {len(text)} caracteres extraídos do PDF")
                result = parse_designations(text, state)

                # Checar custo após parse
                if verificar_limite_custo(state):
                    log.warning("Processamento interrompido por limite de custo após análise.")
                    break

                if result.get("tem_designacoes"):
                    desigs = result["designacoes"]
                    log.info(f"Edição {num}: {len(desigs)} designação(ões) encontrada(s)!")
                    for d in desigs:
                        log.info(
                            f"  → {d['defensor_ausente']} | sub: {d['defensor_substituto']} "
                            f"| {d['dp_nome']} | {d['periodo_inicio']}–{d['periodo_fim']} | {d['tipo']}"
                        )
                    update_index_html(desigs, edition["url"], state)
                    any_updated = True
                else:
                    log.info(f"Edição {num}: sem designações do Polo Médio Amazonas")

                state["ultima_edicao"] = max(state.get("ultima_edicao", 0), num)
                if num not in state.get("edicoes_processadas", []):
                    state.setdefault("edicoes_processadas", []).append(num)
                save_state(state)

            except Exception as e:
                msg_erro = f"Erro ao processar edição {num}: {e}"
                log.error(msg_erro, exc_info=True)
                send_email(
                    assunto=f"ERRO — Falha ao processar edição {num}",
                    corpo=(
                        f"A edição {num} do Diário Oficial falhou ao ser processada.\n\n"
                        f"Erro: {str(e)}\n\n"
                        f"Verifique o log em: docs/logs/"
                    )
                )

        if any_updated:
            log.info("🎉 Site atualizado com as novas designações!")
        else:
            log.info("Nenhuma atualização necessária.")

    except Exception as e:
        msg_erro = f"Erro geral: {e}"
        log.error(msg_erro, exc_info=True)
        send_email(
            assunto="ERRO GERAL — Automação Diário Oficial DPE/AM",
            corpo=(
                f"A automação falhou com um erro inesperado.\n\n"
                f"Erro: {str(e)}\n\n"
                f"Verifique o log em: docs/logs/"
            )
        )

    log.info("=" * 60)
    log.info("Verificação concluída")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
