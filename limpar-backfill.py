#!/usr/bin/env python3
"""
limpar-backfill.py

Limpa registros incorretos criados por backfill-calendario-do-estruturado.py:

  1. Duplicatas do JSON — docs de backfill cujos pares (dp, substituto) já
     existem em eventos do designacoes-2026.json com substituto não-nulo.
     Ação: DELETAR o doc do Firestore.

  2. Docs fragmentados — múltiplos docs para o mesmo (defensor, data_inicio,
     data_fim) criados um por DP em vez de um doc com todas as DPs.
     Ação: CONSOLIDAR em um único doc, DELETAR os extras.

  3. Docs com mistura — parte dos substitutos são duplicatas do JSON, parte
     são dados novos.
     Ação: ATUALIZAR o doc removendo só as entradas duplicadas.

Uso:
  py limpar-backfill.py              # dry-run (padrão — não toca no Firestore)
  py limpar-backfill.py --commit     # executa as ações no Firestore
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_DIR      = Path(__file__).parent
DESIGNACOES_JSON = PROJECT_DIR / "docs" / "designacoes-2026.json"

FIREBASE_PROJECT_ID    = "polo-medio-as"
FIRESTORE_AFASTAMENTOS = "afastamentos_admin"
ORIGEM_BACKFILL        = "backfill-do-estruturado"


# ─── Utilitários ─────────────────────────────────────────────────────────────

def _parse_iso(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def _overlap(a_ini, a_fim, b_ini, b_fim) -> bool:
    return a_ini <= b_fim and b_ini <= a_fim


# ─── Firebase ────────────────────────────────────────────────────────────────

def get_firestore_client():
    import firebase_admin
    from firebase_admin import credentials, firestore
    import os

    if not firebase_admin._apps:
        sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "").strip()
        if sa_json:
            cred = credentials.Certificate(json.loads(sa_json))
        else:
            sa_path = PROJECT_DIR / "firebase-service-account.json"
            if not sa_path.exists():
                raise RuntimeError(
                    "Credencial não encontrada. Coloque "
                    "firebase-service-account.json na raiz do projeto."
                )
            cred = credentials.Certificate(str(sa_path))
        firebase_admin.initialize_app(cred, {"projectId": FIREBASE_PROJECT_ID})
    return firestore.client()


def buscar_backfill_docs(db) -> list[tuple[str, dict]]:
    snaps = db.collection(FIRESTORE_AFASTAMENTOS) \
               .where("origem", "==", ORIGEM_BACKFILL) \
               .stream()
    return [(s.id, s.to_dict() or {}) for s in snaps]


# ─── Dados JSON ──────────────────────────────────────────────────────────────

def carregar_eventos_json() -> list[dict]:
    with open(DESIGNACOES_JSON, encoding="utf-8") as f:
        return json.load(f).get("eventos", [])


def _eventos_json_para_defensor(defensor: str, d_ini, d_fim,
                                eventos: list[dict]) -> list[dict]:
    """Eventos JSON do mesmo defensor com período sobreposto."""
    result = []
    for ev in eventos:
        if ev.get("defensor") != defensor:
            continue
        ei = _parse_iso(ev.get("data_inicio", ""))
        ef = _parse_iso(ev.get("data_fim", ""))
        if ei and ef and _overlap(ei, ef, d_ini, d_fim):
            result.append(ev)
    return result


def _json_ja_tem_sub(evento: dict, dp: str, sub_abrev: str) -> bool:
    """
    True se o evento JSON já registra o par (dp, sub_abrev) com substituto
    não-nulo e não-externo.
    """
    if not sub_abrev or sub_abrev == "_outro":
        return False
    for d in evento.get("designacoes", []):
        if str(d.get("dp")) == str(dp) and d.get("substituto") == sub_abrev:
            return True
    return False


# ─── Análise ─────────────────────────────────────────────────────────────────

def analisar(backfill_docs: list[tuple[str, dict]],
             eventos_json: list[dict]) -> dict:
    """
    Classifica cada doc de backfill e devolve plano de ações:
      {
        "deletar":     [(fid, doc, motivo), ...],
        "consolidar":  [op_dict, ...],
        "ok":          [(fid, doc, motivo), ...],
      }
    """
    # Agrupa por (defensor, data_inicio, data_fim)
    grupos: dict[tuple, list] = {}
    for fid, doc in backfill_docs:
        key = (doc.get("defensor"), doc.get("data_inicio"), doc.get("data_fim"))
        grupos.setdefault(key, []).append((fid, doc))

    plano: dict[str, list] = {"deletar": [], "consolidar": [], "ok": []}

    for (defensor, di_str, df_str), docs_grupo in grupos.items():
        d_ini = _parse_iso(di_str or "")
        d_fim = _parse_iso(df_str or "")
        if not d_ini or not d_fim:
            for fid, doc in docs_grupo:
                plano["ok"].append((fid, doc, "datas inválidas — revisar manualmente"))
            continue

        eventos_match = _eventos_json_para_defensor(defensor, d_ini, d_fim, eventos_json)

        # Classifica cada substituto de cada doc como duplicata ou dado novo
        docs_analisados = []  # (fid, doc, validas, duplicatas)
        for fid, doc in docs_grupo:
            validas = []
            duplicatas = []
            for dp_entry in doc.get("designacoes_dp") or []:
                dp = str(dp_entry.get("dp", ""))
                subs_validos, subs_dup = [], []
                for sub in dp_entry.get("substitutos") or []:
                    sub_abrev = sub.get("substituto", "")
                    is_dup = any(
                        _json_ja_tem_sub(ev, dp, sub_abrev)
                        for ev in eventos_match
                    )
                    (subs_dup if is_dup else subs_validos).append(sub)
                if subs_validos:
                    validas.append({**dp_entry, "substitutos": subs_validos})
                if subs_dup:
                    duplicatas.append({**dp_entry, "substitutos": subs_dup})
            docs_analisados.append((fid, doc, validas, duplicatas))

        # Reúne todos os dp_entries válidos do grupo
        todos_validos = []
        for fid, doc, validas, _ in docs_analisados:
            todos_validos.extend(validas)

        if not todos_validos:
            # Todos os dados já existem no JSON → deletar o grupo inteiro
            for fid, doc, _, _ in docs_analisados:
                motivo = (
                    f"duplicata de evento JSON "
                    f"({defensor} {di_str}→{df_str})"
                )
                plano["deletar"].append((fid, doc, motivo))

        elif len(docs_grupo) == 1:
            # Doc único com algum dado novo
            fid, doc, validas, duplicatas = docs_analisados[0]
            if duplicatas:
                # Mistura de duplicatas e dados novos → atualizar removendo dups
                n_dup = sum(len(e["substitutos"]) for e in duplicatas)
                plano["consolidar"].append({
                    "tipo":               "atualizar",
                    "fid":                fid,
                    "doc_original":       doc,
                    "designacoes_dp_nova": validas,
                    "motivo":             f"removendo {n_dup} substituto(s) duplicado(s) do JSON",
                })
            else:
                # Tudo novo, doc único — sem ação necessária
                plano["ok"].append((fid, doc, "dados novos, doc único — sem ação"))

        else:
            # Múltiplos docs no grupo → consolidar em 1
            # Mescla dp_entries válidos por DP (dedup interno por dp+sub+periodo)
            dp_map: dict[str, dict] = {}
            visto_subs: set[tuple] = set()
            for dp_entry in todos_validos:
                dp = dp_entry["dp"]
                if dp not in dp_map:
                    dp_map[dp] = {**dp_entry, "substitutos": []}
                for sub in dp_entry.get("substitutos", []):
                    sub_key = (
                        dp,
                        sub.get("substituto"),
                        sub.get("data_inicio"),
                        sub.get("data_fim"),
                    )
                    if sub_key not in visto_subs:
                        visto_subs.add(sub_key)
                        dp_map[dp]["substitutos"].append(sub)

            if not dp_map:
                # Todos eram duplicatas (ramo de segurança)
                for fid, doc, _, _ in docs_analisados:
                    plano["deletar"].append((
                        fid, doc,
                        f"duplicata de evento JSON ({defensor} {di_str}→{df_str})"
                    ))
            else:
                fid_base, doc_base = docs_grupo[0]
                ids_deletar = [fid for fid, _ in docs_grupo[1:]]
                n_docs = len(docs_grupo)
                n_dps  = len(dp_map)
                plano["consolidar"].append({
                    "tipo":                "consolidar",
                    "fid_manter":          fid_base,
                    "doc_base":            doc_base,
                    "ids_deletar":         ids_deletar,
                    "designacoes_dp_nova": list(dp_map.values()),
                    "motivo":              (
                        f"{n_docs} doc(s) → 1, "
                        f"{n_dps} DP(s) válida(s) "
                        f"({defensor} {di_str}→{df_str})"
                    ),
                })

    return plano


# ─── Relatório ───────────────────────────────────────────────────────────────

def imprimir_relatorio(plano: dict, commit: bool) -> None:
    print()
    print("=" * 80)
    print(f"  LIMPEZA DE BACKFILL — {'COMMIT' if commit else 'DRY-RUN'}")
    print("=" * 80)

    deletar    = plano["deletar"]
    consolidar = plano["consolidar"]
    ok         = plano["ok"]

    print(f"\nResumo:")
    print(f"  • Docs a DELETAR (duplicatas do JSON) .... {len(deletar)}")
    print(f"  • Ops de CONSOLIDAR / ATUALIZAR .......... {len(consolidar)}")
    print(f"  • Docs sem ação necessária (OK) .......... {len(ok)}")

    if deletar:
        print(f"\n🗑️  DELETAR ({len(deletar)} docs)")
        print("-" * 80)
        for fid, doc, motivo in deletar:
            ddp = doc.get("designacoes_dp") or []
            dps = ", ".join(str(e.get("dp")) for e in ddp)
            print(f"  [{fid}]")
            print(f"    {doc.get('defensor')}  {doc.get('data_inicio')}→{doc.get('data_fim')}  DP(s): {dps}")
            print(f"    ↳ {motivo}")

    if consolidar:
        print(f"\n🔀 CONSOLIDAR / ATUALIZAR ({len(consolidar)} operações)")
        print("-" * 80)
        for op in consolidar:
            if op["tipo"] == "consolidar":
                print(f"  MANTER  [{op['fid_manter']}]")
                print(f"  DELETAR {op['ids_deletar']}")
                print(f"    ↳ {op['motivo']}")
                for dp_entry in op["designacoes_dp_nova"]:
                    for s in dp_entry.get("substitutos", []):
                        sub = s.get("substituto")
                        ext = s.get("substituto_nome_externo") or ""
                        nome = ext if sub == "_outro" else sub
                        print(f"       DP {dp_entry['dp']}: {nome}  "
                              f"{s.get('data_inicio')}→{s.get('data_fim')}")
            else:
                print(f"  ATUALIZAR [{op['fid']}]")
                print(f"    ↳ {op['motivo']}")
                for dp_entry in op["designacoes_dp_nova"]:
                    for s in dp_entry.get("substitutos", []):
                        sub = s.get("substituto")
                        ext = s.get("substituto_nome_externo") or ""
                        nome = ext if sub == "_outro" else sub
                        print(f"       DP {dp_entry['dp']}: {nome}  "
                              f"{s.get('data_inicio')}→{s.get('data_fim')}")

    if ok:
        print(f"\n✅ SEM AÇÃO ({len(ok)} docs)")
        print("-" * 80)
        for fid, doc, motivo in ok:
            print(f"  [{fid}]  {doc.get('defensor')}  "
                  f"{doc.get('data_inicio')}→{doc.get('data_fim')}  |  {motivo}")

    print()
    print("=" * 80)
    if not commit:
        print("  ℹ️  Dry-run concluído. Use --commit para aplicar as ações.")
    print("=" * 80)
    print()


# ─── Execução ────────────────────────────────────────────────────────────────

def executar(plano: dict, db) -> None:
    from firebase_admin import firestore as fs
    col = db.collection(FIRESTORE_AFASTAMENTOS)
    ts  = fs.SERVER_TIMESTAMP

    deletados    = 0
    consolidados = 0

    for fid, doc, motivo in plano["deletar"]:
        col.document(fid).delete()
        deletados += 1
        print(f"  🗑️  DELETADO   {fid}  "
              f"({doc.get('defensor')} {doc.get('data_inicio')}→{doc.get('data_fim')})")

    for op in plano["consolidar"]:
        if op["tipo"] == "consolidar":
            # Atualiza o doc base com as DPs consolidadas
            col.document(op["fid_manter"]).update({
                "designacoes_dp":  op["designacoes_dp_nova"],
                "atualizado_por":  "limpeza-backfill",
                "atualizado_em":   ts,
            })
            print(f"  🔀 CONSOLIDADO {op['fid_manter']}  ({op['motivo']})")
            consolidados += 1
            # Deleta os docs extras
            for fid_del in op["ids_deletar"]:
                col.document(fid_del).delete()
                deletados += 1
                print(f"  🗑️  DELETADO   {fid_del}  (consolidado em {op['fid_manter']})")
        else:
            col.document(op["fid"]).update({
                "designacoes_dp":  op["designacoes_dp_nova"],
                "atualizado_por":  "limpeza-backfill",
                "atualizado_em":   ts,
            })
            print(f"  ✏️  ATUALIZADO  {op['fid']}  ({op['motivo']})")
            consolidados += 1

    print(f"\n  Total: {deletados} deletado(s), {consolidados} consolidado(s).")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--commit", action="store_true",
        help="Executa as ações no Firestore (padrão é dry-run)"
    )
    args = ap.parse_args()

    if not DESIGNACOES_JSON.exists():
        print(f"❌ Arquivo não encontrado: {DESIGNACOES_JSON}", file=sys.stderr)
        sys.exit(1)

    eventos_json = carregar_eventos_json()
    print(f"📋 {len(eventos_json)} evento(s) JSON carregados.")

    db = get_firestore_client()
    backfill_docs = buscar_backfill_docs(db)
    print(f"🔥 {len(backfill_docs)} documento(s) de backfill encontrados no Firestore.")

    if not backfill_docs:
        print("Nenhum doc de backfill encontrado. Nada a fazer.")
        return

    plano = analisar(backfill_docs, eventos_json)
    imprimir_relatorio(plano, commit=args.commit)

    if args.commit:
        print("\n💾 Executando no Firestore...\n")
        executar(plano, db)


if __name__ == "__main__":
    main()
