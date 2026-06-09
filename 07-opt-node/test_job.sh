#!/bin/bash
#SBATCH -J test_dgemm
#SBATCH -N 1
#SBATCH -p ppx2
#SBATCH -w ppx2-00
#SBATCH -o test_dgemm_%j.out
#SBATCH -e test_dgemm_%j.err
#SBATCH -t 00:05:00

set -euo pipefail

# パスを環境に合わせて再定義
export LD_LIBRARY_PATH=/opt/nvidia/hpc_sdk/Linux_x86_64/26.3/compilers/lib:${LD_LIBRARY_PATH:-}
HEADER_PATH=/opt/nvidia/hpc_sdk/Linux_x86_64/26.3/compilers/include
LIB_PATH=/opt/nvidia/hpc_sdk/Linux_x86_64/26.3/compilers/lib

echo "--- Check if header exists ---"
ls -l "$HEADER_PATH/cblas.h" || echo "Header not found at $HEADER_PATH"

echo "=== LD_LIBRARY_PATH ===" && echo $LD_LIBRARY_PATH
echo "=== ライブラリの存在確認 ===" && ls /opt/nvidia/hpc_sdk/Linux_x86_64/26.3/compilers/lib/libblas* 2>&1
ldd ./bin/test_dgemm 2>&1   # どのライブラリが未解決か確認

echo "--- Compiling with Verbose mode ---"
# -v をつけて、コンパイラがどこを探しているかを確認
gcc -v -O3 test_dgemm.c -o test_dgemm_bin \
    -I"$HEADER_PATH" \
    -L"$LIB_PATH" \
    -Wl,-rpath,"$LIB_PATH" \
    -lblas

echo "--- Execution ---"
./test_dgemm_bin
