#!/usr/bin/env python3
"""
BiCG法とBiCGSTAB法の相対残差の比較分析スクリプト
複数のパラメータgammaについて実験結果を分析し、グラフ化・考察を行う
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from pathlib import Path

# 日本語フォント表示支援 (コンテナに japanize-matplotlib があれば自動で適用)
try:
    import japanize_matplotlib  # type: ignore
except Exception:
    pass

# 出力ディレクトリの設定
output_dir = Path("../out")
csv_file = output_dir / "residuals.csv"
plot_dir = Path("./plots")
plot_dir.mkdir(exist_ok=True)

# フォント設定（日本語対応）
plt.rcParams['font.size'] = 11
plt.rcParams['figure.figsize'] = (14, 10)

def load_residuals(csv_path):
    """CSVファイルから相対残差データを読み込む"""
    if not csv_path.exists():
        print(f"エラー: {csv_path} が見つかりません")
        print("先に solver を実行してください: cd .. && make clean && make && ./bin/solver")
        return None
    
    df = pd.read_csv(csv_path)
    return df

def plot_comparison_by_gamma(df):
    """gammaごとにBiCGとBiCGSTABを比較するグラフを作成"""
    gammas = sorted(df['Gamma'].unique())
    methods = df['Method'].unique()
    
    fig, axes = plt.subplots(1, len(gammas), figsize=(16, 5))
    if len(gammas) == 1:
        axes = [axes]
    
    for idx, gamma in enumerate(gammas):
        ax = axes[idx]
        df_gamma = df[df['Gamma'] == gamma]
        
        for method in methods:
            df_method = df_gamma[df_gamma['Method'] == method]
            iterations = df_method['Iteration'].values
            residuals = df_method['RelativeResidual'].values
            
            ax.semilogy(iterations, residuals, marker='o', markersize=3, 
                       label=method, linewidth=1.5, alpha=0.8)
        
        ax.set_xlabel('反復回数')
        ax.set_ylabel('相対残差 $||r_k||_2 / ||b||_2$')
        ax.set_title(f'γ = {gamma}')
        ax.grid(True, alpha=0.3)
        ax.legend()
    
    plt.tight_layout()
    plt.savefig(plot_dir / "comparison_by_gamma.png", dpi=150, bbox_inches='tight')
    print("✓ グラフ保存: comparison_by_gamma.png")
    plt.close()

def plot_gamma_effect(df):
    """各メソッドについて、gammaの影響を比較するグラフを作成"""
    methods = sorted(df['Method'].unique())
    gammas = sorted(df['Gamma'].unique())
    
    fig, axes = plt.subplots(1, len(methods), figsize=(14, 5))
    if len(methods) == 1:
        axes = [axes]
    
    for idx, method in enumerate(methods):
        ax = axes[idx]
        df_method = df[df['Method'] == method]
        
        for gamma in gammas:
            df_gamma = df_method[df_method['Gamma'] == gamma]
            iterations = df_gamma['Iteration'].values
            residuals = df_gamma['RelativeResidual'].values
            
            ax.semilogy(iterations, residuals, marker='s', markersize=3,
                       label=f'γ = {gamma}', linewidth=1.5, alpha=0.8)
        
        ax.set_xlabel('反復回数')
        ax.set_ylabel('相対残差 $||r_k||_2 / ||b||_2$')
        ax.set_title(f'{method}法')
        ax.grid(True, alpha=0.3)
        ax.legend()
    
    plt.tight_layout()
    plt.savefig(plot_dir / "gamma_effect.png", dpi=150, bbox_inches='tight')
    print("✓ グラフ保存: gamma_effect.png")
    plt.close()

def plot_convergence_rates(df):
    """収束速度の比較グラフを作成"""
    gammas = sorted(df['Gamma'].unique())
    methods = sorted(df['Method'].unique())
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x_pos = np.arange(len(gammas))
    width = 0.35
    
    # 各メソッドについて収束に要した反復回数を取得
    convergence_iters = {}
    for method in methods:
        iters = []
        for gamma in gammas:
            df_filter = df[(df['Method'] == method) & (df['Gamma'] == gamma)]
            if len(df_filter) > 0:
                # 相対残差が1e-12以下になった時点を収束と判定
                converged = df_filter[df_filter['RelativeResidual'] <= 1e-12]
                if len(converged) > 0:
                    iter_count = converged['Iteration'].min()
                else:
                    iter_count = df_filter['Iteration'].max()
                iters.append(iter_count)
            else:
                iters.append(np.nan)
        convergence_iters[method] = iters
    
    # グラフを描画
    for idx, method in enumerate(methods):
        offset = width * (idx - (len(methods) - 1) / 2)
        ax.bar(x_pos + offset, convergence_iters[method], width, 
               label=method, alpha=0.8)
    
    ax.set_xlabel('パラメータ γ')
    ax.set_ylabel('収束に要した反復回数')
    ax.set_title('収束速度の比較')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f'{g}' for g in gammas])
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(plot_dir / "convergence_rates.png", dpi=150, bbox_inches='tight')
    print("✓ グラフ保存: convergence_rates.png")
    plt.close()

def generate_analysis_report(df):
    """分析レポートを生成"""
    report = []
    report.append("=" * 80)
    report.append("BiCG法とBiCGSTAB法の相対残差分析レポート")
    report.append("=" * 80)
    report.append("")
    
    # 基本情報
    report.append("【実験条件】")
    report.append(f"  - 行列サイズ: n = 50,000")
    report.append(f"  - パラメータγ: {sorted(df['Gamma'].unique())}")
    report.append(f"  - 最大反復回数: 10,000")
    report.append(f"  - 収束判定値 (eps): 1e-12")
    report.append("")
    
    # 各パラメータについての分析
    report.append("【各パラメータγでの性能比較】")
    report.append("")
    
    gammas = sorted(df['Gamma'].unique())
    methods = sorted(df['Method'].unique())
    
    for gamma in gammas:
        report.append(f"━━━ γ = {gamma} ━━━")
        df_gamma = df[df['Gamma'] == gamma]
        
        for method in methods:
            df_method = df_gamma[df_gamma['Method'] == method]
            if len(df_method) == 0:
                continue
            
            # 収束情報
            converged_rows = df_method[df_method['RelativeResidual'] <= 1e-12]
            if len(converged_rows) > 0:
                iter_to_converge = converged_rows['Iteration'].min()
                status = "✓ 収束"
            else:
                iter_to_converge = df_method['Iteration'].max()
                final_residual = df_method['RelativeResidual'].iloc[-1]
                status = f"✗ 未収束 (最終残差: {final_residual:.2e})"
            
            # 最初と最後の反復での収束率を計算
            first_residual = df_method['RelativeResidual'].iloc[0]
            last_residual = df_method['RelativeResidual'].iloc[-1]
            reduction_ratio = first_residual / (last_residual + 1e-20)
            
            report.append(f"  {method}法:")
            report.append(f"    - 収束反復: {iter_to_converge} ({status})")
            report.append(f"    - 初期残差: {first_residual:.2e}")
            report.append(f"    - 最終残差: {last_residual:.2e}")
            report.append(f"    - 残差削減率: {reduction_ratio:.2e}")
        
        report.append("")
    
    # 全体的な考察
    report.append("【全体的な考察】")
    report.append("")
    
    # 各メソッドの平均収束反復数を計算
    report.append("1. 方法の比較:")
    for method in methods:
        df_method = df[df['Method'] == method]
        avg_iters = []
        for gamma in gammas:
            df_filter = df_method[df_method['Gamma'] == gamma]
            converged = df_filter[df_filter['RelativeResidual'] <= 1e-12]
            if len(converged) > 0:
                avg_iters.append(converged['Iteration'].min())
        
        if avg_iters:
            avg = np.mean(avg_iters)
            report.append(f"   • {method}法: 平均収束反復 {avg:.1f}")
    
    report.append("")
    report.append("2. パラメータγの影響:")
    report.append("   • γが大きいほど行列の非対角要素が大きくなり、条件数が増加")
    report.append("   • 一般にγが大きいと収束に多くの反復が必要になる傾向")
    report.append("   • BiCGSTAB法はBiCG法よりも安定性が高く、収束が速い場合が多い")
    report.append("")
    
    report.append("3. 計算安定性:")
    report.append("   • BiCG法: 転置行列を使用し、理論的には安定だが実装上の数値誤差に影響を受けやすい")
    report.append("   • BiCGSTAB法: 安定化技法(STAB)により、数値的に更に安定")
    report.append("")
    
    report.append("【推奨事項】")
    report.append("• 実務では、数値安定性の観点からBiCGSTAB法の使用を推奨")
    report.append("• 前処理（preconditioner）を導入することで、収束を大幅に高速化可能")
    report.append("• 並列化の効果を最大限に活かすために、行列ベクトル積の最適化が重要")
    report.append("")
    report.append("=" * 80)
    
    return "\n".join(report)

def main():
    print("相対残差分析スクリプトを開始します...")
    print("")
    
    # CSVを読み込む
    df = load_residuals(csv_file)
    if df is None:
        return
    
    print(f"✓ {csv_file} を読み込みました")
    print(f"  - データ件数: {len(df)}")
    print(f"  - パラメータγ: {sorted(df['Gamma'].unique())}")
    print(f"  - メソッド: {sorted(df['Method'].unique())}")
    print("")
    
    # グラフの作成
    print("グラフを生成中...")
    plot_comparison_by_gamma(df)
    plot_gamma_effect(df)
    plot_convergence_rates(df)
    print("")
    
    # 分析レポート
    report = generate_analysis_report(df)
    print(report)
    
    # レポートをファイルに保存
    report_file = plot_dir / "analysis_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✓ 分析レポートを保存: {report_file}")

if __name__ == "__main__":
    main()
