#!/usr/bin/env python3
"""
backfill-calendario-do-estruturado.py

Lê `docs/diario-oficial-completo-2026.json` (dados já estruturados) e extrai
via regex todas as designações de substituição do Polo Médio com período
fechado (início e fim), mesclando com afastamentos existentes no Firestore
(`afastamentos_admin`). Não chama a API Anthropic — 100% parser local.

Uso:
  py backfill-calendario-do-estruturado.py                 # dry-run (padrão)
  py backfill-calendario-do-estruturado.py --commit        # grava no Firestore
  py backfill-calendario-do-estruturado.py --no-firestore  # dry-run sem ler Firestore
"""

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import date, datetime

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_DIR      = Path(__file__).parent
DO_JSON          = PROJECT_DIR / "docs" / "diario-oficial-completo-2026.json"
DESIGNACOES_JSON = PROJECT_DIR / "docs" / "designacoes-2026.json"

FIREBASE_PROJECT_ID         = "polo-medio-as"
FIRESTORE_AFASTAMENTOS      = "afastamentos_admin"
FIRESTORE_TITULARES         = "titulares_admin"
CRIADO_POR                  = "backfill@diario-estruturado"
ORIGEM                      = "backfill-do-estruturado"

MES_MAP = {
    "janeiro":   1, "fevereiro": 2, "março":    3, "marco":    3,
    "abril":     4, "maio":      5, "junho":    6, "julho":    7,
    "agosto":    8, "setembro":  9, "outubro":  10,
    "novembro": 11, "dezembro":  12,
}

# ─── Parser de datas ─────────────────────────────────────────────────────────

_DIAS_MESES_RE = re.compile(
    r'\b(\d+(?:\s*(?:,|\s+a\s+|\s+e\s+)\s*\d+)*)\s+de\s+'
    r'(janeiro|fevereiro|mar[çc]o|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\b',
    re.IGNORECASE,
)

_SPLIT_DIAS_RE = re.compile(r'\s*(,|\s+a\s+|\s+e\s+)\s*', re.IGNORECASE)

_REJEITOS_RE = re.compile(
    r'\ba\s+(contar|partir)\s+(?:do\s+)?dia\b',
    re.IGNORECASE,
)


def _expand_day_sequence(seq: str) -> list[int]:
    """
    Recebe 'X a Y' / '07, 08 e 09' / '3, 4, 5, 6 e 8' / '22 a 25'
    e devolve a lista ordenada de dias cobertos.
    """
    parts = _SPLIT_DIAS_RE.split(seq.strip())
    parts = [p.strip() for p in parts if p is not None]

    result: list[int] = []
    i = 0
    while i < len(parts):
        token = parts[i]
        if not token:
            i += 1
            continue
        if token.isdigit():
            day = int(token)
            if i + 1 < len(parts) and parts[i + 1].strip().lower() == "a" \
                    and i + 2 < len(parts) and parts[i + 2].isdigit():
                end = int(parts[i + 2])
                if end >= day and end - day < 60:
                    result.extend(range(day, end + 1))
                    i += 3
                    continue
            result.append(day)
        i += 1

    # Dedup + ordena
    return sorted(set(result))


def _runs_consecutivos(dias: list[int]) -> list[tuple[int, int]]:
    if not dias:
        return []
    dias = sorted(set(dias))
    runs = []
    ini = fim = dias[0]
    for d in dias[1:]:
        if d == fim + 1:
            fim = d
        else:
            runs.append((ini, fim))
            ini = fim = d
    runs.append((ini, fim))
    return runs


# Regex para período que cruza meses: "12 de março de 2026 a 10 de abril de 2026"
_CROSS_PERIOD_RE = re.compile(
    r'(\d+)[ºo°]?\s+de\s+(janeiro|fevereiro|mar[çc]o|abril|maio|junho|julho|agosto|'
    r'setembro|outubro|novembro|dezembro)(?:\s+de\s+(\d{4}))?'
    r'\s+a\s+(\d+)[ºo°]?\s+de\s+(janeiro|fevereiro|mar[çc]o|abril|maio|junho|julho|agosto|'
    r'setembro|outubro|novembro|dezembro)(?:\s+de\s+(\d{4}))?',
    re.IGNORECASE,
)


