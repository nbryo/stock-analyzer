from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# --- Screener ---
class StockScreenerItem(BaseModel):
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    market: str = "US"
    price: Optional[float] = None
    change_pct: Optional[float] = None
    market_cap: Optional[float] = None
    score: Optional[int] = None
    per: Optional[float] = None
    pbr: Optional[float] = None
    peg: Optional[float] = None
    eps: Optional[float] = None
    eps_growth_5y: Optional[float] = None
    rev_growth_5y: Optional[float] = None
    fcf_yield: Optional[float] = None
    roic: Optional[float] = None
    roe: Optional[float] = None
    div_yield: Optional[float] = None
    beta: Optional[float] = None
    alpha: Optional[float] = None
    sharpe: Optional[float] = None

    model_config = {"from_attributes": True}


class ScreenerResponse(BaseModel):
    total: int
    page: int
    per_page: int
    stocks: list[StockScreenerItem]


# --- Stock Detail ---
class ValuationDetail(BaseModel):
    per: Optional[float] = None
    pbr: Optional[float] = None
    psr: Optional[float] = None
    ev_ebitda: Optional[float] = None
    peg: Optional[float] = None


class ProfitabilityDetail(BaseModel):
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    roic: Optional[float] = None


class GrowthDetail(BaseModel):
    eps_growth_1y: Optional[float] = None
    eps_growth_3y: Optional[float] = None
    eps_growth_5y: Optional[float] = None
    rev_growth_1y: Optional[float] = None
    rev_growth_3y: Optional[float] = None
    rev_growth_5y: Optional[float] = None
    fcf_growth_5y: Optional[float] = None


class FinancialHealthDetail(BaseModel):
    de_ratio: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    interest_coverage: Optional[float] = None


class CashflowDetail(BaseModel):
    fcf_yield: Optional[float] = None
    fcf_conversion: Optional[float] = None
    capex_ratio: Optional[float] = None


class ShareholderReturnsDetail(BaseModel):
    div_yield: Optional[float] = None
    buyback_yield: Optional[float] = None
    total_yield: Optional[float] = None
    share_change_pct: Optional[float] = None


class CAPMDetail(BaseModel):
    beta: Optional[float] = None
    alpha: Optional[float] = None
    expected_return: Optional[float] = None
    actual_return_1y: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    treynor_ratio: Optional[float] = None
    r_squared: Optional[float] = None


class StockDetailResponse(BaseModel):
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market: str = "US"
    exchange: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    score: Optional[int] = None
    valuation: ValuationDetail = ValuationDetail()
    profitability: ProfitabilityDetail = ProfitabilityDetail()
    growth: GrowthDetail = GrowthDetail()
    financial_health: FinancialHealthDetail = FinancialHealthDetail()
    cashflow: CashflowDetail = CashflowDetail()
    shareholder_returns: ShareholderReturnsDetail = ShareholderReturnsDetail()
    capm: CAPMDetail = CAPMDetail()

    model_config = {"from_attributes": True}


# --- Financials ---
class IncomeStatementSchema(BaseModel):
    year: int
    revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    eps: Optional[float] = None
    eps_diluted: Optional[float] = None


class CashFlowStatementSchema(BaseModel):
    year: int
    operating_cash_flow: Optional[float] = None
    capex: Optional[float] = None
    free_cash_flow: Optional[float] = None
    dividends_paid: Optional[float] = None
    buybacks: Optional[float] = None


class FinancialsResponse(BaseModel):
    ticker: str
    income_statements: list[IncomeStatementSchema]
    cash_flow_statements: list[CashFlowStatementSchema]


# --- Price History ---
class PricePoint(BaseModel):
    date: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None


class PriceHistoryResponse(BaseModel):
    ticker: str
    prices: list[PricePoint]


# --- CAPM ---
class CAPMResponse(BaseModel):
    ticker: str
    market_index: str = "SPY"
    risk_free_rate: Optional[float] = None
    market_return_1y: Optional[float] = None
    beta: Optional[float] = None
    alpha: Optional[float] = None
    expected_return_capm: Optional[float] = None
    actual_return_1y: Optional[float] = None
    residual_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    treynor_ratio: Optional[float] = None
    information_ratio: Optional[float] = None
    r_squared: Optional[float] = None
    volatility_annualized: Optional[float] = None
    max_drawdown: Optional[float] = None
    regression_data: Optional[dict] = None


