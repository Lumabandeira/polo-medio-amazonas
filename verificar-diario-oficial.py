#!/usr/bin/env python3
"""
Verificador automático do Diário Oficial da DPE/AM
Detecta novas designações do Polo Médio Amazonas e grava no Firestore.
Executa diariamente via GitHub Actions.
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

import firebase_admin
from firebase_admin import credentials, firestore

# ─── Configuração ────────────────────────────────────────────────────────────

PROJECT_DIR = Path(__file__).parent
STATE_FILE  = PROJECT_DIR / "docs" / ".estado-diario.json"
CONFIG_FILE = PROJECT_DIR / "docs" / "config.json"
LOGS_DIR    = PROJECT_DIR / "docs" / "logs"
DIARIO_URL  = "https://diario.defensoria.am.def.br/"

FIREBASE_PROJECT_ID = "polo-medio-as"
FIRESTORE_COLECAO   = "afastamentos_admin"
CRIADO_POR_AUTOMACAO = "automacao@github-actions"

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
    Envia e-mail e marca como pausada se necessário.
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

# ─── Firebase / Firestore ────────────────────────────────────────────────────

_firestore_client = None


def get_firestore_client():
    """
    Inicializa o Firebase Admin SDK (idempotente) e retorna o cliente Firestore.

    Credencial lida em ordem de precedência:
      1. Env var FIREBASE_SERVICE_ACCOUNT  (JSON string — usado no GitHub Actions)
      2. Env var GOOGLE_APPLICATION_CREDENTIALS  (caminho de arquivo — padrão gcloud)
      3. Arquivo local PROJECT_DIR / 'firebase-service-account.json'
    """
    global _firestore_client
    if _firestore_client is not None:
        return _firestore_client

    if not firebase_admin._apps:
        cred = None
        sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "").strip()
        if sa_json:
            cred_info = json.loads(sa_json)
            cred = credentials.Certificate(cred_info)
        else:
            sa_path_env = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
            candidates = [
                Path(sa_path_env) if sa_path_env else None,
                PROJECT_DIR / "firebase-service-account.json",
            ]
            for p in candidates:
                if p and p.exists():
                    cred = credentials.Certificate(str(p))
                    break
        if cred is None:
            raise RuntimeError(
                "Credencial do Firebase não encontrada. "
                "Defina FIREBASE_SERVICE_ACCOUNT (JSON) ou coloque "
                "firebase-service-account.json na raiz do projeto."
            )
        firebase_admin.initialize_app(cred, {"projectId": FIREBASE_PROJECT_ID})
        log.info(f"Firebase Admin inicializado (projeto: {FIREBASE_PROJECT_ID})")

    _firestore_client = firestore.client()
    return _firestore_client


def _mapear_defensor_abrev(nome: str) -> str:
    """Mapeia nome completo → abrev. Se não achar, devolve o nome como está."""
    if not nome:
        return ""
    alvo = nome.strip().lower()
    for nome_completo, dados in DEFENSORES_POLO.items():
        if nome_completo.lower() == alvo:
            return dados["abrev"]
    # tenta por primeiro + último nome
    partes_alvo = alvo.split()
    for nome_completo, dados in DEFENSORES_POLO.items():
        partes = nome_completo.lower().split()
        if partes_alvo and partes_alvo[0] == partes[0] and partes_alvo[-1] == partes[-1]:
            return dados["abrev"]
    return nome.strip()


_TIPO_MAP = {
    "férias": "ferias", "ferias": "ferias",
    "folga": "folga", "folgas": "folga",
    "licença especial": "licenca_especial",
    "licenca especial": "licenca_especial",
    "licença": "licenca_especial",
}


def _mapear_tipo(tipo: str) -> str:
    if not tipo:
        return "outro"
    return _TIPO_MAP.get(tipo.strip().lower(), "outro")


def _normalizar_data(data: str) -> str:
    """Aceita DD/MM/AAAA ou YYYY-MM-DD e devolve YYYY-MM-DD. '' se inválido."""
    if not data:
        return ""
    data = data.strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", data)
    if m:
        return data
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", data)
    if m:
        d, mth, y = m.groups()
        return f"{y}-{int(mth):02d}-{int(d):02d}"
    return ""


def salvar_afastamentos_firestore(afastamentos: list, edition_url: str) -> list:
    """
    Grava cada afastamento como um documento em `afastamentos_admin`.
    Retorna lista dos documentos criados (com id) para uso em notificações.

    Dedup simples: antes de inserir, busca documentos com mesmo
    (defensor, data_inicio, data_fim, tipo). Se existir, pula.
    """
    if not afastamentos:
        return []

    db = get_firestore_client()
    col = db.collection(FIRESTORE_COLECAO)
    criados = []

    for af in afastamentos:
        defensor_abrev = _mapear_defensor_abrev(af.get("defensor_ausente", ""))
        tipo_slug      = _mapear_tipo(af.get("tipo", ""))
        data_inicio    = _normalizar_data(af.get("data_inicio", ""))
        data_fim       = _normalizar_data(af.get("data_fim", ""))

        if not defensor_abrev or not data_inicio or not data_fim:
            log.warning(
                f"Afastamento descartado (campos obrigatórios faltando): "
                f"defensor={defensor_abrev!r} inicio={data_inicio!r} fim={data_fim!r}"
            )
            continue

        # Dedup
        existentes = list(
            col.where("defensor", "==", defensor_abrev)
               .where("data_inicio", "==", data_inicio)
               .where("data_fim", "==", data_fim)
               .where("tipo", "==", tipo_slug)
               .limit(1).stream()
        )
        if existentes:
            log.info(
                f"Afastamento já existe no Firestore (id={existentes[0].id}): "
                f"{defensor_abrev} {tipo_slug} {data_inicio}→{data_fim}. Pulando."
            )
            continue

        # Schema Firestore esperado pelo site (form de edicao):
        #   designacoes_dp: [{ dp, substitutos: [{ substituto, substituto_nome_externo,
        #                     data_inicio, data_fim, portaria_numero, portaria_url }] }]
        # substituto = abrev de defensor interno OU "_outro" (quando externo, com
        # o nome real em substituto_nome_externo).
        abrevs_internos = {v["abrev"] for v in DEFENSORES_POLO.values()}
        portaria_numero = (af.get("portaria_numero") or "").strip()
        processo_sei    = (af.get("processo_sei") or "").strip()

        dp_map = {}
        for d in af.get("designacoes", []) or []:
            dp_num = str(d.get("dp_numero", "")).strip().replace("ª", "").replace("DP", "").strip()
            if not dp_num:
                continue
            sub_raw = (d.get("substituto") or "").strip()
            if sub_raw:
                maybe_abrev = _mapear_defensor_abrev(sub_raw)
                if maybe_abrev in abrevs_internos:
                    substituto = maybe_abrev
                    substituto_nome_externo = ""
                else:
                    substituto = "_outro"
                    substituto_nome_externo = sub_raw
            else:
                substituto = ""
                substituto_nome_externo = ""
            dp_map.setdefault(dp_num, []).append({
                "substituto":              substituto,
                "substituto_nome_externo": substituto_nome_externo,
                "data_inicio":             data_inicio,
                "data_fim":                data_fim,
                "portaria_numero":         portaria_numero,
                "portaria_url":            edition_url,
            })
        designacoes_dp = [{"dp": dp, "substitutos": subs} for dp, subs in dp_map.items()]

        doc = {
            "defensor":        defensor_abrev,
            "tipo":            tipo_slug,
            "tipo_custom":     "" if tipo_slug != "outro" else (af.get("tipo_custom") or "").strip(),
            "data_inicio":     data_inicio,
            "data_fim":        data_fim,
            "processo_tipo":   "SEI" if processo_sei else "",
            "processo_sei":    processo_sei,
            "portaria_numero": portaria_numero,
            "portaria_url":    edition_url,
            "portaria_sei":    processo_sei,  # compat com codigo antigo
            "designacoes_dp":  designacoes_dp,
            "criado_por":      CRIADO_POR_AUTOMACAO,
            "criado_em":       firestore.SERVER_TIMESTAMP,
            "atualizado_por":  CRIADO_POR_AUTOMACAO,
            "atualizado_em":   firestore.SERVER_TIMESTAMP,
            "origem":          "automacao-diario-oficial",
        }
        _, ref = col.add(doc)
        log.info(
            f"✅ Afastamento gravado: id={ref.id} | {defensor_abrev} {tipo_slug} "
            f"{data_inicio}→{data_fim} | {len(designacoes_dp)} DP(s)"
        )
        criados.append({"id": ref.id, **doc})

    return criados

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

# Termos-gatilho: se nenhum aparece no PDF, pulamos a chamada ao Claude (custo zero)
TERMOS_POLO_MEDIO = [
    r"Polo\s+(?:do\s+)?M[eé]dio\s+Amazonas",
    r"Itacoatiara",
    r"Elton\s+Dariva",
    r"Eliaquim\s+Antunes",
    r"[ÍI]caro\s+Oliveira\s+Avelar",
    r"Elaine\s+Maria\s+Sousa",
    r"Jos[eé]\s+Ant[oô]nio\s+Pereira",
]


def _extrair_trechos_relevantes(text: str, janela: int = 1500) -> str:
    """
    Encontra todas as mencoes ao Polo Medio no texto (termos-gatilho) e
    devolve a concatenacao de janelas de +-`janela` caracteres em volta de cada
    mencao, com intervalos sobrepostos mesclados. Se nada for encontrado,
    devolve string vazia.
    """
    posicoes = set()
    for termo in TERMOS_POLO_MEDIO:
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


def parse_designations(text: str, state: dict) -> dict:
    """
    Usa Claude para identificar designações do Polo Médio no texto do PDF.
    Agrupa por afastamento (defensor + período + tipo) com lista de designações.
    Pre-filtra o texto por termos-gatilho para reduzir tokens e custo.
    """
    trechos = _extrair_trechos_relevantes(text)
    if not trechos:
        log.info("PDF sem menção a termos do Polo Médio. Pulando chamada ao Claude.")
        return {"tem_designacoes": False, "afastamentos": []}

    log.info(
        f"Trechos relevantes extraidos: {len(trechos)} caracteres "
        f"(de {len(text)} totais). Analisando com Claude API…"
    )
    client = Anthropic()

    defensores_str = "\n".join(
        f"- {nome} ({', '.join(d['dps'])})"
        for nome, d in DEFENSORES_POLO.items()
    )

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": f"""Analise este texto do Diário Oficial da Defensoria Pública do Estado do Amazonas.

