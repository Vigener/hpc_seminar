#!/bin/bash
# Tiny OpenMP smoke after: qlogin -A QHPC -q debug
# OpenMP only. Do NOT add mpirun. Not the grading measurement.
set -euo pipefail

cd "$(dirname "$0")"

echo "=== smoke start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "hostname=$(hostname)"
echo "whoami=$(whoami)"
echo "pwd=$(pwd)"
gcc --version | head -n 1

mkdir -p bin out results
make qhpc-bins

MATVEC_SIZES=256 MATVEC_THREADS="1 2" MATVEC_WARMUP=1 MATVEC_REPS=2 \
  CSV_OUT=results/matvec_qhpc_smoke.csv \
  RUN_OUT=out/run_qhpc_smoke.out \
  ./scripts/run_matvec_edu1.sh

echo "=== smoke end $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "CSV: $(pwd)/results/matvec_qhpc_smoke.csv"
