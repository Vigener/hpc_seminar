#!/usr/bin/env bash
#SBATCH --job-name=fft-benchmark
#SBATCH --output=out/fft_benchmark.%j.out
#SBATCH --error=out/fft_benchmark.%j.err
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=1

set -euo pipefail

# PPX では既存の実行バイナリを直接呼ぶ
mkdir -p out

# 実行結果を CSV に残す。
RAWCSV="out/fft_benchmark_ppx_$(date +%Y%m%d_%H%M%S).csv"
./bin/fft_benchmark_cpp --size "${FFT_SIZE:-65536}" > "$RAWCSV"

echo "Wrote $RAWCSV"