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
MODE_ORDER = ["serial", "parallel", "parallel_simd"]
MODE_DISPLAY = {
    "serial": "Serial",
    "parallel": "Parallel",
    "parallel_simd": "Parallel + SIMD",
}

# (size, mode) -> style
SERIES_STYLE = {
    ("M=N=4096", "serial"): {"color": "#1f77b4", "marker": "o", "linestyle": "-"},
    ("M=N=4096", "parallel"): {"color": "#1f77b4", "marker": "s", "linestyle": "--"},
    ("M=N=4096", "parallel_simd"): {"color": "#1f77b4", "marker": "^", "linestyle": ":"},
    ("M=N=8192", "serial"): {"color": "#d62728", "marker": "o", "linestyle": "-"},
    ("M=N=8192", "parallel"): {"color": "#d62728", "marker": "s", "linestyle": "--"},
    ("M=N=8192", "parallel_simd"): {"color": "#d62728", "marker": "^", "linestyle": ":"},
}

THREAD_RE = re.compile(r"^OMP_NUM_THREADS=(\d+)$")
TIME_RE = re.compile(
    r"^(Serial|Parallel|Parallel with SIMD|Unoptimized|Optimized|Optimized with SIMD):\s+Execution Time:\s+([0-9.]+)\s+sec$"
)

LABEL_TO_MODE = {
    "Serial": "serial",
    "Parallel": "parallel",
    "Parallel with SIMD": "parallel_simd",
    "Unoptimized": "serial",
    "Optimized": "parallel_simd",
    "Optimized with SIMD": "parallel_simd",
}


def parse_run_output(input_path: Path) -> dict[str, dict[str, dict[int, float]]]:
    """Parse a combined run output file with all modes."""
    data: dict[str, dict[str, dict[int, float]]] = {
        mode: {size: {} for size in SIZE_ORDER} for mode in MODE_ORDER
    }
    
    current_size = SIZE_ORDER[0]
    current_thread_count: int | None = None

    for raw_line in input_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # Check for size marker
        if line == "=== M=N=4096 ===":
            current_size = "M=N=4096"
            current_thread_count = None
            continue
        elif line == "=== M=N=8192 ===":
            current_size = "M=N=8192"
            current_thread_count = None
            continue

        # Check for thread count
        thread_match = THREAD_RE.match(line)
        if thread_match:
            current_thread_count = int(thread_match.group(1))
            continue

        # Check for result line
        time_match = TIME_RE.match(line)
        if time_match:
            label = time_match.group(1)
            time_sec = float(time_match.group(2))
            time_ms = time_sec * 1000.0

            if current_thread_count is None:
                raise ValueError(f"実行時間が見つかりましたがスレッド数が不明です: {line}")

            mode = LABEL_TO_MODE.get(label)
            if mode is None:
                raise ValueError(f"未対応のラベルです: {label}")

            data[mode][current_size][current_thread_count] = time_ms

    return data


def validate_data(data: dict[str, dict[str, dict[int, float]]]) -> None:
    """Validate that all datasets have all required sizes and thread counts"""
    for mode in MODE_ORDER:
        for size_label in SIZE_ORDER:
            series = data.get(mode, {}).get(size_label, {})
            missing_threads = [t for t in THREAD_ORDER if t not in series]
            if missing_threads:
                raise ValueError(f"{size_label} の {mode} データが不足しています: {missing_threads}")


def plot_graph(
    data: dict[str, dict[str, dict[int, float]]],
    output_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(12, 7))

    for size_label in SIZE_ORDER:
        for mode in MODE_ORDER:
            series = data[mode][size_label]
            x_values = THREAD_ORDER
            y_values = [series[thread_count] for thread_count in x_values]
            style = SERIES_STYLE[(size_label, mode)]

            label_display = f"{size_label} ({MODE_DISPLAY[mode]})"
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
    ax.set_title("OpenMP 行列ベクトル積の実行時間比較\n（並列化とSIMDの有無）", fontsize=FONT_SIZE_TITLE)
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
        description="OpenMP の実行時間（並列化と SIMD の有無）をスレッド数ごとに比較するグラフを描画します。"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="3 モードの結果を含む統合実行結果ファイル",
    )
    parser.add_argument(
        "output_path",
        type=Path,
        help="出力先の画像または PDF ファイル",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = parse_run_output(args.input_file)
    validate_data(data)
    plot_graph(data, args.output_path)


if __name__ == "__main__":
    main()