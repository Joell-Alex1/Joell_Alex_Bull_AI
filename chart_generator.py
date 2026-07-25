"""
Renders report charts as PNG data-URIs (base64) so they can be embedded
directly in the Jinja/WeasyPrint HTML without needing static file serving.

Colors and mark specs follow the project's dataviz skill: single-hue bars for
single-series magnitude charts, the skill's pre-validated 3-slot categorical
triple (blue/orange/aqua) for the multi-series price-performance chart, and
direct value labels instead of a second y-axis -- a dual-axis bar+line combo
(as in the original Geojit sample) is the #1 flagged anti-pattern, so growth/
margin figures are shown as direct labels above each bar instead.
"""
import base64
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# Report brand teal (matches report_template.html --teal-dark) used as the
# single hue for single-series magnitude charts.
TEAL = "#0b5c59"
TEAL_LIGHT = "#bfe0dc"

# Pre-validated 3-series categorical triple from the dataviz skill's reference
# palette (references/palette.md) -- these three clear all-pairs CVD checks in
# both light and dark mode, so no separate validator run is needed here.
CATEGORICAL_3 = ["#2a78d6", "#eb6834", "#1baf7a"]  # blue, orange, aqua

INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans", "Helvetica"],
    "axes.edgecolor": BASELINE,
    "axes.linewidth": 0.8,
    "text.color": INK_PRIMARY,
    "axes.labelcolor": INK_SECONDARY,
    "xtick.color": INK_SECONDARY,
    "ytick.color": INK_SECONDARY,
})


def _fig_to_data_uri(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", pad_inches=0.12, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _fmt_value(v: float) -> str:
    if v == int(v):
        return f"{int(v):,}"
    return f"{v:,.1f}"


def render_metric_bar_chart(title: str, categories: list, bar_values: list, line_values: list = None) -> str:
    """Single-series magnitude bar chart (Revenue, GOV, EBITDA, PAT, ...).

    bar_values are the metric itself (Rs cr); line_values, if present, is a
    parallel growth/margin % series shown as a direct label above each bar
    rather than a second y-axis (see module docstring).
    """
    if not categories or not bar_values:
        return None

    fig, ax = plt.subplots(figsize=(4.4, 2.6))

    x = range(len(categories))
    bar_width = 0.56
    bars = ax.bar(x, bar_values, width=bar_width, color=TEAL, zorder=3)

    ax.set_xticks(list(x))
    ax.set_xticklabels(categories, fontsize=8)
    ax.tick_params(axis="both", length=0, labelsize=8)

    ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=4))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.grid(axis="y", color=GRIDLINE, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)

    for spine_name in ("top", "right", "left"):
        ax.spines[spine_name].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)

    # headroom on BOTH sides of zero so labels never sit clipped against the
    # axes edge or overlap the bar fill -- a bar can dip below zero (e.g.
    # EBITDA loss quarters), and its label needs room to sit below it too.
    data_max = max(bar_values)
    data_min = min(0, min(bar_values))
    span = (data_max - data_min) or abs(data_max) or 1
    top_pad = span * 0.30
    bottom_pad = span * 0.16 if data_min < 0 else 0
    ax.set_ylim(data_min - bottom_pad, data_max + top_pad)

    label_gap = span * 0.03
    growth_gap = span * 0.12

    for i, (bar, val) in enumerate(zip(bars, bar_values)):
        height = bar.get_height()
        # Below the bar (and further from zero) when negative, above it when
        # positive -- otherwise the label lands inside the fill and reads as
        # near-illegible dark-on-teal text instead of dark-on-white.
        va = "bottom" if height >= 0 else "top"
        value_y = height + label_gap if height >= 0 else height - label_gap
        growth_y = height + growth_gap if height >= 0 else height - growth_gap

        ax.text(
            bar.get_x() + bar.get_width() / 2, value_y,
            _fmt_value(val), ha="center", va=va, fontsize=7.5, color=INK_PRIMARY, fontweight="bold",
        )
        if line_values and i < len(line_values) and line_values[i] is not None:
            growth = line_values[i]
            sign = "+" if growth > 0 else ""
            ax.text(
                bar.get_x() + bar.get_width() / 2, growth_y,
                f"{sign}{growth:.1f}%", ha="center", va=va, fontsize=7, color=INK_SECONDARY,
            )

    fig.tight_layout(pad=0.4)
    return _fig_to_data_uri(fig)


