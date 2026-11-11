from __future__ import annotations

import argparse
import json
import math
from datetime import date
from pathlib import Path
from typing import Any, Sequence

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMPANIES = (
    ("0000320193", "苹果", "#5B7C99"),
    ("0000789019", "微软", "#0078D4"),
    ("0001652044", "Alphabet", "#34A853"),
    ("0001018724", "亚马逊", "#E8890C"),
    ("0001045810", "英伟达", "#8A60B0"),
)
MARGIN_SERIES = (
    ("gross_margin", "毛利率", "#4C78A8"),
    ("operating_margin", "经营利润率", "#F58518"),
    ("net_margin", "净利率", "#54A24B"),
)
BACKGROUND = "#F5F7FB"
TEXT = "#172033"
MUTED = "#667085"
GRID = "#E4E9F0"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = (
        ("C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf")
        if bold
        else ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf")
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
    fill: str = TEXT,
) -> None:
    draw.text((x, y), text, font=text_font, fill=fill, anchor="mm")


def checked_number(metrics: dict[str, Any], key: str, label: str) -> float:
    value = metrics.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} 的 {key} 缺失或无效")
    return float(value)


def check_close(actual: float, expected: float, label: str, metric: str) -> None:
    if not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-9):
        raise ValueError(f"{label} 的{metric}与原始数据不一致")


def load_data(path: Path) -> tuple[list[dict[str, Any]], str, str]:
    with path.open(encoding="utf-8") as file:
        document = json.load(file)
    by_cik = {company["cik"]: company for company in document["companies"]}
    rows = []
    for cik, label, color in COMPANIES:
        if cik not in by_cik:
            raise ValueError(f"输入文件缺少{label}（CIK {cik}）")
        company = by_cik[cik]
        metrics = company["metrics"]
        period = company["period"]
        start = date.fromisoformat(period["start"])
        end = date.fromisoformat(period["end"])
        if not 300 <= (end - start).days <= 400:
            raise ValueError(f"{label} 的财年期间不是完整年度")

        revenue = checked_number(metrics, "revenue_usd", label)
        previous_revenue = checked_number(metrics, "previous_year_revenue_usd", label)
        gross_profit = checked_number(metrics, "gross_profit_usd", label)
        operating_income = checked_number(metrics, "operating_income_usd", label)
        net_income = checked_number(metrics, "net_income_usd", label)
        if revenue <= 0 or previous_revenue <= 0:
            raise ValueError(f"{label} 的营收必须大于零")

        growth = (revenue / previous_revenue - 1) * 100
        gross_margin = gross_profit / revenue * 100
        operating_margin = operating_income / revenue * 100
        net_margin = net_income / revenue * 100
        check_close(growth, checked_number(metrics, "revenue_growth_pct", label), label, "营收增速")
        check_close(gross_margin, checked_number(metrics, "gross_margin_pct", label), label, "毛利率")
        check_close(operating_margin, checked_number(metrics, "operating_margin_pct", label), label, "经营利润率")
        check_close(net_margin, checked_number(metrics, "net_margin_pct", label), label, "净利率")

        sources = company["sources"]
        for key in ("revenue", "operating_income", "net_income"):
            source = sources[key]
            if (source["start"], source["end"]) != (period["start"], period["end"]):
                raise ValueError(f"{label} 的 {key} 与财年期间不一致")
        if sources["previous_year_revenue"]["value_usd"] != previous_revenue:
            raise ValueError(f"{label} 的前期营收与来源记录不一致")
        for fact in sources["gross_profit"]["facts"]:
            if (fact["start"], fact["end"]) != (period["start"], period["end"]):
                raise ValueError(f"{label} 的毛利润来源与财年期间不一致")

        rows.append(
            {
                "name": label,
                "color": color,
                "fiscal_year_end": period["end"],
                "revenue": revenue,
                "revenue_bn": revenue / 1_000_000_000,
                "growth": growth,
                "gross_margin": gross_margin,
                "operating_margin": operating_margin,
                "net_margin": net_margin,
            }
        )
    return rows, document["source"], document["generated_at"].split("T", 1)[0]


def axis_limit(rows: Sequence[dict[str, Any]], key: str, step: int) -> int:
    maximum = max(row[key] for row in rows)
    if minimum_negative(rows, key):
        raise ValueError(f"{key} 含负值，当前柱状图版式仅支持非负值")
    return max(step, math.ceil(maximum * 1.1 / step) * step)


def minimum_negative(rows: Sequence[dict[str, Any]], key: str) -> bool:
    return any(row[key] < 0 for row in rows)


def draw_company_bar_panel(
    draw: ImageDraw.ImageDraw,
    rows: Sequence[dict[str, Any]],
    key: str,
    bounds: tuple[int, int, int, int],
    step: int,
    suffix: str = "",
) -> None:
    left, top, right, bottom = bounds
    maximum = axis_limit(rows, key, step)
    tick_font = font(19)
    value_font = font(22, bold=True)
    label_font = font(23, bold=True)
    date_font = font(18)

    for tick in range(0, maximum + 1, step):
        y = bottom - tick / maximum * (bottom - top)
        draw.line((left, y, right, y), fill=GRID, width=2)
        draw.text((left - 18, y), str(tick), font=tick_font, fill=MUTED, anchor="rm")

    slot = (right - left) / len(rows)
    bar_width = min(82, slot * 0.52)
    for index, row in enumerate(rows):
        center_x = left + slot * (index + 0.5)
        value = row[key]
        bar_top = bottom - value / maximum * (bottom - top)
        draw.rounded_rectangle(
            (center_x - bar_width / 2, bar_top, center_x + bar_width / 2, bottom),
            radius=10,
            fill=row["color"],
        )
        centered_text(draw, center_x, bar_top - 25, f"{value:.1f}{suffix}", value_font)
        centered_text(draw, center_x, bottom + 43, row["name"], label_font)
        centered_text(draw, center_x, bottom + 80, row["fiscal_year_end"], date_font, MUTED)
    draw.line((left, bottom, right, bottom), fill="#AAB4C3", width=2)