Identifique APENAS designações/substituições/afastamentos do **Polo Médio Amazonas** (também chamado "Polo do Médio Amazonas").

Defensores titulares do Polo Médio e suas DPs:
{defensores_str}

Agrupe por AFASTAMENTO: um afastamento é a ausência de UM defensor em UM período por UM motivo (férias, folga, licença especial). Um mesmo afastamento pode gerar várias designações de substitutos (uma por DP do titular).

Retorne SOMENTE um JSON válido com esta estrutura:
{{
  "tem_designacoes": true,
  "afastamentos": [
    {{
      "defensor_ausente": "Nome completo do titular ausente",
      "tipo": "ferias|folga|licenca_especial|outro",
      "data_inicio": "YYYY-MM-DD",
      "data_fim": "YYYY-MM-DD",
      "portaria_numero": "Portaria nº 123/2026-GSPG/DPE/AM ou vazio",
      "processo_sei": "número SEI/SGI ou vazio",
      "designacoes": [
        {{"dp_numero": "5", "substituto": "Nome completo do substituto"}}
      ]
    }}
  ]
}}

Se não houver afastamentos do Polo Médio, retorne:
{{"tem_designacoes": false, "afastamentos": []}}

REGRAS:
- Datas SEMPRE no formato YYYY-MM-DD (ex: 2026-05-15)
- tipo em minúsculas, sem acento, valores fixos: ferias, folga, licenca_especial, outro
- Se não identificar algum campo, use string vazia "" (não use null)

