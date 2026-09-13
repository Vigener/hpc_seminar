#!/usr/bin/env python3
"""
BiCG / BiCGSTAB residual analysis.
Overlay residual curves per method (log y) and a bar chart of iterations vs gamma.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# 日本語フォント表示支援 (コンテナに japanize-matplotlib があれば自動で適用)
try:
    import japanize_matplotlib  # type: ignore
except Exception:
    pass

output_dir = Path("../out")
csv_file = output_dir / "residuals.csv"
summary_file = output_dir / "summary.csv"
plot_dir = Path("./plots")
plot_dir.mkdir(exist_ok=True)

plt.rcParams['font.size'] = 11


def load_csv(csv_path):
    if not csv_path.exists():
        return None
    return pd.read_csv(csv_path)


def plot_residual_overlay(df):
    """One panel per method; overlay 9 gamma curves on a log-y residual plot."""
    methods = sorted(df['Method'].unique())
    gammas = sorted(df['Gamma'].unique())
    cmap = plt.cm.viridis
    colors = {g: cmap(i / max(len(gammas) - 1, 1)) for i, g in enumerate(gammas)}

    fig, axes = plt.subplots(1, len(methods), figsize=(14, 5), sharey=True)
    if len(methods) == 1:
        axes = [axes]

    for ax, method in zip(axes, methods):
        df_method = df[df['Method'] == method]
        for gamma in gammas:
            df_gamma = df_method[df_method['Gamma'] == gamma]
            ax.semilogy(
                df_gamma['Iteration'].values,
                df_gamma['RelativeResidual'].values,
                color=colors[gamma],
                label=f'γ = {gamma:.1f}',
                linewidth=1.4,
                alpha=0.9,
            )
        ax.set_xlabel('Iteration')
        ax.set_ylabel(r'Relative residual $||r||_2 / ||b||_2$')
        ax.set_title(method)
        ax.grid(True, which='both', alpha=0.3)
        ax.legend(fontsize=8, ncol=1, loc='best')

    fig.suptitle('Relative residual history (log scale)', y=1.02)
    plt.tight_layout()
    out = plot_dir / "residuals_overlay.png"
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {out}")


def _iters_from_residuals(df):
    gammas = sorted(df['Gamma'].unique())
    methods = sorted(df['Method'].unique())
    rows = []
    for method in methods:
        for gamma in gammas:
            sub = df[(df['Method'] == method) & (df['Gamma'] == gamma)]
            if len(sub) == 0:
                continue
            converged = sub[sub['RelativeResidual'] <= 1e-12]
            if len(converged) > 0:
                iters = int(converged['Iteration'].min())
            else:
                iters = int(sub['Iteration'].max())
            rows.append({'method': method, 'gamma': gamma, 'iterations': iters})
    return pd.DataFrame(rows)


def plot_iterations_bar(df_res, df_sum):
    """Grouped bar chart: iterations vs gamma for both methods."""
    if df_sum is not None and {'gamma', 'method', 'iterations'}.issubset(df_sum.columns):
        src = df_sum.rename(columns={'gamma': 'gamma', 'method': 'method'})
        print("Iteration counts taken from summary.csv (last residual index = size-1).")
    else:
        src = _iters_from_residuals(df_res)
        print("Iteration counts inferred from residuals.csv (first index with rel_res <= 1e-12).")

    methods = sorted(src['method'].unique())
    gammas = sorted(src['gamma'].unique())
    x_pos = np.arange(len(gammas))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    for idx, method in enumerate(methods):
        vals = []
        for g in gammas:
            hit = src[(src['method'] == method) & (np.isclose(src['gamma'], g))]
            vals.append(float(hit['iterations'].iloc[0]) if len(hit) else np.nan)
        offset = width * (idx - (len(methods) - 1) / 2.0)
        ax.bar(x_pos + offset, vals, width, label=method, alpha=0.85)

    ax.set_xlabel('gamma')
    ax.set_ylabel('Iterations to convergence')
    ax.set_title('Iterations vs gamma')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f'{g:.1f}' for g in gammas])
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    out = plot_dir / "iterations_vs_gamma.png"
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {out}")


def print_and_save_summary(df_sum):
    cols = ['gamma', 'method', 'iterations', 'final_rel_res',
            'l2_err_to_ones', 'inf_err_to_ones', 'time_sec']
    table = df_sum[cols].copy() if all(c in df_sum.columns for c in cols) else df_sum.copy()
    text = table.to_string(index=False)
    print("")
    print("=" * 80)
    print("Summary (from ../out/summary.csv)")
    print("iterations = last residual index (history size - 1)")
    print("=" * 80)
    print(text)
    print("=" * 80)
    out = plot_dir / "summary_table.txt"
    with open(out, 'w', encoding='utf-8') as f:
        f.write("iterations = last residual index (history size - 1)\n")
        f.write(text + "\n")
    print(f"Saved: {out}")


def main():
    print("Loading residual history from ../out/residuals.csv ...")
    df = load_csv(csv_file)
    if df is None:
        print(f"Error: {csv_file} not found")
        print("Run the solver first: cd .. && make clean && make run")
        return

    print(f"  rows={len(df)}  gamma={sorted(df['Gamma'].unique())}  methods={sorted(df['Method'].unique())}")

    df_sum = load_csv(summary_file)
    if df_sum is None:
        print(f"Note: {summary_file} not found; bar chart will use residuals.csv")

    plot_residual_overlay(df)
    plot_iterations_bar(df, df_sum)

    if df_sum is not None:
        print_and_save_summary(df_sum)


if __name__ == "__main__":
    main()
