# /// script
# requires-python = ">=3.12"
# ///
from __future__ import annotations

import argparse
import re
from pathlib import Path

import japanize_matplotlib
import matplotlib.pyplot as plt


FONT_SIZE_TITLE = 24
FONT_SIZE_AXIS_LABEL = 20
FONT_SIZE_TICKS = 14
FONT_SIZE_LEGEND = 14

THREAD_ORDER = [1, 2, 4]
SIZE_ORDER = ["M=N=4096", "M=N=8192"]
OPTIMIZATION_ORDER = ["unoptimized", "optimized"]

# (size, optimization) -> style
SERIES_STYLE = {
    ("M=N=4096", "unoptimized"): {"color": "#1f77b4", "marker": "o", "linestyle": "-"},
    ("M=N=4096", "optimized"): {"color": "#1f77b4", "marker": "s", "linestyle": "--"},
    ("M=N=8192", "unoptimized"): {"color": "#d62728", "marker": "o", "linestyle": "-"},
    ("M=N=8192", "optimized"): {"color": "#d62728", "marker": "s", "linestyle": "--"},
}

THREAD_RE = re.compile(r"^OMP_NUM_THREADS=(\d+)$")
TIME_RE = re.compile(r"^(Unoptimized|Optimized):\s+Execution Time:\s+([0-9.]+)\s+sec$")


def parse_run_output(input_path: Path) -> tuple[dict[str, dict[int, float]], dict[str, dict[int, float]]]:
    """
    Parse a combined run output file with both unoptimized and optimized versions.
    Returns (data_unoptimized, data_optimized)
    """
    data_unopt: dict[str, dict[int, float]] = {size: {} for size in SIZE_ORDER}
    data_opt: dict[str, dict[int, float]] = {size: {} for size in SIZE_ORDER}
    
    current_size = SIZE_ORDER[0]
    current_thread_count: int | None = None
    current_optimization: str | None = None  # "Unoptimized" or "Optimized"

    for raw_line in input_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # Check for size marker
        if line == "=== M=N=4096 ===":
            current_size = "M=N=4096"
            current_thread_count = None
            current_optimization = None
            continue
        elif line == "=== M=N=8192 ===":
            current_size = "M=N=8192"
            current_thread_count = None
            current_optimization = None
            continue

        # Check for thread count
        thread_match = THREAD_RE.match(line)
        if thread_match:
            current_thread_count = int(thread_match.group(1))
            continue

        # Check for optimization result line
        time_match = TIME_RE.match(line)
        if time_match:
            opt_label = time_match.group(1)
            time_sec = float(time_match.group(2))
            time_ms = time_sec * 1000.0

            if current_thread_count is None:
                raise ValueError(f"実行時間が見つかりましたがスレッド数が不明です: {line}")

            target_dict = data_opt if opt_label == "Optimized" else data_unopt
            target_dict[current_size][current_thread_count] = time_ms

    return data_unopt, data_opt


def validate_data(data_unopt: dict[str, dict[int, float]], data_opt: dict[str, dict[int, float]]) -> None:
    """Validate that both datasets have all required sizes and thread counts"""
    for data in [data_unopt, data_opt]:
        for size_label in SIZE_ORDER:
            series = data.get(size_label, {})
            missing_threads = [t for t in THREAD_ORDER if t not in series]
            if missing_threads:
                raise ValueError(f"{size_label} のデータが不足しています: {missing_threads}")


def plot_graph(
    data_unopt: dict[str, dict[int, float]],
    data_opt: dict[str, dict[int, float]],
    output_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(12, 7))

    data_dict = {"unoptimized": data_unopt, "optimized": data_opt}

    for size_label in SIZE_ORDER:
        for opt_label in OPTIMIZATION_ORDER:
            series = data_dict[opt_label][size_label]
            x_values = THREAD_ORDER
            y_values = [series[thread_count] for thread_count in x_values]
            style = SERIES_STYLE[(size_label, opt_label)]

            label_display = f"{size_label} ({opt_label})"
            ax.plot(
                x_values,
                y_values,
                marker=style["marker"],
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=2,
                markersize=8,
                label=label_display,
            )

            for thread_count, time_ms in zip(x_values, y_values):
                ax.annotate(
                    f"{time_ms:.1f} ms",
                    xy=(thread_count, time_ms),
                    xytext=(0, 8),
                    textcoords="offset points",
                    ha="center",
                    fontsize=FONT_SIZE_TICKS - 1,
                    color=style["color"],
                )

    ax.set_xlabel("スレッド数", fontsize=FONT_SIZE_AXIS_LABEL)
    ax.set_ylabel("実行時間 [ms]", fontsize=FONT_SIZE_AXIS_LABEL)
    ax.set_title("OpenMP 行列ベクトル積の実行時間比較\n（SIMD最適化の有無）", fontsize=FONT_SIZE_TITLE)
    ax.set_xticks(THREAD_ORDER)
    ax.tick_params(axis="x", labelsize=FONT_SIZE_TICKS)
    ax.tick_params(axis="y", labelsize=FONT_SIZE_TICKS)
    ax.set_ylim(bottom=0)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(fontsize=FONT_SIZE_LEGEND)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format=output_path.suffix.lstrip("."), bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OpenMP の実行時間（SIMD最適化有無）をスレッド数ごとに比較するグラフを描画します。"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="両方の最適化版を含む統合実行結果ファイル",
    )
    parser.add_argument(
        "output_path",
        type=Path,
        help="出力先の画像または PDF ファイル",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_unopt, data_opt = parse_run_output(args.input_file)
    validate_data(data_unopt, data_opt)
    plot_graph(data_unopt, data_opt, args.output_path)


if __name__ == "__main__":
    main()