def parse_date_ranges(trecho: str, ano_default: int = 2026) -> list[tuple[date, date]]:
    """
    Extrai todas as faixas (início, fim) do trecho, cobrindo:
      - "no período de X a Y de <mês> de 2026"
      - "nos dias A, B e C de <mês> de 2026"
      - "nos períodos de X a Y de <mês> e Z a W de <mês>"
      - "dias 3, 4, 5, 6 e 8 de março" (descontínuos → 2 runs)
      - "12 de março de 2026 a 10 de abril de 2026" (cross-month)

    Descarta trechos com "a contar do dia" ou "a partir do dia" (só início).
    """
    if _REJEITOS_RE.search(trecho):
        return []

    t = re.sub(r"\s+", " ", trecho)

    m_ano = re.search(r"de\s+(\d{4})\b", t)
    ano = int(m_ano.group(1)) if m_ano else ano_default

    ranges: list[tuple[date, date]] = []
    matched_spans: list[tuple[int, int]] = []

    # Passo 1: períodos cross-month ("X de MÊS_A a Y de MÊS_B")
    for m in _CROSS_PERIOD_RE.finditer(t):
        dia_ini  = int(m.group(1))
        mes_ini  = MES_MAP.get(m.group(2).lower().replace("ç", "c"))
        ano_ini  = int(m.group(3)) if m.group(3) else ano
        dia_fim  = int(m.group(4))
        mes_fim  = MES_MAP.get(m.group(5).lower().replace("ç", "c"))
        ano_fim  = int(m.group(6)) if m.group(6) else ano
        if not mes_ini or not mes_fim:
            continue
        try:
            d_ini = date(ano_ini, mes_ini, dia_ini)
            d_fim = date(ano_fim, mes_fim, dia_fim)
            if d_fim >= d_ini:
                ranges.append((d_ini, d_fim))
                matched_spans.append((m.start(), m.end()))
        except ValueError:
            continue

    # Passo 2: padrões dentro do mesmo mês, ignorando posições já cobertas
    for m in _DIAS_MESES_RE.finditer(t):
        if any(s <= m.start() < e for s, e in matched_spans):
            continue
        seq = m.group(1)
        mes_nome = m.group(2).lower().replace("ç", "c")
        mes = MES_MAP.get(mes_nome)
        if not mes:
            continue
        dias = _expand_day_sequence(seq)
        for ini, fim in _runs_consecutivos(dias):
            try:
                d_ini = date(ano, mes, ini)
                d_fim = date(ano, mes, fim)
                ranges.append((d_ini, d_fim))
            except ValueError:
                continue

    # Dedup exato
    uniq = []
    seen = set()
    for r in ranges:
        key = (r[0].isoformat(), r[1].isoformat())
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    return uniq


# ─── Parser de DESIGNAR / TORNAR SEM EFEITO ──────────────────────────────────

_RE_DESIGNAR = re.compile(r"\bDESIGNAR\b", re.IGNORECASE)
_RE_TORNAR   = re.compile(r"\bTORNAR\s+SEM\s+EFEITO\b", re.IGNORECASE)
_RE_CESSAR   = re.compile(r"\bCESSAR\s+OS\s+EFEITOS\b", re.IGNORECASE)
_RE_POLO     = re.compile(r"Defensoria\s+P[úu]blica\s+do\s+Polo", re.IGNORECASE)

_RE_NOME_SUB = re.compile(
    r"\b(?:de\s+)?(\d[ªa])\s+Classe\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^,;]+?)\s+para\s+atuar",
    re.IGNORECASE,
)
_RE_DP_AREA = re.compile(
    r"\bna\s+([\d\sªa,eE]+?)\s+Defensoria\s+P[úu]blica",
    re.IGNORECASE,
)
_RE_INCISO = re.compile(
    r"^\s*(I{1,3}|IV|IX|VI{0,3}|V|X{1,2}(?:I{0,3}|IV|VI{0,3})?)\s*[-–—]\s",
    re.IGNORECASE,
)
_RE_PORTARIA_CITADA = re.compile(
    r"PORTARIA\s+(?:n[ºo°\.]*\s*)?(\d+)\s*/\s*(\d{4})",
    re.IGNORECASE,
)


def _limpa_nome(nome: str) -> str:
    return re.sub(r"\s+", " ", nome.strip())


# Mapa de algarismos romanos -> inteiro (cobre I..XX, suficiente para incisos).
_ROMAN_MAP = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
    "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
    "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
    "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19, "XX": 20,
}


def _extrair_inciso(trecho: str) -> str:
    """Retorna o romano do inciso (ex: 'I', 'VII') ou '' se não achar."""
    m = _RE_INCISO.match(trecho)
    if not m:
        return ""
    return m.group(1).upper()


def _portaria_chave(numero: str) -> tuple[int, int] | None:
    """Extrai (num, ano) de uma string 'Portaria Nº 41/2026-GSPG/DPE/AM'."""
    if not numero:
        return None
    m = re.search(r"(\d+)\s*/\s*(\d{4})", numero)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)))


