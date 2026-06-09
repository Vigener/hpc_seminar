# ==============================================================================
# コンパイル設定（共通フラグのみ変数化）
# ==============================================================================
CC = gcc
COMMON_FLAGS = -O3 -Wall -Wextra -lm

# ★変更: 自前ビルドした純度100%の libopenblas.a を指定する
BLAS_FLAGS = -I$(HOME)/work/apps/local/include \
             $(HOME)/work/apps/local/lib/libopenblas.a \
             -lm

# ------------------------------------------------------------------------------
# 評価対象の手法・サイズの定義
# ------------------------------------------------------------------------------
# dgemm を追加
BASE_NAMES  = original loopswap padding loopswap_padding loopswap_unroll
# 非対称サイズ (32_128_16, 32_96_32, 16_256_8) を追加
BLOCK_SIZES = 1_8_8 4_4_4 8_8_8 16_16_16 32_32_32 48_48_48 40_8_8 8_8_40 64_64_64 128_128_128 32_128_16 32_96_32 16_256_8

# --- N=1000 用のターゲット一覧自動生成 ---
BASE_N1000  = $(addprefix bin/matvec_, $(addsuffix _n1000, $(BASE_NAMES)))
BLOCK_N1000 = $(addprefix bin/matvec_blocking_, $(addsuffix _n1000, $(BLOCK_SIZES)))
LOOPBLOCK_N1000 = $(addprefix bin/matvec_loopswap_blocking_, $(addsuffix _n1000, $(BLOCK_SIZES)))
PPX_BASE_N1000  = $(BASE_N1000:%=%_ppx)
PPX_BLOCK_N1000 = $(BLOCK_N1000:%=%_ppx)
PPX_LOOPBLOCK_N1000 = $(LOOPBLOCK_N1000:%=%_ppx)

# --- N=2000 用のターゲット一覧自動生成 ---
BASE_N2000  = $(addprefix bin/matvec_, $(addsuffix _n2000, $(BASE_NAMES)))
BLOCK_N2000 = $(addprefix bin/matvec_blocking_, $(addsuffix _n2000, $(BLOCK_SIZES)))
LOOPBLOCK_N2000 = $(addprefix bin/matvec_loopswap_blocking_, $(addsuffix _n2000, $(BLOCK_SIZES)))
PPX_BASE_N2000  = $(BASE_N2000:%=%_ppx)
PPX_BLOCK_N2000 = $(BLOCK_N2000:%=%_ppx)
PPX_LOOPBLOCK_N2000 = $(LOOPBLOCK_N2000:%=%_ppx)

# ==============================================================================
# ターゲット定義（make コマンドの入り口）
# ==============================================================================
.PHONY: all local_n1000 local_n2000 ppx_n1000 ppx_n2000 clean plot

# 全ての組み合わせを一括ビルドする場合
all: local ppx

# 大元ターゲット（local と ppx）を定義
local: local_n1000 local_n2000
ppx: ppx_n1000 ppx_n2000

# 各大元ターゲットごとに細分化
local_n1000: $(BASE_N1000) $(BLOCK_N1000) $(LOOPBLOCK_N1000)
local_n2000: $(BASE_N2000) $(BLOCK_N2000) $(LOOPBLOCK_N2000)
ppx_n1000:   $(PPX_BASE_N1000) $(PPX_BLOCK_N1000) $(PPX_LOOPBLOCK_N1000)
ppx_n2000:   $(PPX_BASE_N2000) $(PPX_BLOCK_N2000) $(PPX_LOOPBLOCK_N2000)


# ==============================================================================
# ビルド物理ルール（パターンルールによる全自動マッピング）
# ==============================================================================

# --- DGEMM専用ルール (BLAS_FLAGSを結合) ---
bin/matvec_dgemm_n1000: matvec_dgemm.c
	mkdir -p bin
	$(CC) $(COMMON_FLAGS) -DN=1000 $< -o $@ $(BLAS_FLAGS)

bin/matvec_dgemm_n2000: matvec_dgemm.c
	mkdir -p bin
	$(CC) $(COMMON_FLAGS) -DN=2000 $< -o $@ $(BLAS_FLAGS)

bin/matvec_dgemm_n1000_ppx: matvec_dgemm.c
	mkdir -p bin
	$(CC) $(COMMON_FLAGS) -march=znver2 -DN=1000 $< -o $@ $(BLAS_FLAGS)

bin/matvec_dgemm_n2000_ppx: matvec_dgemm.c
	mkdir -p bin
	$(CC) $(COMMON_FLAGS) -march=znver2 -DN=2000 $< -o $@ $(BLAS_FLAGS)

