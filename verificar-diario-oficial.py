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
FIRESTORE_COLECAO_REMOCOES  = "remocoes_admin"
CRIADO_POR_AUTOMACAO = "automacao@github-actions"

LIMITE_CUSTO_USD = 2.00  # Automação para se o custo mensal atingir este valor

# Preço do modelo Haiku 4.5 por token (conservador para não subestimar)
PRECO_ENTRADA_POR_TOKEN = 1.00 / 1_000_000   # $1.00 por milhão de tokens de entrada
PRECO_SAIDA_POR_TOKEN   = 5.00 / 1_000_000   # $5.00 por milhão de tokens de saída

# Preenchido dinamicamente em `inicializar_defensores_e_termos()` a partir de
# docs/designacoes-2026.json + coleção Firestore `titulares_admin`.
DEFENSORES_POLO: dict = {}

DESIGNACOES_JSON = PROJECT_DIR / "docs" / "designacoes-2026.json"
FIRESTORE_COLECAO_TITULARES = "titulares_admin"

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


def salvar_afastamentos_firestore(
    afastamentos: list,
    edition_url: str,
    edition_num: str = "",
    data_publicacao_do: str = "",
) -> list:
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

        if not defensor_abrev or not data_inicio:
            log.warning(
                f"Afastamento descartado (campos obrigatórios faltando): "
                f"defensor={defensor_abrev!r} inicio={data_inicio!r} fim={data_fim!r}"
            )
            continue

        precisa_revisao = not data_fim
        motivo_revisao  = "sem data fim — designação aberta (\"a contar do dia X\")" if precisa_revisao else ""

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
            "defensor":          defensor_abrev,
            "tipo":              tipo_slug,
            "tipo_custom":       "" if tipo_slug != "outro" else (af.get("tipo_custom") or "").strip(),
            "data_inicio":       data_inicio,
            "data_fim":          data_fim,
            "processo_tipo":     "SEI" if processo_sei else "",
            "processo_sei":      processo_sei,
            "portaria_numero":   portaria_numero,
            "portaria_url":      edition_url,
            "portaria_sei":      processo_sei,  # compat com codigo antigo
            "designacoes_dp":    designacoes_dp,
            "criado_por":        CRIADO_POR_AUTOMACAO,
            "criado_em":         firestore.SERVER_TIMESTAMP,
            "atualizado_por":    CRIADO_POR_AUTOMACAO,
            "atualizado_em":     firestore.SERVER_TIMESTAMP,
            "origem":            "automacao-diario-oficial",
            "lido":              False,
            "edicao_do":         str(edition_num),
            "data_publicacao_do": data_publicacao_do,
            "precisa_revisao":   precisa_revisao,
            "motivo_revisao":    motivo_revisao,
        }
        _, ref = col.add(doc)
        log.info(
            f"✅ Afastamento gravado: id={ref.id} | {defensor_abrev} {tipo_slug} "
            f"{data_inicio}→{data_fim} | {len(designacoes_dp)} DP(s)"
        )
        criados.append({"id": ref.id, **doc})

    return criados

# ─── Concurso de Remoção ──────────────────────────────────────────────────────

def _texto_tem_remocao_polo_medio(text: str) -> bool:
    """Verifica se o PDF contém resultado de concurso de remoção afetando o Polo Médio."""
    tem_concurso = any(re.search(t, text, re.IGNORECASE) for t in TERMOS_REMOCAO)
    if not tem_concurso:
        return False
    return bool(re.search(r"Polo\s+(?:do\s+)?M[eé]dio\s+Amazonas", text, re.IGNORECASE))


def _extrair_trechos_remocao(text: str, janela: int = 4000) -> str:
    """Extrai janelas de contexto em torno de menções a Concurso de Remoção."""
    posicoes = set()
    for termo in TERMOS_REMOCAO:
        for m in re.finditer(termo, text, re.IGNORECASE):
            posicoes.add(m.start())
    if not posicoes:
        return ""
    intervalos = sorted(
        (max(0, p - 500), min(len(text), p + janela)) for p in posicoes
    )
    merged = []
    for ini, fim in intervalos:
        if merged and ini <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], fim))
        else:
            merged.append([ini, fim])
    return "\n\n[...corte...]\n\n".join(text[i:f] for i, f in merged)


