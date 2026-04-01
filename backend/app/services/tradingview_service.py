"""TradingView web scraping service for earnings and financial data.

Scrapes financial statements (income statement, balance sheet, cash flow)
from TradingView for both US and Japanese stocks.
"""

import logging
from typing import Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# TradingView scanner API endpoints
SCANNER_URLS = {
    "US": "https://scanner.tradingview.com/america/scan",
    "JP": "https://scanner.tradingview.com/japan/scan",
}

TRADINGVIEW_BASE = "https://www.tradingview.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.tradingview.com",
    "Referer": "https://www.tradingview.com/",
}

# Financial columns available via TradingView scanner API
EARNINGS_COLUMNS = [
    # Identification
    "name",
    "description",
    "sector",
    "industry",
    "exchange",
    "currency",
    # Price
    "close",
    "change",
    "change_abs",
    "volume",
    "market_cap_basic",
    # Earnings / Income Statement
    "earnings_per_share_basic_ttm",
    "earnings_per_share_diluted_ttm",
    "earnings_per_share_forecast_next_fq",
    "revenue_per_share_ttm",
    "total_revenue_ttm",
    "gross_profit_ttm",
    "net_income_ttm",
    "operating_income_ttm",
    "ebitda_ttm",
    # Growth
    "revenue_growth_quarterly_yoy",
    "earnings_per_share_growth_quarterly_yoy",
    "revenue_growth_ttm_yoy",
    "earnings_per_share_growth_ttm_yoy",
    # Valuation
    "price_earnings_ttm",
    "price_book_ratio",
    "price_sales_ratio",
    "enterprise_value_ebitda_ttm",
    "price_earnings_growth_ttm",
    # Profitability
    "return_on_equity",
    "return_on_assets",
    "return_on_invested_capital",
    "gross_margin_ttm",
    "operating_margin_ttm",
    "net_margin_ttm",
    # Cash Flow
    "free_cash_flow_ttm",
    "cash_f_operating_activities_ttm",
    "capital_expenditure_ttm",
    # Financial Health
    "total_debt_to_equity",
    "current_ratio",
    "quick_ratio",
    # Dividends
    "dividend_yield_recent",
    "dividends_per_share_fq",
    "dps_common_stock_prim_issue_fy",
    # Earnings Calendar
    "earnings_release_date",
    "earnings_release_next_date",
    # Analysts
    "number_of_analysts",
    "target_price_average",
    "recommendation_mark",
]

# Financial statement columns for detailed view
INCOME_STATEMENT_COLUMNS = [
    "total_revenue",
    "cost_of_goods_sold",
    "gross_profit",
    "operating_income",
    "pretax_income",
    "net_income",
    "basic_eps",
    "diluted_eps",
    "ebitda",
]

BALANCE_SHEET_COLUMNS = [
    "total_assets",
    "total_liabilities",
    "total_equity",
    "total_debt",
    "total_current_assets",
    "total_current_liabilities",
    "cash_n_short_term_invest",
]

CASH_FLOW_COLUMNS = [
    "cash_f_operating_activities",
    "capital_expenditure",
    "free_cash_flow",
    "cash_f_investing_activities",
    "cash_f_financing_activities",
    "dividends_paid",
    "common_stock_repurchased",
]


def _build_exchange_prefix(ticker: str, market: str) -> str:
    """Build TradingView symbol with exchange prefix."""
    if market == "JP":
        # Japanese stocks: TSE:7203 format
        clean = ticker.replace(".T", "")
        return f"TSE:{clean}"
    # US stocks: use ticker directly (TradingView resolves exchange)
    return ticker.upper()


