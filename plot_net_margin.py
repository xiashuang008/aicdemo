from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Sequence

from PIL import Image, ImageDraw, ImageFont

COMPANIES = (
    ("0000320193", "Apple", "#5B7C99"),
    ("0000789019", "Microsoft", "#0078D4"),
    ("0001652044", "Alphabet (Google)", "#34A853"),
    ("0001018724", "Amazon", "#E8890C"),
)


def load_data(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as file:
        document = json.load(file)
    by_cik = {company["cik"]: company for company in document["companies"]}
    rows = []
    for cik, label, color in COMPANIES:
        company = by_cik[cik]
        metrics = company["metrics"]
        period = company["period"]
        revenue = metrics["revenue_usd"]
        net_income = metrics["net_income_usd"]
        if not revenue or not math.isfinite(revenue) or not math.isfinite(net_income):
            raise ValueError(f"{label} 的营收或净利润无效")
        for key in ("revenue", "net_income"):
            source = company["sources"][key]
            if (source["start"], source["end"]) != (period["start"], period["end"]):
                raise ValueError(f"{label} 的 {key} 与财年期间不一致")
        margin = net_income / revenue * 100
        if not math.isclose(margin, metrics["net_margin_pct"], abs_tol=1e-10):
            raise ValueError(f"{label} 的净利率与原始数据不一致")
        rows.append(
            {
                "label": label,
                "color": color,
                "margin": margin,
                "revenue": revenue,
                "net_income": net_income,
                "fiscal_year_end": period["end"],
            }
        )
    return rows


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = (
        ("C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf")
        if bold
        else ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf")
    )
    for name in (*names, "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def centered_text(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    text: str,
    text_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str,
) -> None:
    draw.text((x, y), text, font=text_font, fill=fill, anchor="mm")


def render(rows: Sequence[dict[str, Any]], output: Path) -> None:
    width, height = 1600, 1000
    image = Image.new("RGB", (width, height), "#F5F7FB")
    draw = ImageDraw.Draw(image)

    title_font = font(52, bold=True)
    subtitle_font = font(25)
    axis_font = font(23)
    label_font = font(27, bold=True)
    date_font = font(21)
    value_font = font(34, bold=True)
    note_font = font(20)

    draw.text((90, 65), "Big Tech Net Margin Comparison", font=title_font, fill="#172033")
    draw.text(
        (92, 140),
        "Latest reported full fiscal year  |  Net income / revenue",
        font=subtitle_font,
        fill="#667085",
    )
    draw.rounded_rectangle((60, 205, 1540, 845), radius=24, fill="#FFFFFF")

    plot_left, plot_right = 185, 1480
    plot_top, plot_bottom = 300, 700
    y_max = 45.0
    draw.text((105, 247), "Net margin (%)", font=axis_font, fill="#475467")

    for tick in (0, 10, 20, 30, 40):
        y = plot_bottom - (tick / y_max) * (plot_bottom - plot_top)
        draw.line((plot_left, y, plot_right, y), fill="#E4E9F0", width=2)
        draw.text(
            (plot_left - 28, y),
            str(tick),
            font=axis_font,
            fill="#667085",
            anchor="rm",
        )

    slot = (plot_right - plot_left) / len(rows)
    bar_width = 180
    for index, row in enumerate(rows):
        center_x = plot_left + slot * (index + 0.5)
        bar_top = plot_bottom - (row["margin"] / y_max) * (plot_bottom - plot_top)
        draw.rounded_rectangle(
            (center_x - bar_width / 2, bar_top, center_x + bar_width / 2, plot_bottom),
            radius=18,
            fill=row["color"],
        )
        centered_text(
            draw,
            center_x,
            bar_top - 38,
            f'{row["margin"]:.1f}%',
            value_font,
            "#172033",
        )
        centered_text(draw, center_x, 745, row["label"], label_font, "#263248")
        centered_text(
            draw,
            center_x,
            790,
            f'FY ends {row["fiscal_year_end"]}',
            date_font,
            "#7A8494",
        )

    draw.line((plot_left, plot_bottom, plot_right, plot_bottom), fill="#AAB4C3", width=2)
    draw.text(
        (90, 890),
        "Source: SEC EDGAR XBRL company facts API (GAAP). Fiscal year-end dates differ across companies.",
        font=note_font,
        fill="#667085",
    )
    draw.text(
        (90, 928),
        "Net margin = net income / revenue x 100%. One-off gains and tax items may affect comparability.",
        font=note_font,
        fill="#667085",
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="绘制苹果、微软、Alphabet 和亚马逊的年度净利率对比图。")
    parser.add_argument("--input", type=Path, default=Path("comparison.json"), help="财务数据 JSON 路径。")
    parser.add_argument("--output", type=Path, default=Path("net_margin_comparison.png"), help="输出 PNG 路径。")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    rows = load_data(args.input)
    render(rows, args.output)
    for row in rows:
        print(
            f'{row["label"]}: {row["margin"]:.6f}% '
            f'(net income {row["net_income"]:,} / revenue {row["revenue"]:,}; '
            f'FY ends {row["fiscal_year_end"]})'
        )
    print(f"Saved: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
