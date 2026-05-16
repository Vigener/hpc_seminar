# コンパイル
gcc -O3 -fopenmp matvec.c -o matvec
gcc -O3 -fopenmp matvec_8192.c -o matvec_8192

# スレッド数を指定して実行
echo "1"
OMP_NUM_THREADS=1 ./matvec
echo "2"
OMP_NUM_THREADS=2 ./matvec
echo "4"
OMP_NUM_THREADS=4 ./matvec
echo "M=N=8192"
echo "1"
OMP_NUM_THREADS=1 ./matvec_8192
echo "2"
OMP_NUM_THREADS=2 ./matvec_8192
echo "4"
OMP_NUM_THREADS=4 ./matvec_8192
