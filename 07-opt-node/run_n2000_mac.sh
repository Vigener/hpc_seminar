#!/bin/bash
set -euo pipefail

# ====================================================
# [重要] Apple Accelerateフレームワークのマルチスレッド暴走を防ぐ
# 必ず1コア（シングルスレッド）で実行させるための制約
# ====================================================
export VECLIB_MAXIMUM_THREADS=1

# 出力先用意
mkdir -p out

# CSVヘッダー
CSV_FILE="out/results_n2000_mac_$(date +%Y%m%d_%H%M%S).csv"
echo "source,n_size,opt_type,repeat,time" > "$CSV_FILE"

# 実験パラメータ
N_SIZE="n2000"
BASE_NAMES=(original loopswap padding loopswap_padding loopswap_unroll)
BLOCK_SIZES=(1_8_8 4_4_4 8_8_8 16_16_16 32_32_32 48_48_48 40_8_8 8_8_40 64_64_64 128_128_128 32_128_16 32_96_32 16_256_8)
REPEATS=3

# ローカル環境用なので、opt は "mac_native" として記録します
opt="mac_native"

echo "Starting Experiments on Mac..."

# 1. 基本手法の実行
for base in "${BASE_NAMES[@]}"; do
    source_name="matvec_${base}_${N_SIZE}"

    # バイナリが存在するかチェック
    if [ ! -f "./bin/${source_name}" ]; then
        echo "Skip: ./bin/${source_name} not found."
        continue
    fi

    echo "Testing: ${source_name} (${opt})"
    for r in $(seq 1 $REPEATS); do
        res=$(./bin/${source_name})
        exec_time=$(echo "$res" | grep -v "Dummy:")
        echo "${source_name},${N_SIZE},${opt},${r},${exec_time}" >> "$CSV_FILE"
    done
done

# dgemm は特殊（バイナリ名に _mac サフィックス付き）
source_name="matvec_dgemm_${N_SIZE}_mac"
if [ -f "./bin/${source_name}" ]; then
    echo "Testing: ${source_name} (${opt})"
    for r in $(seq 1 $REPEATS); do
        res=$(./bin/${source_name})
        exec_time=$(echo "$res" | grep -v "Dummy:")
        echo "${source_name},${N_SIZE},${opt},${r},${exec_time}" >> "$CSV_FILE"
    done
else
    echo "Skip: ./bin/${source_name} not found."
fi

# 2. ブロッキング手法の実行
for size in "${BLOCK_SIZES[@]}"; do
    source_name="matvec_blocking_${size}_${N_SIZE}"

    if [ ! -f "./bin/${source_name}" ]; then
        continue
    fi

    echo "Testing: ${source_name} (${opt})"
    for r in $(seq 1 $REPEATS); do
        res=$(./bin/${source_name})
        exec_time=$(echo "$res" | grep -v "Dummy:")
        echo "${source_name},${N_SIZE},${opt},${r},${exec_time}" >> "$CSV_FILE"
    done
done

# 3. ループ入れ替え＋ブロッキング手法の実行
for size in "${BLOCK_SIZES[@]}"; do
    source_name="matvec_loopswap_blocking_${size}_${N_SIZE}"

    if [ ! -f "./bin/${source_name}" ]; then
        continue
    fi

    echo "Testing: ${source_name} (${opt})"
    for r in $(seq 1 $REPEATS); do
        res=$(./bin/${source_name})
        exec_time=$(echo "$res" | grep -v "Dummy:")
        echo "${source_name},${N_SIZE},${opt},${r},${exec_time}" >> "$CSV_FILE"
    done
done

# 実行完了後、最新のCSVを "results_n2000_latest_mac.csv" としてコピーしておく
cp "$CSV_FILE" "out/results_n2000_latest_mac.csv"

echo "Experiment complete. Results saved to ${CSV_FILE} and copied to out/results_n2000_latest_mac.csv"
