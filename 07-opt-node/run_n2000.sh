#!/bin/bash
#SBATCH -J matvec_n2000_full
#SBATCH -N 1
#SBATCH -p ppx2
#SBATCH -w ppx2-00
#SBATCH -o out/matvec_n2000_%j.out
#SBATCH -e out/matvec_n2000_%j.err
#SBATCH -t 01:00:00

# 1. set -u を一時的にオフにする（これが原因です）
set +u
set -e
set -o pipefail

# 2. LD_LIBRARY_PATH が空でもエラーにならないように設定
if [ -z "${LD_LIBRARY_PATH:-}" ]; then
    export LD_LIBRARY_PATH=/opt/nvidia/hpc_sdk/Linux_x86_64/26.3/compilers/lib
else
    export LD_LIBRARY_PATH=/opt/nvidia/hpc_sdk/Linux_x86_64/26.3/compilers/lib:$LD_LIBRARY_PATH
fi

# 3. 再度 set -u を有効化
set -u

# ====================================================
# [重要] マルチスレッド暴走を防ぐ
# ====================================================
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

# (以下、実行ループ等の処理は変更なし)

# 出力先用意
mkdir -p out

# CSVヘッダー
CSV_FILE="out/results_n2000_all_$(date +%Y%m%d_%H%M%S).csv"
echo "source,n_size,opt_type,repeat,time" > "$CSV_FILE"

# 実験パラメータ (dgemm と新しい非対称サイズを追加)
N_SIZE="n2000"
BASE_NAMES=(original loopswap padding loopswap_padding loopswap_unroll dgemm)
BLOCK_SIZES=(1_8_8 4_4_4 8_8_8 16_16_16 32_32_32 48_48_48 40_8_8 8_8_40 64_64_64 128_128_128 32_128_16 32_96_32 16_256_8)
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

# 実行完了後、最新のCSVを "results_n2000_latest.csv" としてコピーしておく
cp "$CSV_FILE" "out/results_n2000_latest.csv"

echo "Experiment complete. Results saved to ${CSV_FILE} and copied to out/results_n2000_latest.csv"
