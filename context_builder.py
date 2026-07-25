from schema import ReportData, PeriodValue, FinancialStatementRow

PLACEHOLDER_IMG = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4"
    "//8/AwAI/AL+p5qgoAAAAABJRU5ErkJggg=="
)
# ---------- Static broker boilerplate (same for every report, not from ReportData) ----------
STATIC_BROKER_INFO = {
    "logo_url": PLACEHOLDER_IMG,
    "broker_name": "Geojit",
    "broker_tagline": "PEOPLE YOU PROSPER WITH",
    "broker_full_name": "Geojit Investments Ltd",
    "broker_short_name": "GIL",
    "analyst_name": "Research Analyst",
    "research_support_disclaimer": (
        "CRISIL has provided research support in preparation of this research report and the "
        "investment rational contained herein along with financial forecast. The target price "
        "and recommendation provided in the report are strictly GIL's views and are NOT "
        "PROVIDED by CRISIL."
    ),
    "regulatory_disclosure_text": (
        "Group companies/ Fellow subsidiaries of Geojit Investments Ltd (GIL) are Geojit "
        "Financial Services Limited (GFSL), Geojit Technologies Private Limited (Software "
        "Solutions provider), Geojit Credits Private Limited (NBFC), Geojit Fintech Private "
        "Ltd, Geojit IFSC Ltd."
    ),
    "ai_tools_disclosure": "Neither Geojit Investments Limited nor its Analysts have utilized any AI tools in the preparation of the research reports.",
    "registered_office": "7th Floor 34/659-P, Civil Line Road, Padivattom, Kochi-682024, Kerala, India",
    "broker_phone": "+91 484-2901000",
    "website_url": "www.geojit.com",
    "investor_email": "customercare@geojit.com",
    "signature_img_url": PLACEHOLDER_IMG,
    "compliance_officer_name": "Ms. Indu K.",
    "compliance_address": "7th Floor, 34/659-P, Civil Line Road, Padivattom, Ernakulam",
    "compliance_phone": "+91 484-2901367",
    "compliance_email": "compliance@geojit.com",
    "grievances_email": "grievances@geojit.com",
    "scores_url": "www.scores.sebi.gov.in",
    "odr_url": "https://smartodr.in",
    "cin_number": "U66110KL2023PLC080586",
    "sebi_reg_no": "INH000019567",
    "dp_reg_no": "IN-DP-781-2024",
    "rating_disclaimer_text": (
        "The recommendations are based on 12 month horizon, unless otherwise specified. "
        "The investment ratings are on absolute positive/negative return basis. It is "
        "possible that due to volatile price fluctuation in the near to medium term, there "
        "could be a temporary mismatch to rating."
    ),
    "rating_criteria_rows": [
        {"rating": "Buy", "large_cap": "Upside is above 10%", "mid_cap": "Upside is above 15%", "small_cap": "Upside is above 20%"},
        {"rating": "Accumulate", "large_cap": "-", "mid_cap": "Upside is between 10%-15%", "small_cap": "Upside is between 10%-20%"},
        {"rating": "Hold", "large_cap": "Upside is between 0% - 10%", "mid_cap": "Upside is between 0%-10%", "small_cap": "Upside is between 0%-10%"},
        {"rating": "Reduce/sell", "large_cap": "Downside is more than 0%", "mid_cap": "Downside is more than 0%", "small_cap": "Downside is more than 0%"},
    ],
}

# Fields the current schema doesn't capture at all. Defaulted so template never crashes.
NOT_YET_EXTRACTED_DEFAULTS = {
    "report_tag": "Result Update",
    "target_change_dir": "flat",
    "rating_change_dir": "flat",
    "earnings_change_dir": "flat",
    "stock_type": "N/A",
    "bloomberg_code": "N/A",
    "sensex_value": "N/A",
    "nse_code": "N/A",
    "bse_code": "N/A",
    "time_frame": "12 Months",
    "est_year1": "N/A",
    "est_year2": "N/A",
    "change_in_estimates_rows": [],
}


def _lookup(values: list[PeriodValue], period: str, default="N/A"):
    """Find a PeriodValue's value by its period label, e.g. 'FY25A' or '3 Month'."""
    for pv in values:
        if pv.period == period:
            return pv.value if pv.value is not None else default
    return default


