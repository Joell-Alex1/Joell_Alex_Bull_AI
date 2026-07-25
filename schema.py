from pydantic import BaseModel
from typing import Optional


class HeaderInfo(BaseModel):
    company_name: str
    headline: Optional[str] = None        # short one-line takeaway, e.g. "Blinkit propels growth; valuation limits upside"
    sector: Optional[str] = None
    report_date: Optional[str] = None
    rating: Optional[str] = None          # e.g. "HOLD", "BUY"
    target_price: Optional[float] = None
    cmp: Optional[float] = None           # current market price
    return_pct: Optional[float] = None


class CompanyData(BaseModel):
    market_cap_cr: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    enterprise_value_cr: Optional[float] = None
    outstanding_shares_cr: Optional[float] = None
    free_float_pct: Optional[float] = None
    dividend_yield_pct: Optional[float] = None
    beta: Optional[float] = None
    face_value: Optional[float] = None


class PeriodValue(BaseModel):
    period: str              # e.g. "Q3FY25", "3 Month", "FY23A"
    value: Optional[float] = None


class ShareholdingRow(BaseModel):
    category: str             # "Promoters", "FIIs", "MFs/Institutions", etc.
    values: list[PeriodValue]


class PricePerformanceRow(BaseModel):
    metric: str                # "Absolute Return", "Absolute Sensex", "Relative Return"
    values: list[PeriodValue]


class KeyMetricsRow(BaseModel):
    year: str                  # "FY25A", "FY26E", "FY27E"
    sales: Optional[float] = None
    growth_pct: Optional[float] = None
    ebitda: Optional[float] = None
    ebitda_margin_pct: Optional[float] = None
    pat_adjusted: Optional[float] = None
    pat_growth_pct: Optional[float] = None
    adjusted_eps: Optional[float] = None
    eps_growth_pct: Optional[float] = None
    pe: Optional[float] = None
    pb: Optional[float] = None
    ev_ebitda: Optional[float] = None
    roe_pct: Optional[float] = None
    de_ratio: Optional[float] = None


class QuarterlyFinancialRow(BaseModel):
    """One line item of a quarterly results comparison table.

    Field names are deliberately period-agnostic (current/prior_year/prior_quarter)
    rather than hardcoded fiscal-quarter labels like "q1fy26" -- a fixed label
    only matches whichever company's reporting calendar it was modeled on, and
    silently mismaps every other company's actual current quarter into the wrong
    column. Each *_period field carries its own label (e.g. "Q2FY26") so the
    template can render the real column headers instead of assuming one.
    """
    metric: str                            # "Sales", "EBITDA", "Margin (%)", etc.
    current_period: Optional[str] = None   # e.g. "Q2FY26" -- the document's own latest reported quarter
    current_value: Optional[float] = None
    prior_year_period: Optional[str] = None    # e.g. "Q2FY25" -- same quarter, prior year
    prior_year_value: Optional[float] = None
    yoy_growth_pct: Optional[float] = None
    prior_quarter_period: Optional[str] = None  # e.g. "Q1FY26" -- immediately preceding quarter
    prior_quarter_value: Optional[float] = None
    qoq_growth_pct: Optional[float] = None


class ChartData(BaseModel):
    title: str                 # "Revenue", "Gross Order Value", "EBITDA", "PAT"
    categories: list[str]      # x-axis labels e.g. ["Q2FY24", "Q3FY24", ...]
    bar_values: list[float]
    line_values: Optional[list[float]] = None   # e.g. margin/growth % line overlay


class FinancialStatementRow(BaseModel):
    line_item: str
    values: list[PeriodValue]   # e.g. [{"period": "FY23A", "value": 7079}, ...]


class RecommendationRow(BaseModel):
    date: str
    rating: str
    target: Optional[float] = None


class ReportData(BaseModel):
    header: HeaderInfo
    company_data: CompanyData
    shareholding: list[ShareholdingRow]
    price_performance: list[PricePerformanceRow]
    key_metrics: list[KeyMetricsRow]
    quarterly_financials: list[QuarterlyFinancialRow]
    business_summary: str
    key_bullets: list[str]
    outlook_and_valuation: str
    key_highlights: list[str]
    charts: list[ChartData]
    profit_and_loss: list[FinancialStatementRow]
    balance_sheet: list[FinancialStatementRow]
    cashflow: list[FinancialStatementRow]
    ratios: list[FinancialStatementRow]
    recommendation_history: list[RecommendationRow]