#!/bin/bash
#SBATCH -J matvec_n2000_full
#SBATCH -N 1
#SBATCH -p ppx2
#SBATCH -w ppx2-00
#SBATCH -o out/matvec_n2000_%j.out
#SBATCH -e out/matvec_n2000_%j.err
#SBATCH -t 01:00:00

set -euo pipefail

# 出力先用意
mkdir -p out

# CSVヘッダー（n_size列を追加して、後で1000の結果と結合しやすくします）
CSV_FILE="out/results_n2000_all.csv"
echo "source,n_size,opt_type,repeat,time" > "$CSV_FILE"

# 実験パラメータ
N_SIZE="n2000"
BASE_NAMES=(original loopswap padding loopswap_padding loopswap_unroll)
BLOCK_SIZES=(1_8_8 4_4_4 8_8_8 16_16_16 32_32_32 48_48_48 40_8_8 8_8_40 64_64_64 128_128_128)
REPEATS=3

# 実行ループ
for opt in "generic" "ppx_tuned"; do
    # 最適化タイプによってバイナリの接尾辞を切り替える
    suffix=""
    [[ "$opt" == "ppx_tuned" ]] && suffix="_ppx"

    # 1. 基本手法の実行
    for base in "${BASE_NAMES[@]}"; do
        source_name="matvec_${base}_${N_SIZE}${suffix}"
        echo "Testing: ${source_name} (${opt})"

        for r in $(seq 1 $REPEATS); do
            res=$(./bin/${source_name})
            exec_time=$(echo "$res" | grep -v "Dummy:")
            echo "${source_name},${N_SIZE},${opt},${r},${exec_time}" >> "$CSV_FILE"
        done
    done

    # 2. ブロッキング手法の実行
    for size in "${BLOCK_SIZES[@]}"; do
        source_name="matvec_blocking_${size}_${N_SIZE}${suffix}"
        echo "Testing: ${source_name} (${opt})"

        for r in $(seq 1 $REPEATS); do
            res=$(./bin/${source_name})
            exec_time=$(echo "$res" | grep -v "Dummy:")
            echo "${source_name},${N_SIZE},${opt},${r},${exec_time}" >> "$CSV_FILE"
        done
    done

    # 3. ループ入れ替え＋ブロッキング手法の実行
    for size in "${BLOCK_SIZES[@]}"; do
        source_name="matvec_loopswap_blocking_${size}_${N_SIZE}${suffix}"
        echo "Testing: ${source_name} (${opt})"

        for r in $(seq 1 $REPEATS); do
            res=$(./bin/${source_name})
            exec_time=$(echo "$res" | grep -v "Dummy:")
            echo "${source_name},${N_SIZE},${opt},${r},${exec_time}" >> "$CSV_FILE"
        done
    done
done

echo "Experiment complete. Results saved to ${CSV_FILE}"
