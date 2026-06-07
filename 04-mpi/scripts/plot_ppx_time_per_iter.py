#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import japanize_matplotlib  # noqa: F401
import matplotlib.pyplot as plt

# フォントサイズの定数設定
FONT_SIZE_TITLE = 20
FONT_SIZE_AXIS_LABEL = 18
FONT_SIZE_TICKS = 14
FONT_SIZE_LEGEND = 14

METHOD_ORDER = ["laplace", "laplace_basic1", "laplace_basic2", "laplace_advanced"]
# 凡例をわかりやすい日本語に変更
METHOD_LABELS = {
    "laplace": "オリジナル (laplace)",
    "laplace_basic1": "1次元分割 (basic1)",
    "laplace_basic2": "2次元分割 (basic2)",
    "laplace_advanced": "片方向通信 (advanced)",
}
METHOD_COLORS = {
    "laplace": "#444444",
    "laplace_basic1": "#1f77b4",
    "laplace_basic2": "#ff7f0e",
    "laplace_advanced": "#2ca02c",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create PPX time per iteration plots from a raw CSV and write a summary CSV."
    )
    parser.add_argument("--input", type=Path, required=True, help="Raw CSV path.")
    parser.add_argument(
        "--summary-output", type=Path, required=True, help="Summary CSV output path."
    )
    parser.add_argument(
        "--figure-output", type=Path, required=True, help="Main figure output path."
    )
    parser.add_argument(
        "--zoom-figure-output",
        type=Path,
        default=None,
        help="Zoomed figure output path.",
    )
    parser.add_argument(
        "--relative-figure-output",
        type=Path,
        default=None,
        help="Relative time figure output path.",
    )
    parser.add_argument(
        "--title",
        default="Laplace MPI: 1反復あたりの平均実行時間",
        help="Figure title.",
    )
    parser.add_argument(
        "--show-error-bars",
        action="store_true",
        help="Show standard deviation error bars.",
    )
    return parser.parse_args()


def load_rows(input_path: Path) -> list[dict[str, str]]:
    with input_path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def aggregate(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, int], list[float]] = defaultdict(list)
    for row in rows:
        if row.get("status", "").lower() != "ok":
            continue
        source = row["source"]
        nprocs = int(row["nprocs"])
        elapsed = float(row["time_per_iter"])
        grouped[(source, nprocs)].append(elapsed)

    summary_rows: list[dict[str, str]] = []
    for source in METHOD_ORDER:
        nprocs_values = sorted(
            nprocs
            for (current_source, nprocs) in grouped.keys()
            if current_source == source
        )
        for nprocs in nprocs_values:
            samples = grouped[(source, nprocs)]
            mean_sec = statistics.mean(samples)
            stdev_sec = statistics.stdev(samples) if len(samples) >= 2 else 0.0
            summary_rows.append(
                {
                    "source": source,
                    "nprocs": str(nprocs),
                    "repeat_count": str(len(samples)),
                    "mean_sec": f"{mean_sec:.9f}",
                    "stdev_sec": f"{stdev_sec:.9f}",
                }
            )
    return summary_rows


def write_summary(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source", "nprocs", "repeat_count", "mean_sec", "stdev_sec"],
        )
        writer.writeheader()
        writer.writerows(rows)


def _group_summary_rows(
    summary_rows: list[dict[str, str]],
) -> dict[str, list[tuple[int, float, float]]]:
    grouped: dict[str, list[tuple[int, float, float]]] = defaultdict(list)
    for row in summary_rows:
        grouped[row["source"]].append(
            (int(row["nprocs"]), float(row["mean_sec"]), float(row["stdev_sec"]))
        )
    for source in grouped:
        grouped[source].sort(key=lambda item: item[0])
    return grouped


def _zoom_upper_bound(summary_rows: list[dict[str, str]]) -> float:
    non_baseline = [
        float(row["mean_sec"]) for row in summary_rows if row["source"] != "laplace"
    ]
    values = (
        non_baseline
        if non_baseline
        else [float(row["mean_sec"]) for row in summary_rows]
    )
    if not values:
        return 1.0
    return max(values) * 1.15


