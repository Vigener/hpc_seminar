.PHONY: build release debug clean benchmark-ppx run-profile

PYTHON ?= python3
CC := mpicc

CFLAGS_BASE := -Wall
CFLAGS_DEBUG := $(CFLAGS_BASE) -g -O0
CFLAGS_RELEASE := $(CFLAGS_BASE) -O3

# 数学ライブラリ(-lm)とtlogライブラリ(-ltlog)のリンクフラグ
LDFLAGS := -lm -ltlog

# PPX 環境向けの問題サイズと反復回数
PPX_XSIZE ?= 4480
PPX_NITER ?= 1000
PPX_DEFINE_FLAGS = -DXSIZE=$(PPX_XSIZE) -DYSIZE=$(PPX_XSIZE) -DNITER=$(PPX_NITER)

# --- ビルドターゲット ---
build: release

release: CFLAGS := $(CFLAGS_RELEASE)
release: laplace_basic1 laplace_basic1_temporal

debug: CFLAGS := $(CFLAGS_DEBUG)
debug: laplace_basic1 laplace_basic1_temporal

laplace_basic1: laplace_basic1.c
	@mkdir -p bin
	@$(CC) $(CFLAGS) $(PPX_DEFINE_FLAGS) -o bin/laplace_basic1 laplace_basic1.c $(LDFLAGS)

laplace_basic1_temporal: laplace_basic1_temporal.c
	@mkdir -p bin
	@$(CC) $(CFLAGS) $(PPX_DEFINE_FLAGS) -o bin/laplace_basic1_temporal laplace_basic1_temporal.c $(LDFLAGS)

# --- クリーン ---
clean:
	rm -f bin/laplace_basic1 bin/laplace_basic1_temporal
	rm -f out/trace*.log

# PPX 実行用のジョブを投入する
benchmark-ppx:
	@sbatch run.sh

# --- 実行ターゲット (ローカルでのプロファイル実行用) ---
run-profile: release
	@bash run.sh

plot:
	uv run scripts/plot_temporal_blocking.py \
    --input out/laplace_opt_raw_latest.csv \
    --summary-output results/temporal_summary.csv \
    --figure-output results/temporal_time.png