# --- 1. local_n1000 (汎用最適化, N=1000) ---
bin/matvec_%_n1000: matvec_%.c
	mkdir -p bin
	$(CC) $(COMMON_FLAGS) -DN=1000 $< -o $@

bin/matvec_blocking_%_n1000: matvec_blocking.c
	mkdir -p bin
	$(CC) $(COMMON_FLAGS) -DN=1000 \
		-DB_I=$(word 1,$(subst _, ,$*)) \
		-DB_J=$(word 2,$(subst _, ,$*)) \
		-DB_K=$(word 3,$(subst _, ,$*)) \
		$< -o $@

bin/matvec_loopswap_blocking_%_n1000: matvec_loopswap_blocking.c
	mkdir -p bin
	$(CC) $(COMMON_FLAGS) -DN=1000 \
		-DB_I=$(word 1,$(subst _, ,$*)) -DB_J=$(word 2,$(subst _, ,$*)) -DB_K=$(word 3,$(subst _, ,$*)) \
		$< -o $@

# --- 2. local_n2000 (汎用最適化, N=2000) ---
bin/matvec_%_n2000: matvec_%.c
	mkdir -p bin
	$(CC) $(COMMON_FLAGS) -DN=2000 $< -o $@

bin/matvec_blocking_%_n2000: matvec_blocking.c
	mkdir -p bin
	$(CC) $(COMMON_FLAGS) -DN=2000 \
		-DB_I=$(word 1,$(subst _, ,$*)) \
		-DB_J=$(word 2,$(subst _, ,$*)) \
		-DB_K=$(word 3,$(subst _, ,$*)) \
		$< -o $@

bin/matvec_loopswap_blocking_%_n2000: matvec_loopswap_blocking.c
	mkdir -p bin
	$(CC) $(COMMON_FLAGS) -DN=2000 \
		-DB_I=$(word 1,$(subst _, ,$*)) -DB_J=$(word 2,$(subst _, ,$*)) -DB_K=$(word 3,$(subst _, ,$*)) \
		$< -o $@

# --- 3. ppx_n1000 (AMD Zen 2 特化, N=1000) ---
bin/matvec_%_n1000_ppx: matvec_%.c
	mkdir -p bin
	$(CC) $(COMMON_FLAGS) -march=znver2 -DN=1000 $< -o $@

bin/matvec_blocking_%_n1000_ppx: matvec_blocking.c
	mkdir -p bin
	$(CC) $(COMMON_FLAGS) -march=znver2 -DN=1000 \
		-DB_I=$(word 1,$(subst _, ,$*)) \
		-DB_J=$(word 2,$(subst _, ,$*)) \
		-DB_K=$(word 3,$(subst _, ,$*)) \
		$< -o $@

bin/matvec_loopswap_blocking_%_n1000_ppx: matvec_loopswap_blocking.c
	mkdir -p bin
	$(CC) $(COMMON_FLAGS) -march=znver2 -DN=1000 \
		-DB_I=$(word 1,$(subst _, ,$*)) -DB_J=$(word 2,$(subst _, ,$*)) -DB_K=$(word 3,$(subst _, ,$*)) \
		$< -o $@

# --- 4. ppx_n2000 (AMD Zen 2 特化, N=2000) ---
bin/matvec_%_n2000_ppx: matvec_%.c
	mkdir -p bin
	$(CC) $(COMMON_FLAGS) -march=znver2 -DN=2000 $< -o $@

bin/matvec_blocking_%_n2000_ppx: matvec_blocking.c
	mkdir -p bin
	$(CC) $(COMMON_FLAGS) -march=znver2 -DN=2000 \
		-DB_I=$(word 1,$(subst _, ,$*)) \
		-DB_J=$(word 2,$(subst _, ,$*)) \
		-DB_K=$(word 3,$(subst _, ,$*)) \
		$< -o $@

bin/matvec_loopswap_blocking_%_n2000_ppx: matvec_loopswap_blocking.c
	mkdir -p bin
	$(CC) $(COMMON_FLAGS) -march=znver2 -DN=2000 \
		-DB_I=$(word 1,$(subst _, ,$*)) -DB_J=$(word 2,$(subst _, ,$*)) -DB_K=$(word 3,$(subst _, ,$*)) \
		$< -o $@

# ==============================================================================
# Pythonグラフ描画
# ==============================================================================
plot:
	python scripts/plot_graph.py out/results_n2000_latest.csv out/

# ==============================================================================
# クリーンアップ
# ==============================================================================
clean:
	rm -rf bin