def parse_trecho_designar(trecho: str) -> dict | None:
    """Se for uma DESIGNAR do Polo Médio com período fechado, retorna dict:
       { substituto_nome, dps: [..], ranges: [(ini, fim)] }. Senão None.
    """
    if not _RE_DESIGNAR.search(trecho):
        return None
    if _RE_TORNAR.search(trecho):
        return None
    if not _RE_POLO.search(trecho):
        return None

    # Exclui designações "em caráter especial" para Tribunal do Júri etc.
    if re.search(r"DESIGNAR[^,.;]*,?\s*em\s+car[áa]ter\s+especial", trecho, re.IGNORECASE):
        return None
    if re.search(r"Tribunal\s+do\s+J[úu]ri", trecho, re.IGNORECASE):
        return None

    m_nome = _RE_NOME_SUB.search(trecho)
    if not m_nome:
        return None
    sub_nome = _limpa_nome(m_nome.group(2))

    m_dp = _RE_DP_AREA.search(trecho)
    if not m_dp:
        return None
    dp_nums = re.findall(r"\d+", m_dp.group(1))
    if not dp_nums:
        return None

    ranges = parse_date_ranges(trecho)
    if not ranges:
        return None

    return {
        "substituto_nome": sub_nome,
        "dps":             dp_nums,
        "ranges":          ranges,
        "inciso":          _extrair_inciso(trecho),
    }


def parse_trecho_revogacao(trecho: str) -> dict | None:
    """Detecta TORNAR SEM EFEITO ou CESSAR OS EFEITOS e extrai o que foi revogado.

    Retorna dict com `alvos` = lista de dicts {portaria: (num, ano), incisos: set|None}.
    `incisos == None` significa "toda a portaria".
    """
    if not (_RE_TORNAR.search(trecho) or _RE_CESSAR.search(trecho)):
        return None

    portarias_citadas = list(_RE_PORTARIA_CITADA.finditer(trecho))
    alvos = []
    for m in portarias_citadas:
        num, ano = int(m.group(1)), int(m.group(2))
        # Tenta achar "inciso X [e Y] da PORTARIA ..." logo antes do match.
        ctx_ini = max(0, m.start() - 150)
        ctx = trecho[ctx_ini:m.start()]
        m_inc = re.search(
            r"\binciso[s]?\s+((?:[IVX]+(?:\s*(?:,|\s+e\s+)\s*[IVX]+)*))\s+da\s*$",
            ctx, re.IGNORECASE,
        )
        incisos: set | None = None
        if m_inc:
            raw = m_inc.group(1)
            pieces = re.split(r"\s*(?:,|\s+e\s+)\s*", raw, flags=re.IGNORECASE)
            incisos = {p.strip().upper() for p in pieces if p.strip()}
        alvos.append({
            "portaria": (num, ano),
            "incisos":  incisos,
        })

    return {
        "tipo":   "revogacao",
        "trecho": trecho,
        "alvos":  alvos,
    }


# ─── Carga do JSON de designações ────────────────────────────────────────────

def carregar_designacoes_json() -> dict:
    with open(DESIGNACOES_JSON, encoding="utf-8") as f:
        return json.load(f)


def aplicar_overrides_titulares(defensorias: dict, db) -> None:
    """Aplica overrides de `titulares_admin` do Firestore (mesmo do Projeto 1)."""
    try:
        for snap in db.collection(FIRESTORE_TITULARES).stream():
            dp_key = snap.id
            doc = snap.to_dict() or {}
            hist = doc.get("historico_titulares")
            if hist and dp_key in defensorias:
                defensorias[dp_key]["historico_titulares"] = hist
    except Exception as e:
        print(f"⚠️  Falha ao ler overrides de titulares: {e}", file=sys.stderr)


def titular_em_data(dp_num: str, d: date, defensorias: dict) -> str | None:
    """Retorna abrev do titular vigente na data (right-exclusive)."""
    dp = defensorias.get(str(dp_num))
    if not dp:
        return None
    for h in dp.get("historico_titulares", []) or []:
        try:
            ini = datetime.strptime(h["inicio"], "%Y-%m-%d").date()
        except Exception:
            continue
        fim_s = h.get("fim")
        fim = datetime.strptime(fim_s, "%Y-%m-%d").date() if fim_s else None
        if ini <= d and (fim is None or d < fim):
            return h.get("defensor")
    return None


def nome_para_abrev(nome: str, defensores: dict) -> str | None:
    """Mapeia nome completo → abrev via match forte/fraco."""
    if not nome:
        return None
    alvo = nome.strip().lower()
    for abrev, info in defensores.items():
        if info.get("nome", "").strip().lower() == alvo:
            return abrev
    partes_alvo = alvo.split()
    if len(partes_alvo) >= 2:
        for abrev, info in defensores.items():
            partes = info.get("nome", "").lower().split()
            if len(partes) >= 2 and partes[0] == partes_alvo[0] \
                    and partes[-1] == partes_alvo[-1]:
                return abrev
        for abrev, info in defensores.items():
            partes = info.get("nome", "").lower().split()
            if len(partes) >= 2 and partes[0] == partes_alvo[0] \
                    and partes[1] == partes_alvo[1]:
                return abrev
    return None