def _stmt_rows(rows: list[FinancialStatementRow]) -> list[dict]:
    """Convert FinancialStatementRow list -> template's {label, values} row shape."""
    return [
        {
            "label": r.line_item,
            "values": [pv.value if pv.value is not None else "N/A" for pv in r.values],
        }
        for r in rows
    ]


def _fin_years(rows: list[FinancialStatementRow]) -> list[str]:
    """Pull the year/period labels in order from the first row, for table headers."""
    if not rows:
        return []
    return [pv.period for pv in rows[0].values]


def _transpose_key_metrics(key_metrics) -> tuple[list[str], list[dict]]:
    """
    KeyMetricsRow is one row per year with many metric fields (sales, ebitda, ...).
    The template wants the opposite: one row per metric, with a value per year.
    This flips it.
    """
    years = [km.year for km in key_metrics]
    metric_fields = [
        ("Sales", "sales"),
        ("Growth (%)", "growth_pct"),
        ("EBITDA", "ebitda"),
        ("EBITDA Margin (%)", "ebitda_margin_pct"),
        ("PAT Adjusted", "pat_adjusted"),
        ("Growth (%)", "pat_growth_pct"),
        ("Adjusted EPS", "adjusted_eps"),
        ("Growth (%)", "eps_growth_pct"),
        ("P/E", "pe"),
        ("P/B", "pb"),
        ("EV/EBITDA", "ev_ebitda"),
        ("ROE (%)", "roe_pct"),
        ("D/E", "de_ratio"),
    ]
    rows = []
    for label, attr in metric_fields:
        values = [getattr(km, attr) if getattr(km, attr) is not None else "N/A" for km in key_metrics]
        rows.append({"label": label, "values": values, "bold": label == "Sales"})
    return years, rows


def _shareholding_context(shareholding) -> dict:
    quarters = []
    if shareholding:
        quarters = [pv.period for pv in shareholding[0].values]

    rows = []
    total_row = None
    for row in shareholding:
        entry = {
            "name": row.category,
            "values": [pv.value if pv.value is not None else "N/A" for pv in row.values],
        }
        if row.category.strip().lower() == "total":
            total_row = entry["values"]
        else:
            rows.append(entry)

    if total_row is None:
        # No explicit "Total" row extracted -> compute it ourselves.
        total_row = []
        for i in range(len(quarters)):
            col_sum = sum(r["values"][i] for r in rows if isinstance(r["values"][i], (int, float)))
            total_row.append(round(col_sum, 1))

    return {
        "shareholding_quarters": [{"label": q} for q in quarters],
        "shareholding_rows": rows,
        "shareholding_total": total_row,
        "promoter_pledge": ["N/A"] * len(quarters),  # not in schema yet
    }


def _price_performance_context(price_performance) -> dict:
    ctx = {}
    label_map = {
        "absolute return": "perf_absolute",
        "absolute sensex": "perf_sensex",
        "relative return": "perf_relative",
    }
    period_map = {"3 Month": "3m", "6 Month": "6m", "1 Year": "1y"}

    for row in price_performance:
        prefix = label_map.get(row.metric.strip().lower())
        if not prefix:
            continue
        for pv in row.values:
            suffix = period_map.get(pv.period)
            if suffix:
                ctx[f"{prefix}_{suffix}"] = pv.value if pv.value is not None else "N/A"

    # Fill any combination that wasn't found, so the template never KeyErrors
    for prefix in ("perf_absolute", "perf_sensex", "perf_relative"):
        for suffix in ("3m", "6m", "1y"):
            ctx.setdefault(f"{prefix}_{suffix}", "N/A")

    return ctx


def _quarterly_financials_context(quarterly_financials) -> list[dict]:
    rows = []
    for row in quarterly_financials:
        rows.append({
            "label": row.metric,
            "current": row.q1fy26 if row.q1fy26 is not None else "N/A",
            "yoy": row.q1fy25 if row.q1fy25 is not None else "N/A",
            "yoy_growth": row.yoy_growth_pct if row.yoy_growth_pct is not None else "N/A",
            "qoq": row.q4fy25 if row.q4fy25 is not None else "N/A",
            "qoq_growth": row.qoq_growth_pct if row.qoq_growth_pct is not None else "N/A",
            "italic": "margin" in row.metric.lower(),
        })
    return rows


