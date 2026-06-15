#!/bin/bash
#SBATCH -J laplace_opt_system
#SBATCH -N 4
#SBATCH --ntasks-per-node=28
#SBATCH -p ppx2
#SBATCH -w ppx2-[00-03]
#SBATCH -o out/laplace_opt_%j.out
#SBATCH -e out/laplace_opt_%j.err
#SBATCH -t 00:30:00

set -euo pipefail

# PPX 上で MPI 実行環境を読み込む。
module load openmpi

# 出力先を用意する。
mkdir -p out

# 実行対象とプロセス数
PROCS="1 2 4 8 16 32 64 112"
SOURCES=(laplace_basic1 laplace_basic1_temporal)
REPEATS=1

RAWCSV="out/laplace_opt_raw_$(date +%Y%m%d_%H%M%S).csv"
echo "source,nprocs,repeat_index,elapsed_sec,time_per_iter,status" > "$RAWCSV"

export OMP_NUM_THREADS=1
export OMP_PROC_BIND="${OMP_PROC_BIND:-close}"
export OMP_PLACES="${OMP_PLACES:-cores}"

# 実行バイナリの存在確認
for source in "${SOURCES[@]}"; do
    bin="./bin/${source}"
    if [[ ! -x "$bin" ]]; then
        echo "Missing executable: $bin" >&2
        echo "Build first with: make build" >&2
        exit 1
    fi
done

# ==========================================
# 1. 速度スケーリング計測 (CSV出力)
# ==========================================
for source in "${SOURCES[@]}"; do
    bin="./bin/${source}"
    for np in $PROCS; do
        for rep in $(seq 1 "$REPEATS"); do
            echo "[RUN] source=${source} np=${np} repeat=${rep}" >&2

            set +e
            run_output=$(mpirun --bind-to core --map-by core -np "$np" "$bin" 2>&1)
            rc=$?
            set -e

            printf '%s\n' "$run_output"

            if [[ "$rc" -ne 0 ]]; then
                echo "${source},${np},${rep},,error" >> "$RAWCSV"
                echo "[ERROR] source=${source} np=${np} repeat=${rep} exit=${rc}" >&2
                continue
            fi

            elapsed_sec=$(printf '%s\n' "$run_output" | awk -F'= *' '/^time[[:space:]]*=/{print $2; exit}' | awk '{print $1}')
            time_per_iter=$(printf '%s\n' "$run_output" | awk -F'= *' '/^time_per_iter[[:space:]]*=/{print $2; exit}' | awk '{print $1}')

            echo "${source},${np},${rep},${elapsed_sec},${time_per_iter},ok" >> "$RAWCSV"
        done
    done
done

echo "[DONE] raw CSV: ${RAWCSV}" >&2

echo "すべての処理が完了しました。" >&2