# ─── Firestore client (opcional) ─────────────────────────────────────────────

def get_firestore_client():
    import firebase_admin
    from firebase_admin import credentials, firestore
    import os

    if not firebase_admin._apps:
        cred = None
        sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "").strip()
        if sa_json:
            cred = credentials.Certificate(json.loads(sa_json))
        else:
            sa_path = PROJECT_DIR / "firebase-service-account.json"
            if sa_path.exists():
                cred = credentials.Certificate(str(sa_path))
        if cred is None:
            raise RuntimeError(
                "Credencial do Firebase não encontrada. Coloque "
                "firebase-service-account.json na raiz do projeto."
            )
        firebase_admin.initialize_app(cred, {"projectId": FIREBASE_PROJECT_ID})
    return firestore.client()


def buscar_afastamentos_do_defensor(db, defensor_abrev: str) -> list[tuple[str, dict]]:
    col = db.collection(FIRESTORE_AFASTAMENTOS)
    snaps = col.where("defensor", "==", defensor_abrev).stream()
    return [(s.id, s.to_dict() or {}) for s in snaps]


def overlap(a_ini: date, a_fim: date, b_ini: date, b_fim: date) -> bool:
    return a_ini <= b_fim and b_ini <= a_fim


def _parse_iso(s: str) -> date | None:
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def _json_evento_cobre_sub(eventos_json: list, defensor: str, dp: str,
                            d_ini: date, d_fim: date,
                            sub_abrev: str | None) -> bool:
    """
    True se algum evento JSON para este defensor/período já registra o par
    (dp, sub_abrev) com substituto não-nulo — significa duplicata, não criar.
    """
    if not sub_abrev or sub_abrev == "_outro":
        return False
    for ev in eventos_json:
        if ev.get("defensor") != defensor:
            continue
        ei = _parse_iso(ev.get("data_inicio", ""))
        ef = _parse_iso(ev.get("data_fim", ""))
        if not ei or not ef or not overlap(ei, ef, d_ini, d_fim):
            continue
        for d in ev.get("designacoes", []):
            if str(d.get("dp")) == str(dp) and d.get("substituto") == sub_abrev:
                return True
    return False


# ─── Planejamento de ações ───────────────────────────────────────────────────