def plot(
    summary_rows: list[dict[str, str]],
    output_path: Path,
    title: str,
    show_error_bars: bool,
    zoom: bool = False,
) -> None:
    grouped = _group_summary_rows(summary_rows)
    x_values = sorted({int(row["nprocs"]) for row in summary_rows})
    if not x_values:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    for source in METHOD_ORDER:
        series = grouped.get(source, [])
        if not series:
            continue
        xs = [item[0] for item in series]
        means = [item[1] for item in series]
        stdevs = [item[2] for item in series]
        color = METHOD_COLORS.get(source)
        label = METHOD_LABELS.get(source, source)
        if show_error_bars:
            ax.errorbar(
                xs,
                means,
                yerr=stdevs,
                marker="o",
                linewidth=2,
                markersize=6,
                capsize=4,
                color=color,
                label=label,
            )
        else:
            ax.plot(
                xs,
                means,
                marker="o",
                linewidth=2,
                markersize=6,
                color=color,
                label=label,
            )

        for x_value, y_value in zip(xs, means):
            ax.annotate(
                f"{y_value:.5f}s",
                xy=(x_value, y_value),
                xytext=(0, 6),
                textcoords="offset points",
                ha="center",
                fontsize=9,
                color=color,
            )

    ax.set_title(title + (" (Y軸拡大)" if zoom else ""), fontsize=FONT_SIZE_TITLE)
    ax.set_xlabel("MPI プロセス数", fontsize=FONT_SIZE_AXIS_LABEL)
    ax.set_ylabel("1反復あたりの平均実行時間 [秒]", fontsize=FONT_SIZE_AXIS_LABEL)

    ax.set_xticks(x_values)
    ax.tick_params(axis="both", labelsize=FONT_SIZE_TICKS)
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(fontsize=FONT_SIZE_LEGEND)
    ax.set_xscale("log", base=2)
    ax.set_xlim(left=min(x_values) * 0.9, right=max(x_values) * 1.1)
    if zoom:
        ax.set_ylim(bottom=0, top=_zoom_upper_bound(summary_rows))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def plot_relative(
    summary_rows: list[dict[str, str]],
    output_path: Path,
    title: str,
    zoom_y: bool = False,
) -> None:
    grouped = _group_summary_rows(summary_rows)
    x_values = sorted({int(row["nprocs"]) for row in summary_rows})
    if not x_values:
        return

    # laplace（オリジナル）の時間を基準 (1.0) として辞書に保存
    baseline = {}
    for item in grouped.get("laplace", []):
        baseline[item[0]] = item[1]  # nprocs -> mean_sec

    fig, ax = plt.subplots(figsize=(10, 6))

    # Y軸ズーム時の計算用に値を保持するリスト
    focus_vals = []

    for source in METHOD_ORDER:
        series = grouped.get(source, [])
        if not series:
            continue

        xs = []
        rel_means = []
        for item in series:
            nprocs = item[0]
            mean = item[1]
            if nprocs in baseline and baseline[nprocs] > 0:
                xs.append(nprocs)
                val = mean / baseline[nprocs]
                rel_means.append(val)
                # advanced以外の値をフォーカス用リストに保存
                if source in ["laplace", "laplace_basic1", "laplace_basic2"]:
                    focus_vals.append(val)

        color = METHOD_COLORS.get(source)
        label = METHOD_LABELS.get(source, source)
        ax.plot(
            xs,
            rel_means,
            marker="o",
            linewidth=2,
            markersize=6,
            color=color,
            label=label,
        )

        for x_value, y_value in zip(xs, rel_means):
            # ズーム時は、枠外に飛んでいく高い値はアノテーションを描画しない
            if zoom_y and y_value > max(focus_vals) * 1.1:
                continue

            ax.annotate(
                f"{y_value:.3f}",
                xy=(x_value, y_value),
                xytext=(0, 6),
                textcoords="offset points",
                ha="center",
                fontsize=9,
                color=color,
            )

    plot_title = "Laplace MPI: オリジナル手法に対する相対実行時間"
    if zoom_y:
        plot_title += " (Y軸拡大)"
        # basic1, basic2, laplace の値だけでY軸の範囲を決定
        if focus_vals:
            ymin = min(focus_vals) * 0.95
            ymax = max(focus_vals) * 1.05
            ax.set_ylim(bottom=ymin, top=ymax)

    ax.set_title(plot_title, fontsize=FONT_SIZE_TITLE)
    ax.set_xlabel("MPI プロセス数", fontsize=FONT_SIZE_AXIS_LABEL)
    ax.set_ylabel("相対実行時間 (オリジナル = 1.000)", fontsize=FONT_SIZE_AXIS_LABEL)

    ax.set_xticks(x_values)
    ax.tick_params(axis="both", labelsize=FONT_SIZE_TICKS)
    ax.grid(True, linestyle="--", alpha=0.35)

    # 凡例の位置を少し調整（線と被らないように）
    ax.legend(fontsize=FONT_SIZE_LEGEND, loc="upper left")

    ax.set_xscale("log", base=2)
    ax.set_xlim(left=min(x_values) * 0.9, right=max(x_values) * 1.1)

    # 基準となる 1.0 のラインを点線で強調
    ax.axhline(y=1.0, color="black", linestyle=":", alpha=0.6, linewidth=1.5)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def print_markdown_tables(summary_rows: list[dict[str, str]]) -> None:
    """絶対時間と相対時間のMarkdownテーブルを標準出力に表示する"""
    grouped = _group_summary_rows(summary_rows)
    nprocs_all = sorted({int(row["nprocs"]) for row in summary_rows})
    if not nprocs_all:
        return

    # laplace（オリジナル）の平均時間を取得（相対値の基準）
    baseline: dict[int, float] = {}
    for item in grouped.get("laplace", []):
        baseline[item[0]] = item[1]

    # 手法の表示名（日本語）
    display_names = {
        "laplace": "オリジナル",
        "laplace_basic1": "1次元分割",
        "laplace_basic2": "2次元分割",
        "laplace_advanced": "片方向通信",
    }

    print("\n" + "=" * 70)
    print("【Markdown Table】1反復あたりの平均実行時間")
    print("=" * 70 + "\n")

    # ---- 絶対時間テーブル ----
    print("### 絶対実行時間 [秒]\n")
    header = "| 手法 |" + "".join(f" {n}プロセス |" for n in nprocs_all)
    sep = "| :--- |" + "".join(" :---: |" for _ in nprocs_all)
    print(header)
    print(sep)

    for source in METHOD_ORDER:
        series = grouped.get(source, [])
        means_by_nprocs: dict[int, float] = {item[0]: item[1] for item in series}
        label = display_names.get(source, source)
        cells = "|".join(f" {means_by_nprocs.get(n, 0):.6f} " for n in nprocs_all)
        print(f"| {label} |{cells}|")

    print("")

    # ---- 相対時間テーブル ----
    print("### 相対実行時間 (オリジナル = 1.000)\n")
    header_rel = "| 手法 |" + "".join(f" {n}プロセス |" for n in nprocs_all)
    sep_rel = "| :--- |" + "".join(" :---: |" for _ in nprocs_all)
    print(header_rel)
    print(sep_rel)

    for source in METHOD_ORDER:
        series = grouped.get(source, [])
        rel_means: dict[int, float] = {item[0]: item[1] for item in series}
        label = display_names.get(source, source)
        cell_parts: list[str] = []
        for n in nprocs_all:
            if n in rel_means and n in baseline and baseline[n] > 0:
                rel = rel_means[n] / baseline[n]
                cell_parts.append(f" {rel:.3f} ")
            else:
                cell_parts.append(" N/A ")
        print(f"| {label} |{'|'.join(cell_parts)}|")

    print("\n" + "=" * 70 + "\n")


