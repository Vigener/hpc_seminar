#!/usr/bin/env bash
#SBATCH --job-name=fft-benchmark
#SBATCH --output=out/fft_benchmark.%j.out
#SBATCH --error=out/fft_benchmark.%j.err
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR="$SCRIPT_DIR"
BIN="$ROOT_DIR/bin/fft_benchmark"
BIN_CPP="$ROOT_DIR/bin/fft_benchmark_cpp"
CSV_OUT="$ROOT_DIR/out/fft_benchmark.csv"
SIZE="${FFT_SIZE:-65536}"

if [[ -x "$BIN_CPP" ]]; then
    BIN="$BIN_CPP"
elif [[ ! -x "$BIN" ]]; then
    echo "Missing binary: $BIN_CPP" >&2
    echo "Missing binary: $BIN" >&2
    exit 1
fi

mkdir -p "$ROOT_DIR/out"

"$BIN" --size "$SIZE" > "$CSV_OUT"

echo "Wrote $CSV_OUT"