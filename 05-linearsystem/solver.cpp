#include <iostream>
#include <vector>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <string>
#include <omp.h>

// CRS形式の行列を表現する構造体
struct CRSMatrix {
    int n;
    std::vector<double> val;
    std::vector<int> col_ind;
    std::vector<int> row_ptr;
};

// 内積を計算する関数 (OpenMPのReductionによる並列化)
double dot_product(const std::vector<double>& x, const std::vector<double>& y) {
    double sum = 0.0;
    int n = x.size();
    #pragma omp parallel for reduction(+:sum)
    for (int i = 0; i < n; ++i) {
        sum += x[i] * y[i];
    }
    return sum;
}

// CRS形式の行列とベクトルの積 (OpenMPによる並列化)
void matvec(const CRSMatrix& A, const std::vector<double>& x, std::vector<double>& y) {
    int n = A.n;
    #pragma omp parallel for
    for (int i = 0; i < n; ++i) {
        double sum = 0.0;
        for (int j = A.row_ptr[i]; j < A.row_ptr[i+1]; ++j) {
            sum += A.val[j] * x[A.col_ind[j]];
        }
        y[i] = sum;
    }
}

// 課題指定の行列 A を CRS形式で作成
CRSMatrix create_matrix_A(int n, double gamma) {
    CRSMatrix A;
    A.n = n; // 行列のサイズを設定
    A.row_ptr.assign(n + 1, 0); // `row_ptr`を初期化
    int nnz = 0; // 非ゼロ要素の数をカウントする変数
    
    for (int i = 0; i < n; ++i) {
        A.row_ptr[i] = nnz;
        if (i > 0) {
            A.val.push_back(gamma);
            A.col_ind.push_back(i - 1);
            ++nnz;
        }
        A.val.push_back(2.0);
        A.col_ind.push_back(i);
        ++nnz;
        if (i < n - 1) {
            A.val.push_back(1.0);
            A.col_ind.push_back(i + 1);
            ++nnz;
        }
    }
    A.row_ptr[n] = nnz;
    return A;
}

// BiCG法で使用する転置行列 A^T を CRS形式で作成
CRSMatrix create_matrix_AT(int n, double gamma) {
    CRSMatrix AT;
    AT.n = n;
    AT.row_ptr.assign(n + 1, 0);
    int nnz = 0;
    
    for (int i = 0; i < n; ++i) {
        AT.row_ptr[i] = nnz;
        if (i > 0) {
            AT.val.push_back(1.0);
            AT.col_ind.push_back(i - 1);
            ++nnz;
        }
        AT.val.push_back(2.0);
        AT.col_ind.push_back(i);
        ++nnz;
        if (i < n - 1) {
            AT.val.push_back(gamma);
            AT.col_ind.push_back(i + 1);
            ++nnz;
        }
    }
    AT.row_ptr[n] = nnz;
    return AT;
}

// BiCG法
std::vector<double> solve_BiCG(const CRSMatrix& A, const CRSMatrix& AT, const std::vector<double>& b, int max_iter, double eps) {
    int n = A.n;
    std::vector<double> x(n, 0.0);
    std::vector<double> r = b; 
    std::vector<double> r_star = r;
    std::vector<double> p = r;
    std::vector<double> p_star = r_star;
    std::vector<double> q(n, 0.0);
    std::vector<double> q_star(n, 0.0);
    
    double b_norm2 = dot_product(b, b);
    if (b_norm2 == 0.0) return {0.0};
    double b_norm = std::sqrt(b_norm2);
    
    std::vector<double> res_history;
    
    for (int k = 0; k < max_iter; ++k) {
        double r_norm = std::sqrt(dot_product(r, r));
        double rel_res = r_norm / b_norm;
        res_history.push_back(rel_res);
        
        if (rel_res <= eps) break;
        
        matvec(A, p, q);
        matvec(AT, p_star, q_star);
        
        double r_star_dot_r = dot_product(r_star, r);
        double p_star_dot_q = dot_product(p_star, q);
        double alpha = r_star_dot_r / p_star_dot_q;
        
        std::vector<double> r_next(n);
        std::vector<double> r_star_next(n);
        
        #pragma omp parallel for
        for (int i = 0; i < n; ++i) {
            x[i] += alpha * p[i];
            r_next[i] = r[i] - alpha * q[i];
            r_star_next[i] = r_star[i] - alpha * q_star[i];
        }
        
        double r_star_dot_r_next = dot_product(r_star_next, r_next);
        double beta = r_star_dot_r_next / r_star_dot_r;
        
        #pragma omp parallel for
        for (int i = 0; i < n; ++i) {
            p[i] = r_next[i] + beta * p[i];
            p_star[i] = r_star_next[i] + beta * p_star[i];
        }
        
        r = r_next;
        r_star = r_star_next;
    }
    return res_history;
}