def planejar_acoes(dados_do: list, defensores: dict, defensorias: dict,
                   afastamentos_por_defensor: dict | None,
                   eventos_json: list | None = None) -> dict:
    """
    Faz o parsing e planeja ações. Retorna:
      {
        "acoes": [ {tipo: merge|novo, ...} ],
        "revogacoes": [...],
        "nao_parseadas": [...],
      }
    Se afastamentos_por_defensor for None (modo --no-firestore), pula merge.
    """
    plano = {"acoes": [], "revogacoes": [], "nao_parseadas": []}
    abrevs_validos = set(defensores.keys())

    for ed in dados_do:
        edicao_num = ed.get("edicao")
        edicao_data = ed.get("data_formatada") or ed.get("data")
        edicao_url = ed.get("url", "")

        ports = ed.get("portarias_estruturadas") or []
        if isinstance(ports, dict):
            ports = [ports]
        for port in ports:
            if not isinstance(port, dict):
                continue
            cats = port.get("categorias") or []
            if not any(c in cats for c in ("designacoes", "substituicao", "polo_medio", "defensor")):
                continue
            portaria_numero = (port.get("numero") or "").strip()
            processo_sei    = (port.get("sei") or "").strip()

            for trecho in port.get("trechos") or []:
                rev = parse_trecho_revogacao(trecho)
                if rev:
                    plano["revogacoes"].append({
                        "edicao":          edicao_num,
                        "edicao_data":     edicao_data,
                        "portaria":        portaria_numero,
                        "trecho":          trecho.strip(),
                        "alvos":           rev.get("alvos") or [],
                    })
                    continue

                parsed = parse_trecho_designar(trecho)
                if not parsed:
                    if _RE_DESIGNAR.search(trecho) and _RE_POLO.search(trecho):
                        plano["nao_parseadas"].append({
                            "edicao":      edicao_num,
                            "edicao_data": edicao_data,
                            "portaria":    portaria_numero,
                            "trecho":      trecho.strip(),
                        })
                    continue

                sub_nome_completo = parsed["substituto_nome"]
                sub_abrev = nome_para_abrev(sub_nome_completo, defensores)
                inciso_orig = parsed.get("inciso", "")
                portaria_chave = _portaria_chave(portaria_numero)

                for dp in parsed["dps"]:
                    for d_ini, d_fim in parsed["ranges"]:
                        titular_abrev = titular_em_data(dp, d_ini, defensorias)
                        titular_nome  = ""
                        if titular_abrev and titular_abrev in defensores:
                            titular_nome = defensores[titular_abrev].get("nome_curto") \
                                or defensores[titular_abrev].get("nome") \
                                or titular_abrev

                        # Monta o item base
                        item = {
                            "edicao":           edicao_num,
                            "edicao_data":      edicao_data,
                            "edicao_url":       edicao_url,
                            "portaria_numero":  portaria_numero,
                            "portaria_chave":   portaria_chave,
                            "inciso":           inciso_orig,
                            "processo_sei":     processo_sei,
                            "dp":               dp,
                            "data_inicio":      d_ini.isoformat(),
                            "data_fim":         d_fim.isoformat(),
                            "substituto_nome":  sub_nome_completo,
                            "substituto_abrev": sub_abrev if sub_abrev in abrevs_validos else None,
                            "titular_abrev":    titular_abrev,
                            "titular_nome":     titular_nome,
                            "trecho":           trecho.strip(),
                        }

                        if not titular_abrev:
                            item["tipo"]  = "sem-titular"
                            item["motivo"] = f"Titular não resolvido para DP {dp} em {d_ini.isoformat()}"
                            plano["acoes"].append(item)
                            continue

                        # Se o "substituto" for o próprio titular da DP (auto-designação
                        # ou caso de titular assumindo a DP pela primeira vez), pula.
                        if item["substituto_abrev"] == titular_abrev:
                            item["tipo"]   = "self-assign"
                            item["motivo"] = "Substituto = titular (designação inicial, não é afastamento)"
                            plano["acoes"].append(item)
                            continue

                        # Se o par (dp, substituto) já está em um evento JSON,
                        # não cria registro duplicado no Firestore.
                        if eventos_json and _json_evento_cobre_sub(
                            eventos_json, titular_abrev, dp, d_ini, d_fim,
                            item.get("substituto_abrev")
                        ):
                            item["tipo"]   = "skip-json"
                            item["motivo"] = "Substituto já registrado no evento JSON"
                            plano["acoes"].append(item)
                            continue

                        if afastamentos_por_defensor is None:
                            item["tipo"] = "novo-pendente-firestore"
                            plano["acoes"].append(item)
                            continue

                        # Tenta merge em afastamento existente
                        encontrados = []
                        for fid, doc in afastamentos_por_defensor.get(titular_abrev, []):
                            fi = _parse_iso(doc.get("data_inicio", ""))
                            ff = _parse_iso(doc.get("data_fim", ""))
                            if fi and ff and overlap(fi, ff, d_ini, d_fim):
                                encontrados.append((fid, doc, fi, ff))

                        if encontrados:
                            item["tipo"]                = "merge"
                            item["afastamento_id"]      = encontrados[0][0]
                            item["afastamento_tipo"]    = encontrados[0][1].get("tipo", "")
                            item["afastamento_periodo"] = f"{encontrados[0][2].isoformat()}→{encontrados[0][3].isoformat()}"
                        else:
                            item["tipo"]             = "novo"
                            item["afastamento_tipo"] = "outro"
                        plano["acoes"].append(item)

    return plano


# ─── Dedup dentro do próprio plano ───────────────────────────────────────────

ANO_MINIMO = 2026


def filtrar_ano_minimo(plano: dict, ano: int = ANO_MINIMO) -> dict:
    """Remove ações cuja `data_inicio` é anterior a 01/jan do ano mínimo."""
    limite = f"{ano}-01-01"
    removidos = []
    novo = []
    for a in plano["acoes"]:
        if a.get("data_inicio", "") < limite:
            removidos.append(a)
        else:
            novo.append(a)
    plano["acoes"] = novo
    plano["filtrados_por_ano"] = removidos
    return plano


def aplicar_revogacoes(plano: dict) -> dict:
    """Remove ações cuja (portaria, inciso) foi revogada por TORNAR SEM EFEITO/
    CESSAR OS EFEITOS. Guarda lista dos removidos em plano['removidos_por_revogacao']."""
    # Constrói índice: {(num, ano): set|None}  (None = toda a portaria revogada)
    revogadas_total: set = set()                # (num, ano) -> toda
    revogadas_inc:   dict[tuple, set] = {}      # (num, ano) -> {incisos}
    for rev in plano["revogacoes"]:
        for alvo in rev.get("alvos") or []:
            chave = alvo["portaria"]
            incisos = alvo.get("incisos")
            if incisos is None:
                revogadas_total.add(chave)
                revogadas_inc.pop(chave, None)
            else:
                if chave in revogadas_total:
                    continue
                revogadas_inc.setdefault(chave, set()).update(incisos)

    removidos = []
    novo = []
    for a in plano["acoes"]:
        ch = a.get("portaria_chave")
        if ch is None:
            novo.append(a)
            continue
        if ch in revogadas_total:
            a["motivo_remocao"] = f"Portaria inteira revogada"
            removidos.append(a)
            continue
        incisos_rev = revogadas_inc.get(ch, set())
        if incisos_rev and a.get("inciso", "") in incisos_rev:
            a["motivo_remocao"] = f"Inciso {a['inciso']} revogado"
            removidos.append(a)
            continue
        novo.append(a)
    plano["acoes"] = novo
    plano["removidos_por_revogacao"] = removidos
    return plano


