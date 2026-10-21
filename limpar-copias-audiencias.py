#!/usr/bin/env python3
"""
Apaga as cópias integrais de processos (seção Audiências do site) de semanas
que já passaram. As cópias ficam no Firebase Storage em
audiencias-copias/{semana ISO}/{processo}.pdf e só valem para a semana da
audiência; a partir da segunda-feira seguinte este script apaga os PDFs e
remove o campo `copias` de audiencias_semanas/{semana}.

O site faz a mesma limpeza quando um admin abre Audiências
(_audLimparCopiasAntigas() no index.html); este script garante a limpeza
mesmo que ninguém abra o site. Roda toda segunda pelo GitHub Actions
(.github/workflows/limpar-copias-audiencias.yml).

Credencial: variável FIREBASE_SERVICE_ACCOUNT (JSON) ou
firebase-service-account.json na raiz. --dry-run só lista o que apagaria.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
BUCKET = "polo-medio-as.firebasestorage.app"
PASTA = "audiencias-copias/"
MANAUS = timezone(timedelta(hours=-4))  # sem horário de verão

# Mesmo ajuste de CA do backup-firestore.py (antivírus com inspeção SSL nesta máquina)
_CA_BUNDLE = PROJECT_DIR / ".cache" / "ca-bundle.pem"
if _CA_BUNDLE.exists():
    os.environ.setdefault("GRPC_DEFAULT_SSL_ROOTS_FILE_PATH", str(_CA_BUNDLE))
    os.environ.setdefault("SSL_CERT_FILE", str(_CA_BUNDLE))
    os.environ.setdefault("REQUESTS_CA_BUNDLE", str(_CA_BUNDLE))

import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud.firestore_v1.base_query import FieldFilter


def inicializar():
    sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "").strip()
    if sa_json:
        cred = credentials.Certificate(json.loads(sa_json))
    else:
        sa_path = PROJECT_DIR / "firebase-service-account.json"
        if not sa_path.exists():
            raise RuntimeError("Credencial do Firebase não encontrada (FIREBASE_SERVICE_ACCOUNT "
                               "ou firebase-service-account.json).")
        cred = credentials.Certificate(str(sa_path))
    firebase_admin.initialize_app(cred, {"storageBucket": BUCKET})


def semana_iso(d):
    ano, sem, _ = d.isocalendar()
    return f"{ano}-W{sem:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="só lista, não apaga")
    args = ap.parse_args()

    inicializar()
    atual = semana_iso(datetime.now(MANAUS).date())
    print(f"Semana atual (Manaus): {atual}", flush=True)

    apagados = 0
    for blob in storage.bucket().list_blobs(prefix=PASTA):
        semana = blob.name[len(PASTA):].split("/", 1)[0]
        if semana and semana < atual:
            print(f"{'[dry-run] ' if args.dry_run else ''}apagando {blob.name}")
            if not args.dry_run:
                blob.delete()
            apagados += 1

    db = firestore.client()
    docs_limpos = 0
    for doc in db.collection("audiencias_semanas").where(filter=FieldFilter("semana", "<", atual)).stream():
        if "copias" in (doc.to_dict() or {}):
            print(f"{'[dry-run] ' if args.dry_run else ''}removendo lista de cópias de {doc.id}")
            if not args.dry_run:
                doc.reference.update({"copias": firestore.DELETE_FIELD})
            docs_limpos += 1

    print(f"Concluído: {apagados} arquivo(s) e {docs_limpos} semana(s) limpos.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(1)
