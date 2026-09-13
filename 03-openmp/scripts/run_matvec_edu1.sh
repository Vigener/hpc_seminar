#!/usr/bin/env bash
# Measurement harness for Lecture 03 (Pegasus EDU1).
# Kernels are unchanged: bin/matvec_serial and bin/matvec_parallel only.
# Does not run matvec_simd_reduction.
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
BIN_DIR="$ROOT_DIR/bin"
OUT_DIR="$ROOT_DIR/out"
RESULT_DIR="$ROOT_DIR/results"

SERIAL_BIN="$BIN_DIR/matvec_serial"
PARALLEL_BIN="$BIN_DIR/matvec_parallel"
RUN_OUT="${RUN_OUT:-$OUT_DIR/run_edu1.out}"
CSV_OUT="${CSV_OUT:-$RESULT_DIR/matvec_edu1.csv}"

read -r -a SIZES <<< "${MATVEC_SIZES:-4096 8192}"
read -r -a THREADS <<< "${MATVEC_THREADS:-1 2 4 8 16}"
WARMUP="${MATVEC_WARMUP:-2}"
REPS="${MATVEC_REPS:-7}"

export OMP_PROC_BIND="${OMP_PROC_BIND:-close}"
export OMP_PLACES="${OMP_PLACES:-cores}"

if [[ ! -x "$SERIAL_BIN" || ! -x "$PARALLEL_BIN" ]]; then
    echo "Missing binaries. Build with: make edu1-bins" >&2
    echo "Looked for: $SERIAL_BIN $PARALLEL_BIN" >&2
    exit 1
fi

mkdir -p "$OUT_DIR" "$RESULT_DIR"
: > "$RUN_OUT"

timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

{
    echo "=== matvec EDU1 harness $(timestamp) ==="
    echo "host=$(hostname)"
    echo "whoami=$(whoami 2>/dev/null || true)"
    command -v nproc >/dev/null && echo "nproc=$(nproc)"
    gcc --version 2>/dev/null | head -n 1 || true
    echo "sizes=${SIZES[*]}"
    echo "threads=${THREADS[*]}"
    echo "warmup=$WARMUP reps=$REPS"
    echo "OMP_PROC_BIND=$OMP_PROC_BIND OMP_PLACES=$OMP_PLACES"
    echo
} | tee -a "$RUN_OUT"

parse_time() {
    local text=$1
    printf '%s\n' "$text" | sed -n 's/.*Execution Time: \([0-9.][0-9.]*\) sec.*/\1/p' | head -n 1
}

median() {
    printf '%s\n' "$@" | awk '
        NF && $1+0 == $1 { a[++n] = $1 + 0 }
        END {
            if (n == 0) { print "nan"; exit 1 }
            for (i = 1; i <= n; i++) {
                for (j = i + 1; j <= n; j++) {
                    if (a[j] < a[i]) { t = a[i]; a[i] = a[j]; a[j] = t }
                }
            }
            if (n % 2) printf "%.9f\n", a[(n + 1) / 2]
            else printf "%.9f\n", (a[n / 2] + a[n / 2 + 1]) / 2
        }'
}

run_median() {
    local bin=$1
    local size=$2
    local threads=$3
    local label=$4
    local i output t
    local -a times=()

    for ((i = 1; i <= WARMUP; i++)); do
        output=$(OMP_NUM_THREADS="$threads" "$bin" --size "$size")
        {
            echo "[warmup $i/$WARMUP] size=$size threads=$threads $label"
            printf '%s\n' "$output"
            echo
        } >> "$RUN_OUT"
    done

    for ((i = 1; i <= REPS; i++)); do
        output=$(OMP_NUM_THREADS="$threads" "$bin" --size "$size")
        t=$(parse_time "$output")
        if [[ -z "$t" ]]; then
            echo "Failed to parse time: size=$size threads=$threads $label" >&2
            printf '%s\n' "$output" >&2
            exit 1
        fi
        times+=("$t")
        {
            echo "[rep $i/$REPS] size=$size threads=$threads $label time=$t"
            printf '%s\n' "$output"
            echo
        } >> "$RUN_OUT"
    done

    median "${times[@]}"
}

printf 'size,mode,threads,n_warmup,n_reps,median_sec,speedup_vs_serial,efficiency_vs_serial,speedup_vs_p1,efficiency_vs_p1\n' > "$CSV_OUT"

note_speedup() {
    echo "NOTE: assignment example '370% using 4 threads' is speedup*100, not efficiency." | tee -a "$RUN_OUT"
    echo "      efficiency E(p) = S(p)/p with S(p)=T(1)/T(p)." | tee -a "$RUN_OUT"
}

note_speedup

for size in "${SIZES[@]}"; do
    t_serial=$(run_median "$SERIAL_BIN" "$size" 1 serial)
    printf '%s,serial,1,%s,%s,%s,1.000000000,1.000000000,,\n' \
        "$size" "$WARMUP" "$REPS" "$t_serial" >> "$CSV_OUT"
    echo "serial size=$size median_sec=$t_serial" | tee -a "$RUN_OUT"

    t_p1=""
    for p in "${THREADS[@]}"; do
        t_par=$(run_median "$PARALLEL_BIN" "$size" "$p" parallel)
        if [[ "$p" == "1" ]]; then
            t_p1=$t_par
        fi
        speedup_serial=$(awk -v ts="$t_serial" -v tp="$t_par" 'BEGIN { if (tp<=0) { print "nan"; exit } printf "%.9f", ts/tp }')
        eff_serial=$(awk -v s="$speedup_serial" -v p="$p" 'BEGIN { if (p<=0) { print "nan"; exit } printf "%.9f", s/p }')
        speedup_p1=""
        eff_p1=""
        if [[ -n "$t_p1" ]]; then
            speedup_p1=$(awk -v t1="$t_p1" -v tp="$t_par" 'BEGIN { if (tp<=0) { print "nan"; exit } printf "%.9f", t1/tp }')
            eff_p1=$(awk -v s="$speedup_p1" -v p="$p" 'BEGIN { if (p<=0) { print "nan"; exit } printf "%.9f", s/p }')
        fi
        printf '%s,parallel,%s,%s,%s,%s,%s,%s,%s,%s\n' \
            "$size" "$p" "$WARMUP" "$REPS" "$t_par" \
            "$speedup_serial" "$eff_serial" "$speedup_p1" "$eff_p1" >> "$CSV_OUT"
        echo "parallel size=$size threads=$p median_sec=$t_par S_serial=$speedup_serial E_serial=$eff_serial S_p1=$speedup_p1 E_p1=$eff_p1" | tee -a "$RUN_OUT"
    done
done

echo "Wrote $RUN_OUT"
echo "Wrote $CSV_OUT"
echo "S(p)=T(1)/T(p); E(p)=S(p)/p. T(1) for S_p1 is parallel threads=1. T_serial is the sequential binary."