def parse_remocao(text: str, state: dict) -> dict:
    """
    Usa Claude para extrair dados de concurso de remoção que afete o Polo Médio.
    Retorna dict com tem_remocao, portaria_numero, concurso, data_vigencia,
    saindo[] e chegando[].
    """
    trechos = _extrair_trechos_remocao(text)
    if not trechos:
        return {"tem_remocao": False}

    log.info(
        f"Trechos de remoção extraídos: {len(trechos)} caracteres. Analisando com Claude…"
    )
    client = Anthropic()

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": f"""Analise este texto do Diário Oficial da Defensoria Pública do Estado do Amazonas.

Identifique se há resultado de **Concurso de Remoção** de Defensores Públicos que afete o **Polo do Médio Amazonas** (também chamado "Polo Médio Amazonas").

Retorne SOMENTE um JSON válido:
{{
  "tem_remocao": true,
  "portaria_numero": "Portaria nº 602/2026-GDPG/DPE/AM",
  "concurso": "4º Concurso de Remoção de 2026",
  "data_vigencia": "2026-05-02",
  "saindo": [
    {{"defensor": "Nome Completo", "dp_no_polo": "2ª Defensoria Pública do Polo do Médio Amazonas", "dp_destino": "2ª Defensoria Pública do Polo do Rio Negro Solimões"}}
  ],
  "chegando": [
    {{"defensor": "Nome Completo", "dp_origem": "5ª Defensoria Pública do Polo do Baixo Amazonas", "dp_no_polo": "5ª Defensoria Pública do Polo do Médio Amazonas"}}
  ]
}}

Se não houver concurso de remoção afetando o Polo Médio Amazonas:
{{"tem_remocao": false}}

REGRAS:
- data_vigencia em formato YYYY-MM-DD (ex: "2026-05-02")
- Se a data não estiver explícita, use string vazia ""
- Inclua APENAS defensores cujo ORIGEM ou DESTINO seja uma DP do Polo do Médio Amazonas
- saindo: defensores para quem a DP de ORIGEM é do Polo Médio Amazonas
- chegando: defensores para quem a DP de DESTINO é do Polo Médio Amazonas

TRECHOS DO DIÁRIO OFICIAL:
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
            log.warning("Resposta do Claude (remoção) não é JSON válido")
    return {"tem_remocao": False}


def salvar_remocao_firestore(
    data: dict,
    edition_url: str,
    edition_num: str = "",
    data_publicacao_do: str = "",
) -> dict | None:
    """
    Grava resultado de concurso de remoção em `remocoes_admin`.
    Dedup por portaria_numero.
    """
    portaria_numero = (data.get("portaria_numero") or "").strip()
    if not portaria_numero:
        log.warning("Remoção sem número de portaria — descartada")
        return None

    db = get_firestore_client()
    col = db.collection(FIRESTORE_COLECAO_REMOCOES)

    existentes = list(col.where("portaria_numero", "==", portaria_numero).limit(1).stream())
    if existentes:
        log.info(f"Remoção já gravada (portaria={portaria_numero!r}). Pulando.")
        return None

    doc = {
        "portaria_numero": portaria_numero,
        "portaria_url":    edition_url,
        "edicao_do":       str(edition_num),
        "data_publicacao": data_publicacao_do,
        "data_vigencia":   (_normalizar_data(data.get("data_vigencia") or "") or ""),
        "concurso":        (data.get("concurso") or "").strip(),
        "saindo":          data.get("saindo") or [],
        "chegando":        data.get("chegando") or [],
        "lido":            False,
        "origem":          "automacao-diario-oficial",
        "criado_por":      CRIADO_POR_AUTOMACAO,
        "criado_em":       firestore.SERVER_TIMESTAMP,
    }
    _, ref = col.add(doc)
    log.info(
        f"✅ Concurso de remoção gravado: id={ref.id} | {portaria_numero} "
        f"| {len(doc['saindo'])} saindo / {len(doc['chegando'])} chegando"
    )
    return {"id": ref.id, **doc}

