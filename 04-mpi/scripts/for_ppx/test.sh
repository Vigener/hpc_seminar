#!/bin/bash
#SBATCH -J laplace_ppx
#SBATCH -N 1                     # ノード数（ここは最大プロセス数が1ノードに収まるなら1）
#SBATCH --ntasks-per-node=28     # ノード当たりタスク数（ノードが28コアなら28）
#SBATCH -p ppx2
#SBATCH -w ppx2-00
#SBATCH -o out/laplace_%j.out
#SBATCH -e out/laplace_%j.err
#SBATCH -t 00:30:00              # ジョブの最大実行時間 (HH:MM:SS)

module load openmpi

set -euo pipefail

mkdir -p out
RAWCSV="out/laplace_ppx_$(date +%Y%m%d_%H%M%S).csv"
echo "source,nprocs,repeat_index,elapsed_sec" > "$RAWCSV"

export OMP_NUM_THREADS=1

for np in 1 2 4 8 16; do
    echo "mpirun -n ${np} ./bin/laplace"
    mpirun -n "${np}" ./bin/laplace
    echo "mpirun -n ${np} ./bin/laplace_basic1"
    mpirun -n "${np}" ./bin/laplace_basic1
    echo "mpirun -n ${np} ./bin/laplace_basic2"
    mpirun -n "${np}" ./bin/laplace_basic2
    echo "mpirun -n ${np} ./bin/laplace_advanced"
    mpirun -n "${np}" ./bin/laplace_advanced
done