def _charts_context(charts, chart_img_urls: dict) -> dict:
    """
    chart_img_urls maps chart title -> already-generated image data-uri/path.
    Until matplotlib generation is wired up, pass {} and everything falls back to placeholder.
    """
    boxes = [
        {"title": c.title, "img_url": chart_img_urls.get(c.title, PLACEHOLDER_IMG)}
        for c in charts
    ]
    return {
        "charts_row1": boxes[0:2],
        "charts_row2": boxes[2:4],
    }


def build_context(data: ReportData, chart_img_urls: dict = None) -> dict:
    chart_img_urls = chart_img_urls or {}

    context = {}
    context.update(STATIC_BROKER_INFO)
    context.update(NOT_YET_EXTRACTED_DEFAULTS)

    # Header
    context["company_name"] = data.header.company_name
    context["sector"] = data.header.sector or "N/A"
    context["report_date"] = data.header.report_date or "N/A"
    context["recommendation_rating"] = data.header.rating or "N/A"
    context["target_price"] = data.header.target_price if data.header.target_price is not None else "N/A"
    context["cmp"] = data.header.cmp if data.header.cmp is not None else "N/A"
    context["return_pct"] = data.header.return_pct if data.header.return_pct is not None else "N/A"

    # Company data
    cd = data.company_data
    context["market_cap"] = cd.market_cap_cr if cd.market_cap_cr is not None else "N/A"
    context["week52_high"] = cd.week_52_high if cd.week_52_high is not None else "N/A"
    context["week52_low"] = cd.week_52_low if cd.week_52_low is not None else "N/A"
    context["enterprise_value"] = cd.enterprise_value_cr if cd.enterprise_value_cr is not None else "N/A"
    context["outstanding_shares"] = cd.outstanding_shares_cr if cd.outstanding_shares_cr is not None else "N/A"
    context["free_float"] = cd.free_float_pct if cd.free_float_pct is not None else "N/A"
    context["dividend_yield"] = cd.dividend_yield_pct if cd.dividend_yield_pct is not None else "-"
    context["avg_volume_6m"] = "N/A"  # not in schema
    context["beta"] = cd.beta if cd.beta is not None else "N/A"
    context["face_value"] = cd.face_value if cd.face_value is not None else "N/A"

    # Shareholding + price performance
    context.update(_shareholding_context(data.shareholding))
    context.update(_price_performance_context(data.price_performance))
    context["price_chart_img_url"] = chart_img_urls.get("price_performance", PLACEHOLDER_IMG)

    # Key metrics summary table (transposed)
    summary_years, summary_rows = _transpose_key_metrics(data.key_metrics)
    context["summary_years"] = summary_years
    context["summary_financials_rows"] = summary_rows

    # Narrative
    if data.header.headline:
        context["headline"] = data.header.headline
    elif data.business_summary:
        context["headline"] = data.business_summary.split(".")[0]
    else:
        context["headline"] = "N/A"
    context["company_description"] = data.business_summary or "N/A"
    context["summary_bullets"] = data.key_bullets or []
    context["outlook_text"] = data.outlook_and_valuation or "N/A"
    context["key_highlights"] = data.key_highlights or []

    # Quarterly financials
    context["financials_basis"] = "Consolidated"
    context["q_current_label"] = "Q1FY26"  # could be derived from data if you extract period labels
    context["q_yoy_label"] = "Q1FY25"
    context["q_qoq_label"] = "Q4FY25"
    context["quarterly_financials_rows"] = _quarterly_financials_context(data.quarterly_financials)

    # Charts
    context.update(_charts_context(data.charts, chart_img_urls))

    # Full financial statements
    context["fin_years"] = _fin_years(data.profit_and_loss)
    context["pnl_rows"] = _stmt_rows(data.profit_and_loss)
    context["balance_sheet_rows"] = _stmt_rows(data.balance_sheet)
    context["cashflow_rows"] = _stmt_rows(data.cashflow)
    context["ratio_rows"] = _stmt_rows(data.ratios)  # no section headers for now

    # Recommendation history
    context["recommendation_chart_img_url"] = chart_img_urls.get("recommendation_history", PLACEHOLDER_IMG)
    context["recommendation_history"] = [
        {"date": r.date, "rating": r.rating, "target": r.target if r.target is not None else "N/A"}
        for r in data.recommendation_history
    ]

    return context