# --- Sectors ---
class SectorSummary(BaseModel):
    name: str
    stock_count: int
    avg_per: Optional[float] = None
    avg_roic: Optional[float] = None
    avg_eps_growth: Optional[float] = None
    avg_score: Optional[float] = None
    top_stocks: list[str] = []


class SectorsResponse(BaseModel):
    sectors: list[SectorSummary]


# --- Search ---
class SearchResult(BaseModel):
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    market: str = "US"


# --- Scraper (TradingView) ---
class EarningsData(BaseModel):
    eps_ttm: Optional[float] = None
    eps_diluted_ttm: Optional[float] = None
    eps_forecast_next_fq: Optional[float] = None
    eps_growth_yoy: Optional[float] = None
    eps_growth_quarterly_yoy: Optional[float] = None
    next_earnings_date: Optional[float] = None
    last_earnings_date: Optional[float] = None


class IncomeData(BaseModel):
    revenue_ttm: Optional[float] = None
    revenue_per_share_ttm: Optional[float] = None
    gross_profit_ttm: Optional[float] = None
    operating_income_ttm: Optional[float] = None
    net_income_ttm: Optional[float] = None
    ebitda_ttm: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None
    revenue_growth_quarterly_yoy: Optional[float] = None


class ValuationScraped(BaseModel):
    per: Optional[float] = None
    pbr: Optional[float] = None
    psr: Optional[float] = None
    ev_ebitda: Optional[float] = None
    peg: Optional[float] = None


class ProfitabilityScraped(BaseModel):
    roe: Optional[float] = None
    roa: Optional[float] = None
    roic: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None


class CashFlowScraped(BaseModel):
    fcf_ttm: Optional[float] = None
    operating_cf_ttm: Optional[float] = None
    capex_ttm: Optional[float] = None


class FinancialHealthScraped(BaseModel):
    de_ratio: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None


class DividendData(BaseModel):
    yield_: Optional[float] = None

    model_config = {"populate_by_name": True}


class AnalystData(BaseModel):
    num_analysts: Optional[float] = None
    target_price_avg: Optional[float] = None
    recommendation: Optional[float] = None


class EarningsStockItem(BaseModel):
    symbol: str
    name: Optional[str] = None
    sector: Optional[str] = None
    market: str = "US"
    price: Optional[float] = None
    change_pct: Optional[float] = None
    market_cap: Optional[float] = None
    earnings: EarningsData = EarningsData()
    income: IncomeData = IncomeData()
    valuation: ValuationScraped = ValuationScraped()
    profitability: ProfitabilityScraped = ProfitabilityScraped()
    cash_flow: CashFlowScraped = CashFlowScraped()
    financial_health: FinancialHealthScraped = FinancialHealthScraped()
    dividends: Optional[dict] = None
    analyst: AnalystData = AnalystData()


class EarningsOverviewResponse(BaseModel):
    total: int
    market: str
    stocks: list[EarningsStockItem]


class FinancialStatementsScrapedResponse(BaseModel):
    ticker: str
    market: str = "US"
    period: str = "annual"
    income_statement: list[dict] = []
    balance_sheet: list[dict] = []
    cash_flow: list[dict] = []


class EarningsCalendarEntry(BaseModel):
    symbol: str
    name: Optional[str] = None
    sector: Optional[str] = None
    market: str = "US"
    price: Optional[float] = None
    market_cap: Optional[float] = None
    next_earnings_date: Optional[float] = None
    eps_ttm: Optional[float] = None
    eps_forecast: Optional[float] = None
    num_analysts: Optional[float] = None
    target_price: Optional[float] = None
    recommendation: Optional[float] = None


class EarningsCalendarResponse(BaseModel):
    total: int
    market: str
    entries: list[EarningsCalendarEntry]


class ScraperScreenerResponse(BaseModel):
    total: int
    market: str
    sort_by: str
    stocks: list[EarningsStockItem]