def render_price_performance_chart(perf_rows: list) -> str:
    """Grouped bar chart: Absolute Return / Absolute Sensex / Relative Return across 3M/6M/1Y.

    perf_rows: list of {"metric": str, "values": [{"period": str, "value": float}, ...]}
    (i.e. the raw ReportData.price_performance rows).
    """
    periods = ["3 Month", "6 Month", "1 Year"]
    series = []
    for row in perf_rows or []:
        by_period = {pv.period: pv.value for pv in row.values}
        vals = [by_period.get(p) for p in periods]
        if any(v is not None for v in vals):
            series.append((row.metric, [v if v is not None else 0 for v in vals]))

    if not series:
        return None

    fig, ax = plt.subplots(figsize=(4.4, 2.6))
    n_series = len(series)
    group_width = 0.72
    bar_width = group_width / n_series
    x = list(range(len(periods)))

    for i, (label, vals) in enumerate(series):
        offset = (i - (n_series - 1) / 2) * bar_width
        positions = [xi + offset for xi in x]
        ax.bar(positions, vals, width=bar_width * 0.9, label=label,
               color=CATEGORICAL_3[i % len(CATEGORICAL_3)], zorder=3)

    ax.axhline(0, color=BASELINE, linewidth=0.8, zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels(periods, fontsize=8)
    ax.tick_params(axis="both", length=0, labelsize=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.grid(axis="y", color=GRIDLINE, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)

    for spine_name in ("top", "right", "left"):
        ax.spines[spine_name].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)

    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=n_series,
              frameon=False, fontsize=7.5, handlelength=1.0, handleheight=1.0)

    fig.tight_layout(pad=0.4)
    return _fig_to_data_uri(fig)


def render_recommendation_chart(recommendation_history: list) -> str:
    """Single-series step/line chart of target price over time (no legend needed: one series)."""
    rows = [r for r in (recommendation_history or []) if r.target is not None]
    if len(rows) < 2:
        return None

    labels = [r.date for r in rows]
    values = [r.target for r in rows]
    x = range(len(labels))

    fig, ax = plt.subplots(figsize=(6.2, 2.6))
    ax.plot(x, values, color=TEAL, linewidth=2, marker="o", markersize=5,
            markerfacecolor=TEAL, markeredgecolor="white", markeredgewidth=1, zorder=3)

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=7.5, rotation=30, ha="right")
    ax.tick_params(axis="both", length=0, labelsize=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.grid(axis="y", color=GRIDLINE, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)

    for spine_name in ("top", "right", "left"):
        ax.spines[spine_name].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)

    # direct end-label on the final point (the one series the story is about)
    ax.annotate(
        _fmt_value(values[-1]), xy=(x[-1], values[-1]), xytext=(6, 0),
        textcoords="offset points", va="center", fontsize=8, fontweight="bold", color=INK_PRIMARY,
    )

    fig.tight_layout(pad=0.4)
    return _fig_to_data_uri(fig)


def build_chart_img_urls(data) -> dict:
    """Given a ReportData instance, render every chart and return {title: data_uri}.

    Titles match what context_builder._charts_context looks up: the four
    ChartData.title values (e.g. "Revenue", "EBITDA"), plus the fixed keys
    "price_performance" and "recommendation_history".
    """
    chart_img_urls = {}

    for chart in data.charts or []:
        uri = render_metric_bar_chart(chart.title, chart.categories, chart.bar_values, chart.line_values)
        if uri:
            chart_img_urls[chart.title] = uri

    perf_uri = render_price_performance_chart(data.price_performance)
    if perf_uri:
        chart_img_urls["price_performance"] = perf_uri

    rec_uri = render_recommendation_chart(data.recommendation_history)
    if rec_uri:
        chart_img_urls["recommendation_history"] = rec_uri

    return chart_img_urls
