#!/bin/bash
# UNUSED for this run. Use job_qhpc.sh (Pegasus lab project QHPC / gen_S).
# Lecture 03 OpenMP matvec — Pegasus lecture project EDU1, one node.
# OpenMP only. Do NOT add #PBS -T openmpi or mpirun.
# Submit from /work/EDU1/migarashi/03-openmp (not from /home).
#PBS -q edu-1
#PBS -A EDU1
#PBS -b 1
#PBS -l elapstim_req=00:30:00
#PBS -N matvec_edu1
#PBS -o matvec_edu1.o
#PBS -e matvec_edu1.e

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

make edu1-bins

# Full measurement: N=4096 and 8192; threads 1,2,4,8,16; warmup then median.
# simd_reduction is not part of this job.
./scripts/run_matvec_edu1.sh

echo "=== job end $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "CSV: ${PBS_O_WORKDIR}/results/matvec_edu1.csv"
echo "LOG: ${PBS_O_WORKDIR}/out/run_edu1.out"
