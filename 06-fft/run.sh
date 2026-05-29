#!/usr/bin/env bash
#SBATCH --job-name=fft-benchmark
#SBATCH --output=out/fft_benchmark.%j.out
#SBATCH --error=out/fft_benchmark.%j.err
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=1

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

# PPX では既存の実行バイナリを直接呼ぶ
mkdir -p ./out
./bin/fft_benchmark_cpp --size "${FFT_SIZE:-65536}" > ./out/fft_benchmark.csv

echo "Wrote ./out/fft_benchmark.csv"