# ─── Busca de edições ─────────────────────────────────────────────────────────

def get_latest_editions() -> list:
    """Scrapa o site do Diário Oficial e retorna lista de edições com URL."""
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
                # Data no formato DDMMYYYY → YYYY-MM-DD
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

# ─── Análise com Claude ───────────────────────────────────────────────────────

# Termos-gatilho: se nenhum aparece no PDF, pulamos a chamada ao Claude (custo zero).
# A lista é construída dinamicamente em `inicializar_defensores_e_termos()`:
#   1. Frase fixa "Polo (do) Médio Amazonas"
#   2. Primeiro + segundo nome de cada titular vigente (JSON + Firestore)
# Cidades e servidores foram REMOVIDOS intencionalmente — o Diário Oficial
# designa "Nª Defensoria Pública do Estado do Amazonas", nunca pela cidade,
# e servidores são escopo de outra automação (ver CLAUDE.md, Projeto 2).
TERMOS_POLO_MEDIO: list = [
    r"Polo\s+(?:do\s+)?M[eé]dio\s+Amazonas",
]

TERMOS_REMOCAO: list = [
    r"[Cc]oncurso\s+de\s+[Rr]emo[çc][ãa]o",
]


def _carregar_titulares_vigentes() -> dict:
    """
    Lê `docs/designacoes-2026.json` e aplica overrides do Firestore
    (`titulares_admin/{dpKey}`). Retorna dict no formato:
        { "Nome Completo": {"abrev": "...", "dps": ["1ª DP", "3ª DP", ...]} }
    contendo apenas titulares vigentes hoje (entrada com `fim is None`).
    Membros inativos ou sem DP ativa são ignorados automaticamente.
    """
    if not DESIGNACOES_JSON.exists():
        log.warning(f"Arquivo não encontrado: {DESIGNACOES_JSON}. "
                    f"DEFENSORES_POLO ficará vazio.")
        return {}

    with open(DESIGNACOES_JSON, encoding="utf-8") as f:
        data = json.load(f)

    defensores = data.get("defensores", {})
    defensorias = data.get("defensorias", {})

    # Aplica overrides do Firestore (titulares_admin)
    try:
        db = get_firestore_client()
        for snap in db.collection(FIRESTORE_COLECAO_TITULARES).stream():
            dp_key = snap.id  # ex: "6"
            doc = snap.to_dict() or {}
            hist = doc.get("historico_titulares")
            if hist and dp_key in defensorias:
                defensorias[dp_key]["historico_titulares"] = hist
                log.info(f"Override de titulares aplicado para DP {dp_key} "
                         f"({len(hist)} entrada(s))")
    except Exception as e:
        log.warning(f"Falha ao ler overrides de titulares_admin: {e}. "
                    f"Continuando apenas com o JSON.")

    # Coleta titular vigente (fim is None) de cada DP
    resultado: dict = {}
    for dp_num, dp_info in defensorias.items():
        hist = dp_info.get("historico_titulares", []) or []
        vigente = next((h for h in hist if h.get("fim") is None), None)
        if not vigente:
            continue
        def_key = (vigente.get("defensor") or "").strip()
        if not def_key:
            continue

        info = defensores.get(def_key, {})
        nome = (info.get("nome") or def_key).strip()
        # Evita titular inativo mesmo que apareça como vigente por erro
        if info.get("ativo") is False:
            log.warning(f"DP {dp_num}: titular vigente {nome!r} está marcado "
                        f"ativo=false no JSON. Incluindo mesmo assim.")

        entrada = resultado.setdefault(nome, {"abrev": def_key, "dps": []})
        entrada["dps"].append(f"{dp_num}ª DP")

    # Ordena DPs por número dentro de cada defensor
    for info in resultado.values():
        info["dps"].sort(key=lambda s: int(re.match(r"\d+", s).group()))

    return resultado


