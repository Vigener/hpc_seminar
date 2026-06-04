# ==============================================================================
# コンパイル設定（共通フラグのみ変数化）
# ==============================================================================
CC = gcc
# 後から全ターゲットに共通して追加・変更したいフラグはここに書きます
COMMON_FLAGS = -O3 -Wall -Wextra -lm

# ブロッキング検証用のターゲット一覧（変数で管理してスッキリさせる）
BLOCK_BINS = bin/matvec_blocking_1_8_8 \
             bin/matvec_blocking_4_4_4 \
             bin/matvec_blocking_8_8_8 \
             bin/matvec_blocking_16_16_16 \
             bin/matvec_blocking_32_32_32 \
			 bin/matvec_blocking_48_48_48 \
             bin/matvec_blocking_40_8_8 \
             bin/matvec_blocking_8_8_40 \
             bin/matvec_blocking_64_64_64 \
             bin/matvec_blocking_128_128_128

BLOCK_BINS_PPX = $(BLOCK_BINS:%=%_ppx)

# ==============================================================================
# ターゲット定義（make コマンドの入り口）
# ==============================================================================
.PHONY: all local ppx clean

# `make` または `make all` でローカル用・PPX用をすべてビルド
all: local ppx

# `make local` でローカル（Mac/OrbStack）向けをまとめてビルド
local: bin/matvec_original bin/matvec_loopswap bin/matvec_padding bin/matvec_loopswap_padding bin/matvec_loopswap_unroll $(BLOCK_BINS)

# `make ppx` でPPX（計算ノード AMD Zen 2）向けをまとめてビルド
ppx: bin/matvec_original_ppx bin/matvec_loopswap_ppx bin/matvec_padding_ppx bin/matvec_loopswap_padding_ppx bin/matvec_loopswap_unroll_ppx $(BLOCK_BINS_PPX)


# ==============================================================================
# 1. ローカル環境向け（Mac / OrbStack Ubuntu）のビルドコマンド
# ==============================================================================
bin/matvec_original: matvec_original.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) matvec_original.c -o bin/matvec_original

bin/matvec_loopswap: matvec_loopswap.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) matvec_loopswap.c -o bin/matvec_loopswap

bin/matvec_loopswap_unroll: matvec_loopswap_unroll.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) matvec_loopswap_unroll.c -o bin/matvec_loopswap_unroll

bin/matvec_padding: matvec_padding.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) matvec_padding.c -o bin/matvec_padding

bin/matvec_loopswap_padding: matvec_loopswap_padding.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) matvec_loopswap_padding.c -o bin/matvec_loopswap_padding

# ブロッキング検証用のパターンルール（% に 1_8_8 などが入る）
bin/matvec_blocking_%: matvec_blocking_%.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) $< -o $@


# ==============================================================================
# 2. PPX環境向け（計算ノード AMD Zen 2）のビルドコマンド
# ==============================================================================
bin/matvec_original_ppx: matvec_original.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) -march=znver2 matvec_original.c -o bin/matvec_original

bin/matvec_loopswap_ppx: matvec_loopswap.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) -march=znver2 matvec_loopswap.c -o bin/matvec_loopswap

bin/matvec_loopswap_unroll_ppx: matvec_loopswap_unroll.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) -march=znver2 matvec_loopswap_unroll.c -o bin/matvec_loopswap_unroll

bin/matvec_padding_ppx: matvec_padding.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) -march=znver2 matvec_padding.c -o bin/matvec_padding

bin/matvec_loopswap_padding_ppx: matvec_loopswap_padding.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) -march=znver2 matvec_loopswap_padding.c -o bin/matvec_loopswap_padding

# ブロッキング検証用のパターンルール（PPX用）
# 実行ファイル名は bin/matvec_blocking_XXX のまま生成する（元の仕様を維持）
bin/matvec_blocking_%_ppx: matvec_blocking_%.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) -march=znver2 $< -o bin/matvec_blocking_$*


# ==============================================================================
# クリーンアップ
# ==============================================================================
clean:
	rm -rf bin