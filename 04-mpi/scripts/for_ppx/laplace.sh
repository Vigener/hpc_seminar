#!/bin/bash
#SBATCH -J laplace
#SBATCH -N 4 # 4台の計算ノード全てを要求
#SBATCH -p ppx2
#SBATCH -w ppx2-[00-03]
#SBATCH -o out/laplace_%j.out
#SBATCH --ntasks=64

module load openmpi

set -euo pipefail

mkdir -p out

echo "timestamp,source,nprocs,repeat_index,elapsed_sec,status" > "$RAWCSV"
export OMP_NUM_THREADS=1

for process_count in 1 2 4 8 16; do
    echo "Running with ${process_count} processes..."
    echo "mpirun -n ${process_count} ./laplace"
    for i in {1..10}; do
        mpirun -n "${process_count}" ./laplace
    done
    echo "mpirun -n ${process_count} ./laplace_basic1"
    for i in {1..10}; do
        mpirun -n "${process_count}" ./laplace_basic1
    done
    echo "mpirun -n ${process_count} ./laplace_basic2"
    for i in {1..10}; do
        mpirun -n "${process_count}" ./laplace_basic2
    done
    echo "mpirun -n ${process_count} ./laplace_advanced"
    for i in {1..10}; do
        mpirun -n "${process_count}" ./laplace_advanced
    done
done