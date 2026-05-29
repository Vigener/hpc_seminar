#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
BIN_DIR="$ROOT_DIR/bin"
OUT_DIR="$ROOT_DIR/out"
RESULT_DIR="$ROOT_DIR/results"
RUN_OUT="$OUT_DIR/run.out"
CSV_OUT="$RESULT_DIR/matvec_bench.csv"

read -r -a SIZES <<< "${MATVEC_SIZES:-4096 8192}"
read -r -a THREADS <<< "${MATVEC_THREADS:-1 2 4}"
MODE_KEYS=(serial parallel simd_reduction no_simd)

declare -A MODE_BINARIES=(
    [serial]="matvec_serial"
    [parallel]="matvec_parallel"
    [simd_reduction]="matvec_simd_reduction"
    [no_simd]="matvec_no_simd"
)

mkdir -p "$OUT_DIR" "$RESULT_DIR"
: > "$RUN_OUT"
printf 'size,mode,threads,time_sec\n' > "$CSV_OUT"

export OMP_PROC_BIND="${OMP_PROC_BIND:-close}"
export OMP_PLACES="${OMP_PLACES:-cores}"

for size in "${SIZES[@]}"; do
    for threads in "${THREADS[@]}"; do
        for mode in "${MODE_KEYS[@]}"; do
            binary="$BIN_DIR/${MODE_BINARIES[$mode]}"
            if [[ ! -x "$binary" ]]; then
                echo "Missing binary: $binary" >&2
                exit 1
            fi

            run_output=$(OMP_NUM_THREADS="$threads" "$binary" --size "$size")
            {
                printf '%s\n' "$run_output"
                printf '\n'
            } >> "$RUN_OUT"

            time_sec=$(printf '%s\n' "$run_output" | sed -n 's/.*Execution Time: \([0-9.][0-9.]*\) sec.*/\1/p' | head -n 1)
            if [[ -z "$time_sec" ]]; then
                echo "Failed to parse execution time for size=$size threads=$threads mode=$mode" >&2
                exit 1
            fi

            printf '%s,%s,%s,%s\n' "$size" "$mode" "$threads" "$time_sec" >> "$CSV_OUT"
        done
    done
done

echo "Wrote $RUN_OUT"
echo "Wrote $CSV_OUT"