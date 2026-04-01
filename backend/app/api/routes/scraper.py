"""API routes for TradingView web scraping endpoints."""

from fastapi import APIRouter, Query, HTTPException

from app.services.tradingview_service import (
    scrape_earnings_overview,
    scrape_financial_statements,
    scrape_screener,
    scrape_earnings_calendar,
    format_earnings_response,
)
from app.models.schemas import (
    EarningsOverviewResponse,
    EarningsCalendarResponse,
    FinancialStatementsScrapedResponse,
    ScraperScreenerResponse,
)

router = APIRouter()


@router.get("/scraper/earnings", response_model=EarningsOverviewResponse)
async def get_earnings_overview(
    tickers: str = Query(
        ...,
        description="Comma-separated list of tickers (e.g., 'AAPL,MSFT,GOOGL')",
    ),
    market: str = Query(default="US", pattern="^(US|JP)$"),
):
    """Scrape earnings overview data from TradingView.

    Fetches EPS, revenue, growth, valuation, and profitability metrics
    for multiple tickers at once.
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if not ticker_list:
        raise HTTPException(status_code=400, detail="No tickers provided")
    if len(ticker_list) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 tickers per request")

    try:
        raw_data = await scrape_earnings_overview(ticker_list, market=market)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Scraping failed: {str(e)}")

    formatted = [format_earnings_response(r) for r in raw_data]
    return EarningsOverviewResponse(
        total=len(formatted),
        market=market,
        stocks=formatted,
    )


@router.get("/scraper/financials/{ticker}", response_model=FinancialStatementsScrapedResponse)
async def get_scraped_financials(
    ticker: str,
    market: str = Query(default="US", pattern="^(US|JP)$"),
    period: str = Query(default="annual", pattern="^(annual|quarterly)$"),
):
    """Scrape detailed financial statements from TradingView.

    Returns income statement, balance sheet, and cash flow data
    scraped from TradingView's financials page.
    """
    try:
        data = await scrape_financial_statements(
            ticker=ticker.upper(),
            market=market,
            period=period,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Scraping failed: {str(e)}")

    return FinancialStatementsScrapedResponse(**data)


@router.get("/scraper/screener", response_model=ScraperScreenerResponse)
async def get_screener_data(
    market: str = Query(default="US", pattern="^(US|JP)$"),
    sort_by: str = Query(default="market_cap_basic"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=50, ge=1, le=200),
    sector: str = Query(default=None),
):
    """Scrape stock screener data from TradingView.

    Returns earnings and financial metrics for top stocks
    ranked by the specified criteria.
    """
    try:
        raw_data = await scrape_screener(
            market=market,
            sort_by=sort_by,
            order=order,
            limit=limit,
            sector=sector,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Scraping failed: {str(e)}")

    formatted = [format_earnings_response(r) for r in raw_data]
    return ScraperScreenerResponse(
        total=len(formatted),
        market=market,
        sort_by=sort_by,
        stocks=formatted,
    )


@router.get("/scraper/earnings-calendar", response_model=EarningsCalendarResponse)
async def get_earnings_calendar(
    market: str = Query(default="US", pattern="^(US|JP)$"),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Scrape upcoming earnings calendar from TradingView.

    Returns stocks with upcoming earnings release dates,
    including EPS forecasts and analyst data.
    """
    try:
        raw_data = await scrape_earnings_calendar(market=market, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Scraping failed: {str(e)}")

    entries = []
    for r in raw_data:
        entries.append({
            "symbol": r.get("symbol", ""),
            "name": r.get("description", r.get("name", "")),
            "sector": r.get("sector"),
            "market": r.get("market", market),
            "price": r.get("close"),
            "market_cap": r.get("market_cap_basic"),
            "next_earnings_date": r.get("earnings_release_next_date"),
            "eps_ttm": r.get("earnings_per_share_basic_ttm"),
            "eps_forecast": r.get("earnings_per_share_forecast_next_fq"),
            "num_analysts": r.get("number_of_analysts"),
            "target_price": r.get("target_price_average"),
            "recommendation": r.get("recommendation_mark"),
        })

    return EarningsCalendarResponse(
        total=len(entries),
        market=market,
        entries=entries,
    )