// BiCGSTAB法
std::vector<double> solve_BiCGSTAB(const CRSMatrix& A, const std::vector<double>& b, int max_iter, double eps) {
    int n = A.n;
    std::vector<double> x(n, 0.0);
    std::vector<double> r = b; 
    std::vector<double> r_star_0 = r;
    std::vector<double> p = r;
    std::vector<double> q(n, 0.0);
    std::vector<double> t(n, 0.0);
    std::vector<double> s(n, 0.0);
    
    double b_norm2 = dot_product(b, b);
    if (b_norm2 == 0.0) return {0.0};
    double b_norm = std::sqrt(b_norm2);
    
    std::vector<double> res_history;
    
    for (int k = 0; k < max_iter; ++k) {
        double r_norm = std::sqrt(dot_product(r, r));
        double rel_res = r_norm / b_norm;
        res_history.push_back(rel_res);
        
        if (rel_res <= eps) break;
        
        matvec(A, p, q);
        
        double r_star_0_dot_r = dot_product(r_star_0, r);
        double r_star_0_dot_q = dot_product(r_star_0, q);
        double alpha = r_star_0_dot_r / r_star_0_dot_q;
        
        #pragma omp parallel for
        for (int i = 0; i < n; ++i) {
            t[i] = r[i] - alpha * q[i];
        }
        
        matvec(A, t, s);
        
        double s_dot_t = dot_product(s, t);
        double s_dot_s = dot_product(s, s);
        double zeta = s_dot_t / s_dot_s;
        
        std::vector<double> r_next(n);
        
        #pragma omp parallel for
        for (int i = 0; i < n; ++i) {
            x[i] += alpha * p[i] + zeta * t[i];
            r_next[i] = t[i] - zeta * s[i];
        }
        
        double r_star_0_dot_r_next = dot_product(r_star_0, r_next);
        double beta = (alpha / zeta) * (r_star_0_dot_r_next / r_star_0_dot_r);
        
        #pragma omp parallel for
        for (int i = 0; i < n; ++i) {
            p[i] = r_next[i] + beta * (p[i] - zeta * q[i]);
        }
        
        r = r_next;
    }
    return res_history;
}

int main() {
    int n = 50000; 
    std::vector<double> gammas = {0.1, 0.5, 0.9};
    int max_iter = 10000;
    double eps = 1e-12;
    
    // 現在の最大スレッド数を取得して表示
    int num_threads = omp_get_max_threads();
    std::cout << "====================================\n";
    std::cout << " Matrix Size (n) : " << n << "\n";
    std::cout << " OpenMP Threads  : " << num_threads << "\n";
    std::cout << "====================================\n\n";

    std::ofstream ofs("out/residuals.csv");
    ofs << "Iteration,Method,Gamma,RelativeResidual\n";
    
    std::vector<double> ones(n, 1.0); // 右辺ベクトルの準備用配列
    
    for (double gamma : gammas) {
        std::cout << "Solving for gamma = " << gamma << " ...\n";
        
        CRSMatrix A = create_matrix_A(n, gamma);
        CRSMatrix AT = create_matrix_AT(n, gamma);
        
        std::vector<double> b(n, 0.0);
        matvec(A, ones, b); // b = A * [1, 1, ..., 1]^T
        
        // --- BiCG法の時間計測 ---
        double start_time_bicg = omp_get_wtime();
        std::vector<double> res_BiCG = solve_BiCG(A, AT, b, max_iter, eps);
        double end_time_bicg = omp_get_wtime();
        double time_bicg = end_time_bicg - start_time_bicg;

        for (size_t i = 0; i < res_BiCG.size(); ++i) {
            ofs << i << ",BiCG," << gamma << "," << std::scientific << res_BiCG[i] << "\n";
        }
        
        // --- BiCGSTAB法の時間計測 ---
        double start_time_bicgstab = omp_get_wtime();
        std::vector<double> res_BiCGSTAB = solve_BiCGSTAB(A, b, max_iter, eps);
        double end_time_bicgstab = omp_get_wtime();
        double time_bicgstab = end_time_bicgstab - start_time_bicgstab;

        for (size_t i = 0; i < res_BiCGSTAB.size(); ++i) {
            ofs << i << ",BiCGSTAB," << gamma << "," << std::scientific << res_BiCGSTAB[i] << "\n";
        }
        
        std::cout << "  [BiCG]     Converged in " << res_BiCG.size() - 1 
                  << " iters. Time: " << std::fixed << std::setprecision(6) << time_bicg << " sec\n";
        std::cout << "  [BiCGSTAB] Converged in " << res_BiCGSTAB.size() - 1 
                  << " iters. Time: " << std::fixed << std::setprecision(6) << time_bicgstab << " sec\n\n";
    }
    
    ofs.close();
    std::cout << "Results written to out/residuals.csv\n";
    return 0;
}