TRECHOS RELEVANTES DO DIÁRIO OFICIAL (janelas de contexto em volta de menções ao Polo Médio):
{trechos}""",
        }],
    )

    total = registrar_uso(state, msg.usage.input_tokens, msg.usage.output_tokens)
    save_state(state)

    raw = msg.content[0].text
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group())
            # retrocompat: aceita "designacoes" no nível raiz (formato antigo)
            if "afastamentos" not in data and "designacoes" in data:
                data["afastamentos"] = data.pop("designacoes")
            return data
        except json.JSONDecodeError:
            log.warning("Resposta do Claude não é JSON válido")
    return {"tem_designacoes": False, "afastamentos": []}

# ─── Notificação pós-gravação ────────────────────────────────────────────────

def notificar_afastamentos_gravados(criados: list, edition_url: str, custo_total: float):
    """Envia e-mail com o resumo dos afastamentos gravados no Firestore."""
    if not criados:
        return
    resumo = "\n".join(
        f"  • {c['defensor']} ({c['tipo']}) "
        f"de {c['data_inicio']} a {c['data_fim']} "
        f"— {len(c.get('designacoes', []))} designação(ões)"
        for c in criados
    )
    send_email(
        assunto="Novos afastamentos detectados e gravados no site",
        corpo=(
            f"A automação gravou {len(criados)} afastamento(s) no Firestore.\n\n"
            f"Edição do Diário Oficial: {edition_url.split('/')[-1]}\n"
            f"Link do PDF: {edition_url}\n\n"
            f"Afastamentos:\n{resumo}\n\n"
            f"O site (https://lumabandeira.github.io/polo-medio-amazonas/) "
            f"reflete os novos dados assim que a página for recarregada.\n\n"
            f"Custo acumulado no mês: ${custo_total:.4f} / ${LIMITE_CUSTO_USD:.2f}"
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

        total_criados = 0

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
                    log.warning(f"Edição {num}: PDF sem texto extraível (pode ser imagem)")
                    state["ultima_edicao"] = max(state.get("ultima_edicao", 0), num)
                    save_state(state)
                    continue

                log.info(f"Edição {num}: {len(text)} caracteres extraídos do PDF")
                result = parse_designations(text, state)

                if verificar_limite_custo(state):
                    log.warning("Processamento interrompido por limite de custo após análise.")
                    break

                if result.get("tem_designacoes"):
                    afastamentos = result.get("afastamentos", [])
                    log.info(f"Edição {num}: {len(afastamentos)} afastamento(s) detectado(s)")
                    for af in afastamentos:
                        log.info(
                            f"  → {af.get('defensor_ausente')} | {af.get('tipo')} "
                            f"| {af.get('data_inicio')}→{af.get('data_fim')} "
                            f"| {len(af.get('designacoes', []))} DP(s)"
                        )
                    criados = salvar_afastamentos_firestore(afastamentos, edition["url"])
                    if criados:
                        custo_total = state.get("custo", {}).get("total_usd", 0.0)
                        notificar_afastamentos_gravados(criados, edition["url"], custo_total)
                        total_criados += len(criados)
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

        if total_criados:
            log.info(f"🎉 {total_criados} afastamento(s) gravado(s) no Firestore.")
        else:
            log.info("Nenhum afastamento novo para gravar.")

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
