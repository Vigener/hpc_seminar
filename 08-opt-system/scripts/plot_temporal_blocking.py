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

# 今回の実験に合わせた順序とラベル
METHOD_ORDER = ["laplace_basic1", "laplace_basic1_temporal"]
METHOD_LABELS = {
    "laplace_basic1": "最適化前 (1次元分割)",
    "laplace_basic1_temporal": "最適化後 (テンポラルブロッキング)",
}
METHOD_COLORS = {
    "laplace_basic1": "#1f77b4",  # Blue
    "laplace_basic1_temporal": "#ff7f0e",  # Orange
}

# グラフに埋め込むメモ
PARAMS_NOTE = "問題サイズ: XSIZE=4480, YSIZE=4480\n反復回数: NITER=1000"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create Temporal Blocking comparison plots from a raw CSV and write a summary CSV."
    )
    parser.add_argument("--input", type=Path, required=True, help="Raw CSV path.")
    parser.add_argument(
        "--summary-output", type=Path, required=True, help="Summary CSV output path."
    )
    parser.add_argument(
        "--figure-output", type=Path, required=True, help="Main figure output path."
    )
    parser.add_argument(
        "--title",
        default="テンポラルブロッキングによる1反復あたりの平均実行時間の比較",
        help="Figure title.",
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


def plot(
    summary_rows: list[dict[str, str]],
    output_path: Path,
    title: str,
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
        color = METHOD_COLORS.get(source)
        label = METHOD_LABELS.get(source, source)

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
            # 重なりを防ぐため、最適化前は上に、最適化後は下にテキストを配置
            y_offset = 8 if source == "laplace_basic1" else -14
            ax.annotate(
                f"{y_value:.5f}s",
                xy=(x_value, y_value),
                xytext=(0, y_offset),
                textcoords="offset points",
                ha="center",
                fontsize=9,
                color=color,
            )

    ax.set_title(title, fontsize=FONT_SIZE_TITLE)
    ax.set_xlabel("MPI プロセス数", fontsize=FONT_SIZE_AXIS_LABEL)
    ax.set_ylabel("1反復あたりの平均実行時間 [秒]", fontsize=FONT_SIZE_AXIS_LABEL)

    ax.set_xticks(x_values)
    ax.tick_params(axis="both", labelsize=FONT_SIZE_TICKS)
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(fontsize=FONT_SIZE_LEGEND)
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")  # 差を見やすくするためY軸も対数数スケールにする

    # グラフの右上にメモを追加
    ax.text(
        0.98,
        0.95,
        PARAMS_NOTE,
        transform=ax.transAxes,
        fontsize=12,
        ha="right",
        va="top",
        bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="gray", alpha=0.8),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def plot_speedup(
    summary_rows: list[dict[str, str]],
    output_path: Path,
    title: str,
) -> None:
    grouped = _group_summary_rows(summary_rows)
    x_values = sorted({int(row["nprocs"]) for row in summary_rows})
    if not x_values:
        return

    # laplace_basic1（最適化前）の時間を基準として辞書に保存
    baseline = {}
    for item in grouped.get("laplace_basic1", []):
        baseline[item[0]] = item[1]  # nprocs -> mean_sec

    fig, ax = plt.subplots(figsize=(10, 6))

    source = "laplace_basic1_temporal"
    series = grouped.get(source, [])

    if series:
        xs = []
        speedups = []
        for item in series:
            nprocs = item[0]
            mean = item[1]
            if nprocs in baseline and mean > 0:
                xs.append(nprocs)
                # 加速比 = 最適化前の時間 / 最適化後の時間
                speedup = baseline[nprocs] / mean
                speedups.append(speedup)

        color = METHOD_COLORS.get(source)
        label = "最適化による加速比"
        ax.plot(
            xs,
            speedups,
            marker="o",
            linewidth=2,
            markersize=6,
            color=color,
            label=label,
        )

        for x_value, y_value in zip(xs, speedups):
            ax.annotate(
                f"{y_value:.3f}x",
                xy=(x_value, y_value),
                xytext=(0, 6),
                textcoords="offset points",
                ha="center",
                fontsize=9,
                color=color,
            )

    ax.set_title(
        "テンポラルブロッキングによる加速比 (最適化前を1.0とした場合)",
        fontsize=FONT_SIZE_TITLE,
    )
    ax.set_xlabel("MPI プロセス数", fontsize=FONT_SIZE_AXIS_LABEL)
    ax.set_ylabel("加速比 (高いほど良い)", fontsize=FONT_SIZE_AXIS_LABEL)

    ax.set_xticks(x_values)
    ax.tick_params(axis="both", labelsize=FONT_SIZE_TICKS)
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(fontsize=FONT_SIZE_LEGEND, loc="upper left")
    ax.set_xscale("log", base=2)

    # 基準となる 1.0 のラインを点線で強調
    ax.axhline(y=1.0, color="black", linestyle=":", alpha=0.6, linewidth=1.5)

    # グラフの右上にメモを追加
    ax.text(
        0.98,
        0.95,
        PARAMS_NOTE,
        transform=ax.transAxes,
        fontsize=12,
        ha="right",
        va="top",
        bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="gray", alpha=0.8),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def print_markdown_tables(summary_rows: list[dict[str, str]]) -> None:
    grouped = _group_summary_rows(summary_rows)
    nprocs_all = sorted({int(row["nprocs"]) for row in summary_rows})
    if not nprocs_all:
        return

    baseline: dict[int, float] = {}
    for item in grouped.get("laplace_basic1", []):
        baseline[item[0]] = item[1]

    print("\n" + "=" * 70)
    print("【Markdown Table】テンポラルブロッキング性能比較 (XSIZE=4480, NITER=1000)")
    print("=" * 70 + "\n")

    print("### 1反復あたりの絶対実行時間 [秒]\n")
    header = "| 手法 |" + "".join(f" {n}プロセス |" for n in nprocs_all)
    sep = "| :--- |" + "".join(" :---: |" for _ in nprocs_all)
    print(header)
    print(sep)

    for source in METHOD_ORDER:
        series = grouped.get(source, [])
        means_by_nprocs: dict[int, float] = {item[0]: item[1] for item in series}
        label = METHOD_LABELS.get(source, source)
        cells = "|".join(f" {means_by_nprocs.get(n, 0):.4f} " for n in nprocs_all)
        print(f"| {label} |{cells}|")

    print("\n### テンポラルブロッキングによる加速比\n")
    header_rel = "| 手法 |" + "".join(f" {n}プロセス |" for n in nprocs_all)
    sep_rel = "| :--- |" + "".join(" :---: |" for _ in nprocs_all)
    print(header_rel)
    print(sep_rel)

    source = "laplace_basic1_temporal"
    series = grouped.get(source, [])
    rel_means: dict[int, float] = {item[0]: item[1] for item in series}
    label = METHOD_LABELS.get(source, source)
    cell_parts: list[str] = []
    for n in nprocs_all:
        if n in rel_means and n in baseline and baseline[n] > 0:
            rel = baseline[n] / rel_means[n]  # 速くなった割合（加速比）
            cell_parts.append(f" {rel:.3f}x ")
        else:
            cell_parts.append(" N/A ")
    print(f"| 加速比 |{'|'.join(cell_parts)}|")

    print("\n" + "=" * 70 + "\n")


def main() -> int:
    args = parse_args()
    rows = load_rows(args.input)
    summary_rows = aggregate(rows)
    write_summary(args.summary_output, summary_rows)

    # 1. 絶対時間の比較グラフ (Y軸対数)
    plot(summary_rows, args.figure_output, args.title)

    # 2. 加速比のグラフ
    speedup_output = args.figure_output.with_name(
        f"{args.figure_output.stem}_speedup{args.figure_output.suffix}"
    )
    plot_speedup(summary_rows, speedup_output, args.title)

    # 3. Markdownテーブルを標準出力に表示
    print_markdown_tables(summary_rows)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
