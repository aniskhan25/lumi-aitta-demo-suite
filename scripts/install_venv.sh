#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${ROOT_DIR}/env/lumi-env.sh"

module purge
module use /appl/local/laifs/modules
module load lumi-aif-singularity-bindings

mkdir -p "${AITTA_DATA_ROOT}" "${AITTA_OUTPUT_ROOT}" "${AITTA_REPORT_ROOT}" "$(dirname "${AITTA_VENV}")"

singularity exec "${CONTAINER}" bash -lc "
set -euo pipefail
python3 -m venv '${AITTA_VENV}' --system-site-packages
'${AITTA_VENV}/bin/python' -m pip install --upgrade pip setuptools wheel
'${AITTA_VENV}/bin/python' -m pip install -r '${ROOT_DIR}/env/requirements.txt'
"
