#!/usr/bin/env python3
"""
Backup do Firestore (projeto polo-medio-as) para arquivos JSON locais.
Exporta todas as coleções (e subcoleções, se existirem) para uma pasta
com timestamp em backups/firestore/. Rodar periodicamente (manual ou
via Tarefa Agendada do Windows — ver criar-tarefa-agendada-backup.ps1).
"""

import os
import sys
import json
import base64
import shutil
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
FIREBASE_PROJECT_ID = "polo-medio-as"
DESTINO_PADRAO = PROJECT_DIR / "backups" / "firestore"
MANTER_PADRAO = 20  # quantos backups mais recentes preservar

# Máquinas com antivírus que faz inspeção SSL (ex.: Kaspersky) usam um
# certificado raiz próprio que o Windows confia, mas o gRPC (usado pelo
# cliente do Firestore) não — dá erro "self signed certificate in
# certificate chain". Se existir um bundle de CA combinado em .cache/
# (certifi + raízes do antivírus, específico desta máquina — ver comando
# de geração no fim deste arquivo), aponta o gRPC pra ele antes de
# importar qualquer biblioteca do Google.
_CA_BUNDLE = PROJECT_DIR / ".cache" / "ca-bundle.pem"
if _CA_BUNDLE.exists():
    os.environ.setdefault("GRPC_DEFAULT_SSL_ROOTS_FILE_PATH", str(_CA_BUNDLE))
    os.environ.setdefault("SSL_CERT_FILE", str(_CA_BUNDLE))
    os.environ.setdefault("REQUESTS_CA_BUNDLE", str(_CA_BUNDLE))

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import DocumentReference, GeoPoint

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
log = logging.getLogger("backup-firestore")


def inicializar_firestore():
    """Mesma lógica de credenciais usada em verificar-diario-oficial.py:
    var de ambiente FIREBASE_SERVICE_ACCOUNT (JSON) ou arquivo local
    firebase-service-account.json na raiz do projeto."""
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
                "Credencial do Firebase não encontrada. Defina FIREBASE_SERVICE_ACCOUNT "
                "(JSON) ou coloque firebase-service-account.json na raiz do projeto."
            )
        firebase_admin.initialize_app(cred, {"projectId": FIREBASE_PROJECT_ID})
    return firestore.client()


def serializar_valor(valor):
    """Converte tipos do Firestore (Timestamp, GeoPoint, DocumentReference,
    bytes) em algo serializável em JSON, sem perder a informação original."""
    if isinstance(valor, datetime):
        return {"__type__": "timestamp", "value": valor.isoformat()}
    if isinstance(valor, DocumentReference):
        return {"__type__": "reference", "path": valor.path}
    if isinstance(valor, GeoPoint):
        return {"__type__": "geopoint", "lat": valor.latitude, "lng": valor.longitude}
    if isinstance(valor, bytes):
        return {"__type__": "bytes", "value": base64.b64encode(valor).decode("ascii")}
    if isinstance(valor, dict):
        return {k: serializar_valor(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [serializar_valor(v) for v in valor]
    return valor


def exportar_documento(doc_snap):
    """Exporta um documento e, recursivamente, suas subcoleções (se houver)."""
    dados = {"__id__": doc_snap.id, **serializar_valor(doc_snap.to_dict() or {})}
    subcolecoes = list(doc_snap.reference.collections())
    if subcolecoes:
        dados["__subcolecoes__"] = {
            sub.id: exportar_colecao(sub) for sub in subcolecoes
        }
    return dados


def exportar_colecao(colecao_ref):
    return [exportar_documento(doc) for doc in colecao_ref.stream()]


def fazer_backup(destino_base: Path, manter: int) -> Path:
    db = inicializar_firestore()

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    pasta_backup = destino_base / timestamp
    pasta_backup.mkdir(parents=True, exist_ok=True)

    manifesto = {"projeto": FIREBASE_PROJECT_ID, "gerado_em_utc": timestamp, "colecoes": {}}

    for colecao_ref in db.collections():
        nome = colecao_ref.id
        log.info(f"Exportando coleção '{nome}'...")
        documentos = exportar_colecao(colecao_ref)

        arquivo = pasta_backup / f"{nome}.json"
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(documentos, f, ensure_ascii=False, indent=2)

        manifesto["colecoes"][nome] = len(documentos)
        log.info(f"  -> {len(documentos)} documento(s) salvos em {arquivo.name}")

    with open(pasta_backup / "_manifesto.json", "w", encoding="utf-8") as f:
        json.dump(manifesto, f, ensure_ascii=False, indent=2)

    total_docs = sum(manifesto["colecoes"].values())
    log.info(f"Backup concluído: {len(manifesto['colecoes'])} coleção(ões), {total_docs} documento(s) -> {pasta_backup}")

    limpar_backups_antigos(destino_base, manter)
    return pasta_backup


def limpar_backups_antigos(destino_base: Path, manter: int):
    if not destino_base.exists():
        return
    pastas = sorted(
        [p for p in destino_base.iterdir() if p.is_dir()],
        key=lambda p: p.name,
        reverse=True,
    )
    for antiga in pastas[manter:]:
        log.info(f"Removendo backup antigo: {antiga.name}")
        shutil.rmtree(antiga, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Backup do Firestore para JSON local.")
    parser.add_argument("--destino", default=str(DESTINO_PADRAO), help="Pasta onde salvar os backups")
    parser.add_argument("--manter", type=int, default=MANTER_PADRAO, help="Quantos backups recentes manter")
    args = parser.parse_args()

    try:
        fazer_backup(Path(args.destino), args.manter)
    except Exception as e:
        log.error(f"Falha no backup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


# ─── Erro de SSL ("self signed certificate in certificate chain")? ───────────
# Sintoma: o script falha na conexão com o Firestore mesmo com internet
# normal. Causa comum: antivírus com inspeção SSL (ex. Kaspersky) instala um
# certificado raiz próprio que o Windows confia mas o Python/gRPC não.
# Solução (gera .cache/ca-bundle.pem, já ignorado pelo git — rodar 1x por
# máquina em PowerShell, ajustando o caminho do certifi se necessário):
#
#   $destino = Join-Path $PWD '.cache'
#   New-Item -ItemType Directory -Force -Path $destino | Out-Null
#   $certifi = python -c "import certifi; print(certifi.where())"
#   $saida = Join-Path $destino 'ca-bundle.pem'
#   Copy-Item $certifi $saida -Force
#   Get-ChildItem Cert:\LocalMachine\Root, Cert:\CurrentUser\Root |
#     Where-Object { $_.Subject -match 'Kaspersky' } |
#     ForEach-Object {
#       Add-Content $saida "`n# $($_.Subject)"
#       $b64 = [Convert]::ToBase64String($_.RawData, 'InsertLineBreaks')
#       Add-Content $saida "-----BEGIN CERTIFICATE-----`n$b64`n-----END CERTIFICATE-----"
#     }
