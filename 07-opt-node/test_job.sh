#!/bin/bash
#SBATCH -J test_dgemm
#SBATCH -N 1
#SBATCH -p ppx2
#SBATCH -w ppx2-00
#SBATCH -o test_dgemm_%j.out
#SBATCH -e test_dgemm_%j.err
#SBATCH -t 00:05:00

# set -u は維持しますが、変数の展開方法を工夫します
set -euo pipefail

echo "========================================"
echo " 1. ライブラリパスの手動設定"
echo "========================================"

# ${LD_LIBRARY_PATH:-} という記述により、変数が未定義なら空文字として扱います
export LD_LIBRARY_PATH=/opt/nvidia/hpc_sdk/Linux_x86_64/26.3/compilers/lib:${LD_LIBRARY_PATH:-}

echo "LD_LIBRARY_PATH = $LD_LIBRARY_PATH"

echo "========================================"
echo " 2. 計算ノードでのコンパイル"
echo "========================================"
gcc -O3 test_dgemm.c -o test_dgemm_bin \
    -I/opt/nvidia/hpc_sdk/Linux_x86_64/26.3/compilers/include \
    -L/opt/nvidia/hpc_sdk/Linux_x86_64/26.3/compilers/lib \
    -Wl,-rpath,/opt/nvidia/hpc_sdk/Linux_x86_64/26.3/compilers/lib \
    -lblas

echo "コンパイル完了"

echo "========================================"
echo " 3. 共有ライブラリのリンク診断 (ldd)"
echo "========================================"
# ldd は「実行時に必要なライブラリが見つかっているか」を診断する神コマンドです
ldd ./test_dgemm_bin

echo "========================================"
echo " 4. バイナリの実行"
echo "========================================"
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1

./test_dgemm_bin

echo "========================================"
echo " 全プロセス完了"
echo "========================================"
