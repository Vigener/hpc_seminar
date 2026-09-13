#!/bin/bash
# Lecture 03 OpenMP matvec — Pegasus lab project QHPC, one CPU node.
# OpenMP only. Do NOT add #PBS -T openmpi or mpirun.
# Submit from /work/QHPC/migarashi/projects/03-openmp (not from /home).
# QHPC cannot qsub gen_S. Batch queue is gpu (node has H100; this job is CPU OpenMP).
#PBS -q gpu
#PBS -A QHPC
#PBS -b 1
#PBS -l elapstim_req=00:03:00
#PBS -N matvec_qhpc
#PBS -o matvec_qhpc.o
#PBS -e matvec_qhpc.e

set -euo pipefail

cd "${PBS_O_WORKDIR}"

echo "=== job start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "PBS_O_WORKDIR=${PBS_O_WORKDIR}"
echo "hostname=$(hostname)"
echo "whoami=$(whoami)"
echo "pwd=$(pwd)"
command -v nproc >/dev/null && echo "nproc=$(nproc)"
gcc --version | head -n 1

mkdir -p bin out results

make qhpc-bins

CSV_OUT=results/matvec_qhpc.csv \
  RUN_OUT=out/run_qhpc.out \
  ./scripts/run_matvec_edu1.sh

echo "=== job end $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "CSV: ${PBS_O_WORKDIR}/results/matvec_qhpc.csv"
echo "LOG: ${PBS_O_WORKDIR}/out/run_qhpc.out"