def dedup_plano(plano: dict) -> dict:
    """Agrupa itens idênticos (mesmo titular+dp+período+substituto) — pega o
    primeiro que aparece (menor edição). Elimina processamento duplicado de
    uma mesma designação citada em múltiplas edições (ex.: TORNAR SEM EFEITO
    antes + portaria original depois)."""
    visto = {}
    uniq = []
    for item in plano["acoes"]:
        key = (
            item.get("titular_abrev"),
            item.get("dp"),
            item.get("data_inicio"),
            item.get("data_fim"),
            (item.get("substituto_abrev") or item.get("substituto_nome") or "").lower(),
        )
        if key in visto:
            continue
        visto[key] = True
        uniq.append(item)
    plano["acoes"] = uniq
    return plano


# ─── Relatório ───────────────────────────────────────────────────────────────

def _c(s, cor):
    return f"\033[{cor}m{s}\033[0m"


def imprimir_relatorio(plano: dict, commit: bool, usou_firestore: bool) -> None:
    print()
    print("=" * 88)
    print(f"  BACKFILL CALENDÁRIO — {'COMMIT' if commit else 'DRY-RUN'} "
          f"({'com' if usou_firestore else 'sem'} Firestore)")
    print("=" * 88)

    contagem = {"merge": 0, "novo": 0, "sem-titular": 0, "self-assign": 0,
                "novo-pendente-firestore": 0, "skip-json": 0}
    for a in plano["acoes"]:
        contagem[a["tipo"]] = contagem.get(a["tipo"], 0) + 1

    print(f"\nResumo:")
    print(f"  • MERGE em afastamento existente ... {contagem['merge']:>3}")
    print(f"  • NOVO afastamento (tipo=outro) .... {contagem['novo']:>3}")
    print(f"  • Pendente (sem Firestore) ......... {contagem['novo-pendente-firestore']:>3}")
    print(f"  • Sem titular resolvido ............ {contagem['sem-titular']:>3}")
    print(f"  • Auto-designação (pulado) ......... {contagem['self-assign']:>3}")
    print(f"  • Revogações (TORNAR/CESSAR) ....... {len(plano['revogacoes']):>3}")
    print(f"  • Removidos por ano < {ANO_MINIMO} ........ {len(plano.get('filtrados_por_ano', [])):>3}")
    print(f"  • Removidos por revogação .......... {len(plano.get('removidos_por_revogacao', [])):>3}")
    print(f"  • Já no JSON (ignorado) ............. {contagem['skip-json']:>3}")
    print(f"  • Trechos não parseados ............ {len(plano['nao_parseadas']):>3}")

    def _linha_acao(a):
        sub = a.get("substituto_abrev") or f'"_outro" ({a.get("substituto_nome")})'
        tit = a.get("titular_nome") or "?"
        return (f"  Ed.{a['edicao']:<5} {a['portaria_numero']:<35}  "
                f"{sub} → {a['dp']}ª DP  {a['data_inicio']}..{a['data_fim']}  "
                f"(titular: {tit})")

    for categoria, titulo in [
        ("novo",         "➕ NOVOS AFASTAMENTOS (serão criados com tipo=outro)"),
        ("merge",        "🔀 MERGE em afastamentos existentes"),
        ("novo-pendente-firestore", "⏳ PENDENTES (Firestore não consultado)"),
        ("sem-titular",  "⚠️  SEM TITULAR RESOLVIDO — revisar manualmente"),
        ("self-assign",  "↺ AUTO-DESIGNAÇÃO — ignorado"),
        ("skip-json",    "✅ JÁ NO JSON — ignorado (substituto já registrado no evento JSON)"),
    ]:
        items = [a for a in plano["acoes"] if a["tipo"] == categoria]
        if not items:
            continue
        print(f"\n{titulo}  ({len(items)})")
        print("-" * 88)
        for a in items:
            print(_linha_acao(a))
            if categoria == "merge":
                print(f"     ↳ afastamento existente: id={a['afastamento_id']}  "
                      f"tipo={a['afastamento_tipo']}  período={a['afastamento_periodo']}")
            if categoria == "sem-titular":
                print(f"     ↳ {a.get('motivo', '')}")

    if plano["revogacoes"]:
        print(f"\n🚫 REVOGAÇÕES (TORNAR SEM EFEITO / CESSAR OS EFEITOS) — ({len(plano['revogacoes'])})")
        print("   Não gravadas. Revise manualmente se alguma designação já no Firestore foi revogada.")
        print("-" * 88)
        for r in plano["revogacoes"]:
            print(f"  Ed.{r['edicao']} ({r['edicao_data']}) — {r['portaria']}")
            t = r['trecho'][:180].replace('\n', ' ')
            print(f"     {t}{'…' if len(r['trecho']) > 180 else ''}")

    if plano.get("removidos_por_revogacao"):
        print(f"\n🗑️  REMOVIDOS POR REVOGAÇÃO — ({len(plano['removidos_por_revogacao'])})")
        print("-" * 88)
        for a in plano["removidos_por_revogacao"]:
            print(f"  Ed.{a['edicao']} {a['portaria_numero']:<35}  "
                  f"{a.get('substituto_abrev') or a.get('substituto_nome')} → {a['dp']}ª DP  "
                  f"{a['data_inicio']}..{a['data_fim']}   [{a.get('motivo_remocao', '')}]")

    if plano.get("filtrados_por_ano"):
        print(f"\n📆 REMOVIDOS POR ANO < {ANO_MINIMO} — ({len(plano['filtrados_por_ano'])})")
        print("-" * 88)
        for a in plano["filtrados_por_ano"]:
            print(f"  Ed.{a['edicao']} {a['portaria_numero']:<35}  "
                  f"{a.get('substituto_abrev') or a.get('substituto_nome')} → {a['dp']}ª DP  "
                  f"{a['data_inicio']}..{a['data_fim']}")

    if plano["nao_parseadas"]:
        print(f"\n❌ TRECHOS NÃO PARSEADOS (provável falta de data fim) — ({len(plano['nao_parseadas'])})")
        print("-" * 88)
        for n in plano["nao_parseadas"]:
            print(f"  Ed.{n['edicao']} ({n['edicao_data']}) — {n['portaria']}")
            t = n['trecho'][:200].replace('\n', ' ')
            print(f"     {t}{'…' if len(n['trecho']) > 200 else ''}")

    print()
    print("=" * 88)