def _construir_termos_gatilho(defensores: dict) -> list:
    """
    Gera regex (primeiro + segundo nome) para cada titular vigente.
    Ex.: "Miguel Eduardo Martins Tavares" → r"Miguel\\s+Eduardo"
    Usa re.escape para preservar acentos; o flag re.IGNORECASE é aplicado
    em `_extrair_trechos_relevantes`.
    """
    termos = []
    vistos = set()
    for nome in defensores.keys():
        partes = [p for p in nome.split() if len(p) > 2]  # descarta "de", "da"
        if len(partes) < 2:
            continue
        chave = (partes[0].lower(), partes[1].lower())
        if chave in vistos:
            continue
        vistos.add(chave)
        termos.append(re.escape(partes[0]) + r"\s+" + re.escape(partes[1]))
    return termos


def inicializar_defensores_e_termos():
    """
    Popula DEFENSORES_POLO e TERMOS_POLO_MEDIO dinamicamente. Deve ser chamada
    no início de `main()`, após o Firebase estar acessível.
    """
    global DEFENSORES_POLO, TERMOS_POLO_MEDIO

    DEFENSORES_POLO = _carregar_titulares_vigentes()
    if not DEFENSORES_POLO:
        log.warning("Nenhum titular vigente carregado. A análise do Claude "
                    "terá contexto vazio e pode não identificar afastamentos.")
    else:
        log.info(f"Titulares vigentes carregados ({len(DEFENSORES_POLO)}):")
        for nome, info in DEFENSORES_POLO.items():
            log.info(f"  • {nome} ({info['abrev']}) — {', '.join(info['dps'])}")

    termos_dinamicos = _construir_termos_gatilho(DEFENSORES_POLO)
    # Mantém a frase fixa como primeiro termo e anexa os dinâmicos
    TERMOS_POLO_MEDIO = [
        r"Polo\s+(?:do\s+)?M[eé]dio\s+Amazonas",
    ] + termos_dinamicos
    log.info(f"Termos-gatilho ativos ({len(TERMOS_POLO_MEDIO)}): "
             f"{TERMOS_POLO_MEDIO}")


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
- Se a designação for "a contar do dia X" SEM data final explícita, use `"data_fim": ""` — NÃO invente uma data
- Inclua o afastamento mesmo sem data fim; o sistema sinalizará para revisão manual

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

    # Carrega titulares vigentes + monta termos-gatilho dinamicamente
    try:
        inicializar_defensores_e_termos()
    except Exception as e:
        log.error(f"Falha ao inicializar defensores/termos: {e}", exc_info=True)
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
                    criados = salvar_afastamentos_firestore(
                        afastamentos,
                        edition["url"],
                        edition_num=edition["numero"],
                        data_publicacao_do=edition.get("data_publicacao", ""),
                    )
                    if criados:
                        custo_total = state.get("custo", {}).get("total_usd", 0.0)
                        notificar_afastamentos_gravados(criados, edition["url"], custo_total)
                        total_criados += len(criados)
                else:
                    log.info(f"Edição {num}: sem designações do Polo Médio Amazonas")

                # Detecção de concurso de remoção (independente dos afastamentos normais)
                if _texto_tem_remocao_polo_medio(text) and not verificar_limite_custo(state):
                    log.info(f"Edição {num}: texto contém Concurso de Remoção. Analisando…")
                    result_rem = parse_remocao(text, state)
                    if result_rem.get("tem_remocao"):
                        remocao_criada = salvar_remocao_firestore(
                            result_rem,
                            edition["url"],
                            edition_num=edition["numero"],
                            data_publicacao_do=edition.get("data_publicacao", ""),
                        )
                        if remocao_criada:
                            log.info(
                                f"🔄 Remoção gravada: {remocao_criada.get('portaria_numero')} "
                                f"| {len(remocao_criada.get('saindo', []))} saindo "
                                f"/ {len(remocao_criada.get('chegando', []))} chegando"
                            )
                    else:
                        log.info(f"Edição {num}: Polo Médio não afetado no concurso de remoção.")

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