async def scrape_earnings_overview(
    tickers: list[str],
    market: str = "US",
) -> list[dict]:
    """Scrape earnings overview data from TradingView scanner API.

    Uses TradingView's public scanner API to fetch financial metrics
    for multiple tickers at once.

    Args:
        tickers: List of ticker symbols.
        market: "US" or "JP".

    Returns:
        List of dicts with earnings data for each ticker.
    """
    scanner_url = SCANNER_URLS.get(market, SCANNER_URLS["US"])

    symbols = [_build_exchange_prefix(t, market) for t in tickers]

    payload = {
        "symbols": {"tickers": symbols},
        "columns": EARNINGS_COLUMNS,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(scanner_url, json=payload, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("data", []):
        symbol = item.get("s", "")
        values = item.get("d", [])

        if len(values) != len(EARNINGS_COLUMNS):
            logger.warning(f"Column mismatch for {symbol}")
            continue

        row = dict(zip(EARNINGS_COLUMNS, values))
        row["symbol"] = symbol
        row["market"] = market
        results.append(row)

    logger.info(f"Scraped earnings for {len(results)}/{len(tickers)} tickers ({market})")
    return results


async def scrape_financial_statements(
    ticker: str,
    market: str = "US",
    period: str = "annual",
) -> dict:
    """Scrape detailed financial statements from TradingView.

    Fetches income statement, balance sheet, and cash flow data
    by scraping TradingView's financials page.

    Args:
        ticker: Ticker symbol (e.g., "AAPL" or "7203.T").
        market: "US" or "JP".
        period: "annual" or "quarterly".

    Returns:
        Dict with income_statement, balance_sheet, cash_flow data.
    """
    symbol = _build_exchange_prefix(ticker, market)
    # TradingView URL format: /symbols/NASDAQ-AAPL/financials-income-statement/
    symbol_slug = symbol.replace(":", "-")

    result = {
        "ticker": ticker,
        "market": market,
        "period": period,
        "income_statement": [],
        "balance_sheet": [],
        "cash_flow": [],
    }

    pages = {
        "income_statement": f"{TRADINGVIEW_BASE}/symbols/{symbol_slug}/financials-income-statement/",
        "balance_sheet": f"{TRADINGVIEW_BASE}/symbols/{symbol_slug}/financials-balance-sheet/",
        "cash_flow": f"{TRADINGVIEW_BASE}/symbols/{symbol_slug}/financials-cash-flow/",
    }

    if period == "quarterly":
        pages = {k: v + "?selected=quarterly" for k, v in pages.items()}

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for section, url in pages.items():
            try:
                resp = await client.get(url, headers={
                    **HEADERS,
                    "Accept": "text/html,application/xhtml+xml",
                })
                resp.raise_for_status()
                parsed = _parse_financials_html(resp.text, section)
                result[section] = parsed
            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error scraping {section} for {ticker}: {e}")
            except Exception as e:
                logger.warning(f"Error scraping {section} for {ticker}: {e}")

    return result


def _parse_financials_html(html: str, section: str) -> list[dict]:
    """Parse TradingView financials page HTML to extract table data."""
    soup = BeautifulSoup(html, "lxml")
    rows = []

    # TradingView renders financial data in structured div elements
    # Look for financial table containers
    tables = soup.find_all("table")
    if not tables:
        # Try structured div-based layout
        return _parse_financials_divs(soup, section)

    for table in tables:
        thead = table.find("thead")
        tbody = table.find("tbody")
        if not thead or not tbody:
            continue

        # Extract column headers (fiscal years/quarters)
        headers = []
        for th in thead.find_all(["th", "td"]):
            text = th.get_text(strip=True)
            if text:
                headers.append(text)

        # Extract row data
        for tr in tbody.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if len(cells) < 2:
                continue

            metric_name = cells[0].get_text(strip=True)
            values = {}
            for i, cell in enumerate(cells[1:], 1):
                if i < len(headers):
                    val = _parse_financial_value(cell.get_text(strip=True))
                    values[headers[i]] = val

            if metric_name and values:
                rows.append({"metric": metric_name, "values": values})

    return rows


def _parse_financials_divs(soup: BeautifulSoup, section: str) -> list[dict]:
    """Parse div-based financial data layout from TradingView."""
    rows = []

    # Look for data-role or data-name attributes commonly used by TradingView
    containers = soup.find_all("div", attrs={"data-name": True})
    if not containers:
        # Fallback: look for text content that matches financial metrics
        containers = soup.find_all("div", class_=lambda c: c and "container" in c.lower()) if soup else []

    # Extract script-embedded JSON data (TradingView often embeds data in scripts)
    scripts = soup.find_all("script")
    for script in scripts:
        text = script.string or ""
        if "financials" in text.lower() and "income" in text.lower():
            parsed = _extract_json_from_script(text, section)
            if parsed:
                return parsed

    return rows


def _extract_json_from_script(script_text: str, section: str) -> list[dict]:
    """Try to extract financial data from embedded script tags."""
    import json
    import re

    rows = []
    # Look for JSON-like data structures in the script
    json_patterns = re.findall(r'\{[^{}]{100,}\}', script_text)
    for pattern in json_patterns[:5]:  # Limit to prevent excessive parsing
        try:
            data = json.loads(pattern)
            if isinstance(data, dict) and any(
                k in str(data).lower()
                for k in ["revenue", "income", "earnings", "cash_flow"]
            ):
                rows.append(data)
        except (json.JSONDecodeError, ValueError):
            continue

    return rows


def _parse_financial_value(text: str) -> Optional[float]:
    """Parse a financial value string into a float."""
    if not text or text in ("-", "—", "N/A", ""):
        return None

    text = text.replace(",", "").replace(" ", "").strip()

    multiplier = 1.0
    if text.endswith("T"):
        multiplier = 1e12
        text = text[:-1]
    elif text.endswith("B"):
        multiplier = 1e9
        text = text[:-1]
    elif text.endswith("M"):
        multiplier = 1e6
        text = text[:-1]
    elif text.endswith("K"):
        multiplier = 1e3
        text = text[:-1]
    elif text.endswith("%"):
        text = text[:-1]
        try:
            return float(text) / 100.0
        except ValueError:
            return None

    try:
        return float(text) * multiplier
    except ValueError:
        return None


async def scrape_screener(
    market: str = "US",
    sort_by: str = "market_cap_basic",
    order: str = "desc",
    limit: int = 50,
    sector: Optional[str] = None,
) -> list[dict]:
    """Scrape stock screener data from TradingView.

    Uses the TradingView scanner API for bulk stock screening.

    Args:
        market: "US" or "JP".
        sort_by: Column to sort by.
        order: "asc" or "desc".
        limit: Maximum number of results.
        sector: Optional sector filter.

    Returns:
        List of dicts with screener data.
    """
    scanner_url = SCANNER_URLS.get(market, SCANNER_URLS["US"])

    payload = {
        "columns": EARNINGS_COLUMNS,
        "sort": {
            "sortBy": sort_by,
            "sortOrder": order,
        },
        "range": [0, limit],
        "markets": ["america"] if market == "US" else ["japan"],
    }

    # Add sector filter if specified
    if sector:
        payload["filter"] = [
            {"left": "sector", "operation": "equal", "right": sector}
        ]

    # Filter to common stocks only
    payload.setdefault("filter", [])
    payload["filter"].append(
        {"left": "type", "operation": "equal", "right": "stock"}
    )
    payload["filter"].append(
        {"left": "is_primary", "operation": "equal", "right": True}
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(scanner_url, json=payload, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("data", []):
        symbol = item.get("s", "")
        values = item.get("d", [])

        if len(values) != len(EARNINGS_COLUMNS):
            continue

        row = dict(zip(EARNINGS_COLUMNS, values))
        row["symbol"] = symbol
        row["market"] = market
        results.append(row)

    logger.info(f"Scraped screener: {len(results)} stocks ({market})")
    return results


async def scrape_earnings_calendar(
    market: str = "US",
    limit: int = 50,
) -> list[dict]:
    """Scrape upcoming earnings calendar from TradingView.

    Returns stocks with upcoming earnings release dates.

    Args:
        market: "US" or "JP".
        limit: Maximum number of results.

    Returns:
        List of dicts with earnings calendar data.
    """
    scanner_url = SCANNER_URLS.get(market, SCANNER_URLS["US"])

    columns = [
        "name",
        "description",
        "sector",
        "close",
        "market_cap_basic",
        "earnings_release_next_date",
        "earnings_per_share_basic_ttm",
        "earnings_per_share_forecast_next_fq",
        "number_of_analysts",
        "target_price_average",
        "recommendation_mark",
    ]

    payload = {
        "columns": columns,
        "sort": {
            "sortBy": "earnings_release_next_date",
            "sortOrder": "asc",
        },
        "range": [0, limit],
        "markets": ["america"] if market == "US" else ["japan"],
        "filter": [
            {"left": "type", "operation": "equal", "right": "stock"},
            {"left": "is_primary", "operation": "equal", "right": True},
            {"left": "earnings_release_next_date", "operation": "nempty"},
        ],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(scanner_url, json=payload, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("data", []):
        symbol = item.get("s", "")
        values = item.get("d", [])

        if len(values) != len(columns):
            continue

        row = dict(zip(columns, values))
        row["symbol"] = symbol
        row["market"] = market
        results.append(row)

    logger.info(f"Scraped earnings calendar: {len(results)} entries ({market})")
    return results


def format_earnings_response(raw: dict) -> dict:
    """Format raw TradingView data into a clean earnings response."""
    return {
        "symbol": raw.get("symbol", ""),
        "name": raw.get("description", raw.get("name", "")),
        "sector": raw.get("sector"),
        "market": raw.get("market", "US"),
        "price": raw.get("close"),
        "change_pct": raw.get("change"),
        "market_cap": raw.get("market_cap_basic"),
        "earnings": {
            "eps_ttm": raw.get("earnings_per_share_basic_ttm"),
            "eps_diluted_ttm": raw.get("earnings_per_share_diluted_ttm"),
            "eps_forecast_next_fq": raw.get("earnings_per_share_forecast_next_fq"),
            "eps_growth_yoy": raw.get("earnings_per_share_growth_ttm_yoy"),
            "eps_growth_quarterly_yoy": raw.get("earnings_per_share_growth_quarterly_yoy"),
            "next_earnings_date": raw.get("earnings_release_next_date"),
            "last_earnings_date": raw.get("earnings_release_date"),
        },
        "income": {
            "revenue_ttm": raw.get("total_revenue_ttm"),
            "revenue_per_share_ttm": raw.get("revenue_per_share_ttm"),
            "gross_profit_ttm": raw.get("gross_profit_ttm"),
            "operating_income_ttm": raw.get("operating_income_ttm"),
            "net_income_ttm": raw.get("net_income_ttm"),
            "ebitda_ttm": raw.get("ebitda_ttm"),
            "revenue_growth_yoy": raw.get("revenue_growth_ttm_yoy"),
            "revenue_growth_quarterly_yoy": raw.get("revenue_growth_quarterly_yoy"),
        },
        "valuation": {
            "per": raw.get("price_earnings_ttm"),
            "pbr": raw.get("price_book_ratio"),
            "psr": raw.get("price_sales_ratio"),
            "ev_ebitda": raw.get("enterprise_value_ebitda_ttm"),
            "peg": raw.get("price_earnings_growth_ttm"),
        },
        "profitability": {
            "roe": raw.get("return_on_equity"),
            "roa": raw.get("return_on_assets"),
            "roic": raw.get("return_on_invested_capital"),
            "gross_margin": raw.get("gross_margin_ttm"),
            "operating_margin": raw.get("operating_margin_ttm"),
            "net_margin": raw.get("net_margin_ttm"),
        },
        "cash_flow": {
            "fcf_ttm": raw.get("free_cash_flow_ttm"),
            "operating_cf_ttm": raw.get("cash_f_operating_activities_ttm"),
            "capex_ttm": raw.get("capital_expenditure_ttm"),
        },
        "financial_health": {
            "de_ratio": raw.get("total_debt_to_equity"),
            "current_ratio": raw.get("current_ratio"),
            "quick_ratio": raw.get("quick_ratio"),
        },
        "dividends": {
            "yield": raw.get("dividend_yield_recent"),
            "dps_fq": raw.get("dividends_per_share_fq"),
            "dps_fy": raw.get("dps_common_stock_prim_issue_fy"),
        },
        "analyst": {
            "num_analysts": raw.get("number_of_analysts"),
            "target_price_avg": raw.get("target_price_average"),
            "recommendation": raw.get("recommendation_mark"),
        },
    }
