#!/bin/bash
#SBATCH -J matvec_ppx
#SBATCH -N 1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH -p ppx2
#SBATCH -w ppx2-00
#SBATCH -o out/matvec_%j.out
#SBATCH -e out/matvec_%j.err
#SBATCH -t 00:30:00

set -euo pipefail

# PPX 上で使う OpenMP の実行設定を読み込む。
module load openmpi

# 出力先を作る。
mkdir -p out

# 実行結果を CSV に残す。
RAWCSV="out/matvec_ppx_$(date +%Y%m%d_%H%M%S).csv"
echo "source,threads,repeat_index,elapsed_sec" > "$RAWCSV"

export OMP_PROC_BIND="${OMP_PROC_BIND:-close}"
export OMP_PLACES="${OMP_PLACES:-cores}"

# 1, 2, 4 スレッドで 2 種類の実装を順に実行する。
for threads in 1 2 4; do
	# 通常版。
	echo "Running matvec_serial with ${threads} threads"
	run_output=$(OMP_NUM_THREADS="$threads" ./bin/matvec_serial)
	printf '%s\n' "$run_output"
	elapsed_sec=$(printf '%s\n' "$run_output" | sed -n 's/.*Execution Time: \([0-9.][0-9.]*\) sec.*/\1/p' | head -n 1)
	if [[ -z "$elapsed_sec" ]]; then
		echo "Failed to parse execution time for matvec_serial threads=${threads}" >&2
		exit 1
	fi
	printf 'matvec_serial,%s,1,%s\n' "$threads" "$elapsed_sec" >> "$RAWCSV"

	# SIMD reduction 版。
	echo "Running matvec_simd_reduction with ${threads} threads"
	run_output=$(OMP_NUM_THREADS="$threads" ./bin/matvec_simd_reduction)
	printf '%s\n' "$run_output"
	elapsed_sec=$(printf '%s\n' "$run_output" | sed -n 's/.*Execution Time: \([0-9.][0-9.]*\) sec.*/\1/p' | head -n 1)
	if [[ -z "$elapsed_sec" ]]; then
		echo "Failed to parse execution time for matvec_simd_reduction threads=${threads}" >&2
		exit 1
	fi
	printf 'matvec_simd_reduction,%s,1,%s\n' "$threads" "$elapsed_sec" >> "$RAWCSV"
done

echo "Wrote $RAWCSV"
