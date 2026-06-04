#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import japanize_matplotlib
import matplotlib.pyplot as plt


FONT_SIZE_TITLE = 24
FONT_SIZE_AXIS_LABEL = 20
FONT_SIZE_TICKS = 14
FONT_SIZE_LEGEND = 12

SOURCE_ORDER = [
	"matvec_original",
	"matvec_loopswap",
	"matvec_loopswap_padding",
	"matvec_loopswap_unroll",
]

SOURCE_LABELS = {
	"matvec_original": "オリジナル",
	"matvec_loopswap": "ループ入れ替え",
	"matvec_loopswap_padding": "ループ入れ替え＋パディング",
	"matvec_loopswap_unroll": "ループ入れ替え＋ループアンローリング",
}

SOURCE_COLORS = {
	"matvec_original": "#4c78a8",
	"matvec_loopswap": "#f58518",
	"matvec_loopswap_padding": "#54a24b",
	"matvec_loopswap_unroll": "#e45756",
}


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="MatVec の PPX 実行結果 CSV を読み取り、日本語ラベルの棒グラフを描画します。"
	)
	parser.add_argument("input_file", type=Path, help="入力CSVファイルのパス")
	parser.add_argument("output_file", type=Path, help="出力先画像ファイルのパス")
	return parser.parse_args()


def load_times(input_file: Path) -> dict[str, list[float]]:
	times_by_source: dict[str, list[float]] = defaultdict(list)

	with input_file.open("r", encoding="utf-8", newline="") as handle:
		reader = csv.DictReader(handle)
		expected_fields = {"source", "repeat", "time"}
		if set(reader.fieldnames or ()) != expected_fields:
			raise ValueError(f"CSV のヘッダが不正です: {reader.fieldnames}")

		for row in reader:
			source = row["source"]
			if source not in SOURCE_ORDER:
				continue
			times_by_source[source].append(float(row["time"]))

	return times_by_source


def validate_times(times_by_source: dict[str, list[float]]) -> None:
	missing_sources = [source for source in SOURCE_ORDER if source not in times_by_source]
	if missing_sources:
		raise ValueError(f"CSV に必要な source がありません: {missing_sources}")

	empty_sources = [source for source in SOURCE_ORDER if not times_by_source[source]]
	if empty_sources:
		raise ValueError(f"実行時間が1件もない source があります: {empty_sources}")


def plot_graph(times_by_source: dict[str, list[float]], output_file: Path) -> None:
	labels = [SOURCE_LABELS[source] for source in SOURCE_ORDER]
	averages = [sum(times_by_source[source]) / len(times_by_source[source]) for source in SOURCE_ORDER]
	colors = [SOURCE_COLORS[source] for source in SOURCE_ORDER]

	fig, ax = plt.subplots(figsize=(14, 8))
	bars = ax.bar(labels, averages, color=colors, width=0.6)

	ax.set_ylabel("実行時間 [sec]", fontsize=FONT_SIZE_AXIS_LABEL)
	ax.set_title("MatVec の実行時間比較", fontsize=FONT_SIZE_TITLE, pad=18)
	ax.tick_params(axis="both", labelsize=FONT_SIZE_TICKS)
	ax.set_ylim(bottom=0)
	ax.grid(True, axis="y", linestyle="--", alpha=0.35)

	for bar, average in zip(bars, averages, strict=True):
		ax.annotate(
			f"{average:.3f} s",
			xy=(bar.get_x() + bar.get_width() / 2.0, average),
			xytext=(0, 8),
			textcoords="offset points",
			ha="center",
			va="bottom",
			fontsize=FONT_SIZE_LEGEND,
		)

	ax.legend(bars, labels, fontsize=FONT_SIZE_LEGEND)

	output_file.parent.mkdir(parents=True, exist_ok=True)
	fig.tight_layout()
	fig.savefig(output_file, dpi=200, bbox_inches="tight")
	plt.close(fig)


def main() -> None:
	args = parse_args()
	times_by_source = load_times(args.input_file)
	validate_times(times_by_source)
	plot_graph(times_by_source, args.output_file)


if __name__ == "__main__":
	main()
