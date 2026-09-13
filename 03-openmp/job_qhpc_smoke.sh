#!/bin/bash
# Tiny OpenMP smoke — Pegasus QHPC. OpenMP only. No MPI.
# QHPC cannot qsub gen_S (EACCESSDEN). Batch queue is gpu (CPU OpenMP is fine).
# debug is INTERACTIVE only: qlogin -A QHPC -q debug, then bash job_debug_smoke.sh
#PBS -q gpu
#PBS -A QHPC
#PBS -b 1
#PBS -l elapstim_req=00:03:00
#PBS -N matvec_qhpc_smoke
#PBS -o matvec_qhpc_smoke.o
#PBS -e matvec_qhpc_smoke.e

set -euo pipefail

cd "${PBS_O_WORKDIR}"

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
echo "CSV: ${PBS_O_WORKDIR}/results/matvec_qhpc_smoke.csv"