def base_image(title: str, subtitle: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (1800, 1080), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.text((70, 52), title, font=font(50, bold=True), fill=TEXT)
    draw.text((72, 125), subtitle, font=font(24), fill=MUTED)
    draw.rounded_rectangle((45, 190, 1755, 930), radius=24, fill="#FFFFFF")
    return image, draw


def render_revenue_growth(rows: Sequence[dict[str, Any]]) -> Image.Image:
    image, draw = base_image(
        "五家公司营收与增长对比",
        "公司名下方为各自财年截止日；营收采用最近完整财年，增速按相邻完整财年计算。",
    )
    centered_text(draw, 460, 242, "营收（十亿美元）", font(28, bold=True))
    centered_text(draw, 1340, 242, "营收同比增长（%）", font(28, bold=True))
    draw_company_bar_panel(draw, rows, "revenue_bn", (125, 340, 795, 750), 200)
    draw_company_bar_panel(draw, rows, "growth", (1005, 340, 1675, 750), 20, "%")
    draw.line((900, 230, 900, 875), fill="#EDF0F4", width=2)
    return image


def render_margins(rows: Sequence[dict[str, Any]]) -> Image.Image:
    image, draw = base_image(
        "五家公司利润率对比",
        "公司名下方为各自财年截止日；三项利润率均以同一财年的营收为分母。",
    )
    legend_font = font(22)
    legend_x = (485, 835, 1220)
    for x, (_, label, color) in zip(legend_x, MARGIN_SERIES):
        draw.rounded_rectangle((x, 225, x + 30, 255), radius=5, fill=color)
        draw.text((x + 45, 240), label, font=legend_font, fill=TEXT, anchor="lm")

    left, top, right, bottom = 150, 340, 1690, 750
    maximum = axis_limit(rows, "gross_margin", 20)
    for series_key, _, _ in MARGIN_SERIES:
        maximum = max(maximum, axis_limit(rows, series_key, 20))
    tick_font = font(19)
    for tick in range(0, maximum + 1, 20):
        y = bottom - tick / maximum * (bottom - top)
        draw.line((left, y, right, y), fill=GRID, width=2)
        draw.text((left - 18, y), str(tick), font=tick_font, fill=MUTED, anchor="rm")

    slot = (right - left) / len(rows)
    bar_width = 62
    value_font = font(19, bold=True)
    label_font = font(24, bold=True)
    date_font = font(19)
    for index, row in enumerate(rows):
        group_center = left + slot * (index + 0.5)
        for series_index, (key, _, color) in enumerate(MARGIN_SERIES):
            center_x = group_center + (series_index - 1) * 76
            value = row[key]
            bar_top = bottom - value / maximum * (bottom - top)
            draw.rounded_rectangle(
                (center_x - bar_width / 2, bar_top, center_x + bar_width / 2, bottom),
                radius=8,
                fill=color,
            )
            centered_text(draw, center_x, bar_top - 22, f"{value:.1f}", value_font)
        centered_text(draw, group_center, bottom + 43, row["name"], label_font)
        centered_text(draw, group_center, bottom + 80, row["fiscal_year_end"], date_font, MUTED)
    draw.line((left, bottom, right, bottom), fill="#AAB4C3", width=2)
    return image


def add_notes(image: Image.Image, source: str, generated_date: str, margin_note: bool) -> None:
    draw = ImageDraw.Draw(image)
    draw.text(
        (70, 970),
        f"来源：{source}；数据文件生成于 {generated_date}。",
        font=font(20),
        fill=MUTED,
    )
    note = (
        "注：利润按 GAAP 口径；毛利润优先采用披露值，否则以同期间营收减成本计算；一次性项目可能影响可比性。"
        if margin_note
        else "注：金额由美元原始值换算为十亿美元；各公司财年截止日不同，横向比较时需注意期间差异。"
    )
    draw.text((70, 1010), note, font=font(20), fill=MUTED)


def save_png(image: Image.Image, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.stem}.tmp.png")
    try:
        image.save(temporary, format="PNG", optimize=True, dpi=(300, 300))
        temporary.replace(output)
    finally:
        if temporary.exists():
            temporary.unlink()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成五家公司同业对比图，并标注各公司财年截止日。")
    parser.add_argument("--input", type=Path, default=PROJECT_ROOT / "comparison.json", help="财务数据 JSON 路径。")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "output" / "figures", help="图表输出目录。")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    rows, source, generated_date = load_data(args.input)
    revenue_image = render_revenue_growth(rows)
    margin_image = render_margins(rows)
    add_notes(revenue_image, source, generated_date, margin_note=False)
    add_notes(margin_image, source, generated_date, margin_note=True)

    outputs = (
        (revenue_image, args.output_dir / "revenue_growth_comparison.png"),
        (margin_image, args.output_dir / "margin_comparison.png"),
    )
    for row in rows:
        print(
            f'{row["name"]}: FY {row["fiscal_year_end"]}; '
            f'revenue ${row["revenue_bn"]:.6f}bn; growth {row["growth"]:.6f}%; '
            f'margins {row["gross_margin"]:.6f}% / {row["operating_margin"]:.6f}% / {row["net_margin"]:.6f}%'
        )
    for image, output in outputs:
        save_png(image, output)
        print(f"Saved: {output.resolve()}")
        image.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