def default_zoom_path(figure_output: Path) -> Path:
    return figure_output.with_name(f"{figure_output.stem}_zoom{figure_output.suffix}")


def default_relative_path(figure_output: Path) -> Path:
    return figure_output.with_name(
        f"{figure_output.stem}_relative{figure_output.suffix}"
    )


def default_relative_zoom_path(figure_output: Path) -> Path:
    return figure_output.with_name(
        f"{figure_output.stem}_relative_zoom{figure_output.suffix}"
    )


def main() -> int:
    args = parse_args()
    rows = load_rows(args.input)
    summary_rows = aggregate(rows)
    write_summary(args.summary_output, summary_rows)

    # 1. 絶対時間の全体グラフ
    plot(summary_rows, args.figure_output, args.title, args.show_error_bars, zoom=False)

    # 2. 絶対時間のズームグラフ
    zoom_output = (
        args.zoom_figure_output
        if args.zoom_figure_output is not None
        else default_zoom_path(args.figure_output)
    )
    plot(summary_rows, zoom_output, args.title, args.show_error_bars, zoom=True)

    # 3. 相対実行時間の全体グラフ
    relative_output = (
        args.relative_figure_output
        if args.relative_figure_output is not None
        else default_relative_path(args.figure_output)
    )
    plot_relative(summary_rows, relative_output, args.title, zoom_y=False)

    # 4. 相対実行時間のズームグラフ（NEW）
    relative_zoom_output = default_relative_zoom_path(args.figure_output)
    plot_relative(summary_rows, relative_zoom_output, args.title, zoom_y=True)

    # 5. Markdownテーブルを標準出力に表示
    print_markdown_tables(summary_rows)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
