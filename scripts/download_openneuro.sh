#!/usr/bin/env bash
# Descarga OpenNeuro ds003490 desde el bucket público de S3 (sin credenciales).
# Reproduce el mecanismo del cuaderno 01. Requiere la CLI de AWS: pip install awscli
#
# Uso:  bash scripts/download_openneuro.sh
# Destino: ${PARKINSON_EEG_DATA:-data/openneuro}/ds003490
set -euo pipefail

DATA_DIR="${PARKINSON_EEG_DATA:-data/openneuro}"
TARGET="${DATA_DIR}/ds003490"

if ! command -v aws >/dev/null 2>&1; then
  echo "No se encontró la CLI 'aws'. Instálela con: pip install awscli" >&2
  exit 1
fi

mkdir -p "${TARGET}"
echo "Descargando ds003490 en ${TARGET} ..."
aws s3 sync --no-sign-request s3://openneuro.org/ds003490 "${TARGET}" \
  --exclude "*" \
  --include "*.set" --include "*.fdt" --include "*.json" --include "*.tsv" \
  --include "participants.tsv" --include "README"
echo "Listo: ${TARGET}"
