# ==============================================================================
# コンパイル設定（共通フラグのみ変数化）
# ==============================================================================
CC = gcc
# 後から全ターゲットに共通して追加・変更したいフラグはここに書きます
COMMON_FLAGS = -O3 -Wall -Wextra -lm

# ==============================================================================
# ターゲット定義（make コマンドの入り口）
# ==============================================================================
.PHONY: all local ppx clean

# `make` または `make all` でローカル用・PPX用をすべてビルド
all: local ppx

# `make local` でローカル（Mac/OrbStack）向けをまとめてビルド
local: bin/matvec_original bin/matvec_loopswap bin/matvec_padding bin/matvec_loopswap_padding

# `make ppx` でPPX（計算ノード AMD Zen 2）向けをまとめてビルド
ppx: bin/matvec_original_ppx bin/matvec_loopswap_ppx bin/matvec_padding_ppx bin/matvec_loopswap_padding_ppx


# ==============================================================================
# 1. ローカル環境向け（Mac / OrbStack Ubuntu）のビルドコマンド
# ==============================================================================
bin/matvec_original: matvec_original.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) -march=native matvec_original.c -o bin/matvec_original

bin/matvec_loopswap: matvec_loopswap.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) -march=native matvec_loopswap.c -o bin/matvec_loopswap

bin/matvec_padding: matvec_padding.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) -march=native matvec_padding.c -o bin/matvec_padding

bin/matvec_loopswap_padding: matvec_loopswap_padding.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) -march=native matvec_loopswap_padding.c -o bin/matvec_loopswap_padding


# ==============================================================================
# 2. PPX環境向け（計算ノード AMD Zen 2）のビルドコマンド
# ==============================================================================
bin/matvec_original_ppx: matvec_original.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) -march=znver2 matvec_original.c -o bin/matvec_original_ppx

bin/matvec_loopswap_ppx: matvec_loopswap.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) -march=znver2 matvec_loopswap.c -o bin/matvec_loopswap_ppx

bin/matvec_padding_ppx: matvec_padding.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) -march=znver2 matvec_padding.c -o bin/matvec_padding_ppx

bin/matvec_loopswap_padding_ppx: matvec_loopswap_padding.c
	mkdir -p bin
	gcc $(COMMON_FLAGS) -march=znver2 matvec_loopswap_padding.c -o bin/matvec_loopswap_padding_ppx


# ==============================================================================
# クリーンアップ
# ==============================================================================
clean:
	rm -rf bin