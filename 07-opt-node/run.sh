#!/bin/bash
#SBATCH -J matvec_ppx
#SBATCH -N 1
#SBATCH -p ppx2
#SBATCH -w ppx2-00
#SBATCH -o out/matvec_%j.out
#SBATCH -e out/matvec_%j.err
#SBATCH -t 00:30:00

set -euo pipefail

# 出力先を用意する。
mkdir -p out

# CSV出力先の定義とヘッダーの書き込み
CSV_FILE="out/matvec_ppx_$(date +%Y%m%d_%H%M%S).csv"
echo "source,repeat,time" > "$CSV_FILE"

SOURCES=(
    matvec_original
    matvec_loopswap
    # matvec_padding
    matvec_loopswap_padding
    matvec_loopswap_unroll
)
REPEATS=3
for source in "${SOURCES[@]}"; do
    for repeat_index in $(seq 1 "$REPEATS"); do
        echo "Running ${source}, repeat ${repeat_index}"
        # 実行結果を変数に格納し、元の標準出力の挙動も維持する
        res=$(./bin/${source})
        echo "$res"

        # Dummy: の行を除外して実行結果（時間）のみを抽出
        exec_time=$(echo "$res" | grep -v "Dummy:")

        # CSVファイルに構造化して追記
        echo "${source},${repeat_index},${exec_time}" >> "$CSV_FILE"
    done
done
