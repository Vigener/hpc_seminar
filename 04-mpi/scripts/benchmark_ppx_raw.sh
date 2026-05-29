#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
PROJECT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)

PROCS="1 2 4 8 16"
REPEATS=10
OUTPUT=""
ON_ERROR="stop"  # stop | continue
BIND_CORE=1

usage() {
    cat <<'EOF'
Usage: benchmark_ppx_raw.sh [options]

Options:
  --procs "1 2 4 8 16"   Space separated MPI process counts (default: "1 2 4 8 16")
  --repeats N             Number of runs per (source, np) pair (default: 10)
  --output PATH           Output raw CSV path (default: results/laplace_ppx_raw_<timestamp>.csv)
  --on-error MODE         stop or continue (default: stop)
  --no-bind-core          Disable --bind-to core --map-by core
  -h, --help              Show this help
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --procs)
            PROCS=${2:-}
            shift 2
            ;;
        --repeats)
            REPEATS=${2:-}
            shift 2
            ;;
        --output)
            OUTPUT=${2:-}
            shift 2
            ;;
        --on-error)
            ON_ERROR=${2:-}
            shift 2
            ;;
        --no-bind-core)
            BIND_CORE=0
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

if [[ "$ON_ERROR" != "stop" && "$ON_ERROR" != "continue" ]]; then
    echo "--on-error must be 'stop' or 'continue'" >&2
    exit 1
fi

if ! [[ "$REPEATS" =~ ^[0-9]+$ ]] || [[ "$REPEATS" -lt 1 ]]; then
    echo "--repeats must be a positive integer" >&2
    exit 1
fi

if ! command -v mpirun >/dev/null 2>&1; then
    echo "mpirun not found in PATH" >&2
    exit 1
fi

if [[ -z "$OUTPUT" ]]; then
    ts=$(date +%Y%m%d_%H%M%S)
    OUTPUT="$PROJECT_DIR/results/laplace_ppx_raw_${ts}.csv"
fi

mkdir -p "$(dirname "$OUTPUT")"
LOG_FILE="$(dirname "$OUTPUT")/$(basename "${OUTPUT%.csv}")_errors.log"

SOURCES=(laplace laplace_basic1 laplace_basic2 laplace_advanced)
for src in "${SOURCES[@]}"; do
    if [[ ! -x "$PROJECT_DIR/bin/$src" ]]; then
        echo "Binary not found or not executable: $PROJECT_DIR/bin/$src" >&2
        echo "Run: make -C $PROJECT_DIR release" >&2
        exit 1
    fi
done

echo "timestamp,source,nprocs,repeat_index,elapsed_sec,status" > "$OUTPUT"
echo "[INFO] writing raw CSV to $OUTPUT" >&2
echo "[INFO] error log: $LOG_FILE" >&2

for src in "${SOURCES[@]}"; do
    bin="$PROJECT_DIR/bin/$src"
    for np in $PROCS; do
        for rep in $(seq 1 "$REPEATS"); do
            timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

            cmd=(mpirun)
            if [[ "$BIND_CORE" -eq 1 ]]; then
                cmd+=(--bind-to core --map-by core)
            fi
            cmd+=(-np "$np" "$bin")

            set +e
            stdout="$(${cmd[@]} 2>>"$LOG_FILE")"
            rc=$?
            set -e

            if [[ "$rc" -ne 0 ]]; then
                echo "$timestamp,$src,$np,$rep,,error" >> "$OUTPUT"
                echo "[ERROR] source=$src np=$np repeat=$rep exit=$rc" >&2
                if [[ "$ON_ERROR" == "stop" ]]; then
                    echo "[ERROR] stopped due to --on-error=stop" >&2
                    exit "$rc"
                fi
                continue
            fi

            elapsed=$(printf '%s\n' "$stdout" | awk -F'=' '/^time[[:space:]]*=/{gsub(/[[:space:]]/,"",$2); print $2; exit}')
            if [[ -z "$elapsed" ]]; then
                echo "$timestamp,$src,$np,$rep,,error" >> "$OUTPUT"
                echo "[ERROR] source=$src np=$np repeat=$rep: could not parse time" >&2
                if [[ "$ON_ERROR" == "stop" ]]; then
                    exit 2
                fi
                continue
            fi

            echo "$timestamp,$src,$np,$rep,$elapsed,ok" >> "$OUTPUT"
            echo "[OK] source=$src np=$np repeat=$rep time=${elapsed}s" >&2
        done
    done
done

echo "[DONE] raw CSV: $OUTPUT" >&2