# ─── Gravação no Firestore ───────────────────────────────────────────────────

def gravar_firestore(plano: dict, db) -> None:
    from firebase_admin import firestore

    col = db.collection(FIRESTORE_AFASTAMENTOS)
    criados = 0
    merged  = 0

    for item in plano["acoes"]:
        if item["tipo"] != "merge":
            continue

        sub_abrev = item.get("substituto_abrev") or "_outro"
        sub_externo = "" if sub_abrev != "_outro" else item.get("substituto_nome", "")
        novo_sub = {
            "substituto":              sub_abrev,
            "substituto_nome_externo": sub_externo,
            "data_inicio":             item["data_inicio"],
            "data_fim":                item["data_fim"],
            "portaria_numero":         item["portaria_numero"],
            "portaria_url":            item["edicao_url"],
        }

        if item["tipo"] == "merge":
            doc_ref = col.document(item["afastamento_id"])
            snap = doc_ref.get()
            if not snap.exists:
                print(f"  ⚠️  afastamento {item['afastamento_id']} não existe mais; pulado.")
                continue
            doc = snap.to_dict() or {}
            ddp = list(doc.get("designacoes_dp") or [])

            # Localiza ou cria a DP
            dp_entry = next((e for e in ddp if str(e.get("dp", "")) == item["dp"]), None)
            if dp_entry is None:
                dp_entry = {"dp": item["dp"], "substitutos": []}
                ddp.append(dp_entry)
            # Dedup de substituto dentro da DP
            dup = any(
                s.get("substituto") == novo_sub["substituto"]
                and s.get("data_inicio") == novo_sub["data_inicio"]
                and s.get("data_fim") == novo_sub["data_fim"]
                for s in (dp_entry.get("substitutos") or [])
            )
            if dup:
                print(f"  ⚠️  substituto já registrado em {item['afastamento_id']}: "
                      f"{sub_abrev} {item['data_inicio']}→{item['data_fim']}. pulando.")
                continue
            dp_entry.setdefault("substitutos", []).append(novo_sub)

            doc_ref.update({
                "designacoes_dp": ddp,
                "atualizado_por": CRIADO_POR,
                "atualizado_em":  firestore.SERVER_TIMESTAMP,
            })
            merged += 1
            print(f"  🔀 MERGED  {item['afastamento_id']}: {sub_abrev} → {item['dp']}ª DP "
                  f"{item['data_inicio']}..{item['data_fim']}")

    # Novos: agrupa por (titular, data_inicio, data_fim, portaria_numero)
    # para criar UM doc com todas as DPs do mesmo afastamento.
    grupos_novos: dict[tuple, list] = {}
    for item in plano["acoes"]:
        if item["tipo"] != "novo":
            continue
        key = (
            item["titular_abrev"],
            item["data_inicio"],
            item["data_fim"],
            item.get("portaria_numero", ""),
        )
        grupos_novos.setdefault(key, []).append(item)

    for (titular, di, df, portaria), items in grupos_novos.items():
        item0 = items[0]

        # Monta designacoes_dp agrupando por DP (dedup interno já feito por dedup_plano)
        dp_map: dict[str, dict] = {}
        for it in items:
            dp = it["dp"]
            if dp not in dp_map:
                dp_map[dp] = {"dp": dp, "substitutos": []}
            s_abrev = it.get("substituto_abrev") or "_outro"
            s_ext   = "" if s_abrev != "_outro" else it.get("substituto_nome", "")
            dp_map[dp]["substitutos"].append({
                "substituto":              s_abrev,
                "substituto_nome_externo": s_ext,
                "data_inicio":             it["data_inicio"],
                "data_fim":                it["data_fim"],
                "portaria_numero":         it["portaria_numero"],
                "portaria_url":            it["edicao_url"],
            })

        doc = {
            "defensor":        titular,
            "tipo":            "outro",
            "tipo_custom":     "",
            "data_inicio":     di,
            "data_fim":        df,
            "processo_tipo":   "SEI" if item0["processo_sei"] else "",
            "processo_sei":    item0["processo_sei"],
            "portaria_numero": portaria,
            "portaria_url":    item0["edicao_url"],
            "portaria_sei":    item0["processo_sei"],
            "designacoes_dp":  list(dp_map.values()),
            "criado_por":      CRIADO_POR,
            "criado_em":       firestore.SERVER_TIMESTAMP,
            "atualizado_por":  CRIADO_POR,
            "atualizado_em":   firestore.SERVER_TIMESTAMP,
            "origem":          ORIGEM,
        }
        _, ref = col.add(doc)
        criados += 1
        dps_str = ", ".join(f"{dp}ª" for dp in dp_map)
        print(f"  ➕ CRIADO  {ref.id}: {titular} outro {di}..{df}  "
              f"[DP(s): {dps_str}]")

    print(f"\n  Total: {criados} criado(s), {merged} merge(s).")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit",        action="store_true",
                    help="Grava de fato no Firestore (padrão é dry-run)")
    ap.add_argument("--no-firestore",  action="store_true",
                    help="Não consulta Firestore (dry-run local apenas)")
    args = ap.parse_args()

    if not DO_JSON.exists():
        print(f"❌ Arquivo não encontrado: {DO_JSON}", file=sys.stderr)
        sys.exit(1)
    if not DESIGNACOES_JSON.exists():
        print(f"❌ Arquivo não encontrado: {DESIGNACOES_JSON}", file=sys.stderr)
        sys.exit(1)

    with open(DO_JSON, encoding="utf-8") as f:
        dados_do = json.load(f)
    design = carregar_designacoes_json()
    defensores   = design.get("defensores", {}) or {}
    defensorias  = design.get("defensorias", {}) or {}
    eventos_json = design.get("eventos") or []
    print(f"📋 {len(eventos_json)} evento(s) JSON carregados (base para dedup).")

    afastamentos_por_defensor: dict | None = None
    db = None
    if not args.no_firestore:
        try:
            db = get_firestore_client()
            aplicar_overrides_titulares(defensorias, db)
            afastamentos_por_defensor = {}
            for abrev in defensores.keys():
                afastamentos_por_defensor[abrev] = buscar_afastamentos_do_defensor(db, abrev)
            total = sum(len(v) for v in afastamentos_por_defensor.values())
            print(f"🔥 Firestore conectado. {total} afastamento(s) existente(s) carregado(s).")
        except Exception as e:
            print(f"⚠️  Firestore indisponível ({e}). Rodando sem merge.", file=sys.stderr)
            afastamentos_por_defensor = None
            db = None

    plano = planejar_acoes(dados_do, defensores, defensorias,
                           afastamentos_por_defensor, eventos_json)
    plano = filtrar_ano_minimo(plano, ANO_MINIMO)
    plano = aplicar_revogacoes(plano)
    plano = dedup_plano(plano)
    imprimir_relatorio(plano, commit=args.commit, usou_firestore=db is not None)

    if args.commit:
        if db is None:
            print("❌ --commit exige Firestore acessível. Abortando.", file=sys.stderr)
            sys.exit(2)
        print("\n💾 Gravando no Firestore...\n")
        gravar_firestore(plano, db)


if __name__ == "__main__":
    main()
