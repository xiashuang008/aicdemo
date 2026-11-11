from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw

from plot_peer_comparison import GRID, MUTED, PROJECT_ROOT, TEXT, axis_limit, centered_text, font, load_data, save_png


def render_net_margin(rows) -> Image.Image:
    image = Image.new("RGB", (1000, 660), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = 105, 105, 960, 515
    maximum = axis_limit(rows, "net_margin", 20)
    tick_font = font(28)
    value_font = font(34, bold=True)
    label_font = font(32, bold=True)

    draw.text((35, 28), "净利率（%）", font=font(34, bold=True), fill=TEXT)
    for tick in range(0, maximum + 1, 20):
        y = bottom - tick / maximum * (bottom - top)
        draw.line((left, y, right, y), fill=GRID, width=3)
        draw.text((left - 18, y), str(tick), font=tick_font, fill=MUTED, anchor="rm")

    slot = (right - left) / len(rows)
    for index, row in enumerate(rows):
        center_x = left + slot * (index + 0.5)
        value = row["net_margin"]
        bar_top = bottom - value / maximum * (bottom - top)
        draw.rounded_rectangle(
            (center_x - 48, bar_top, center_x + 48, bottom),
            radius=10,
            fill=row["color"],
        )
        centered_text(draw, center_x, bar_top - 30, f"{value:.1f}%", value_font)
        centered_text(draw, center_x, bottom + 58, row["name"], label_font)
    draw.line((left, bottom, right, bottom), fill="#AAB4C3", width=3)
    return image


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成供 LaTeX 报告使用的净利率图，不含图题、来源或财年注释。")
    parser.add_argument("--input", type=Path, default=PROJECT_ROOT / "comparison.json", help="财务数据 JSON 路径。")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "output" / "figures" / "net_margin_report.png", help="输出 PNG 路径。")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    rows, _, _ = load_data(args.input)
    image = render_net_margin(rows)
    save_png(image, args.output)
    for row in rows:
        print(f'{row["name"]}: {row["net_margin"]:.6f}%')
    print(f"Saved: {args.output.resolve()}")
    image.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
