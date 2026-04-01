"""Fetch initial US stock data from FMP and save to SQLite/PostgreSQL.

Usage: python scripts/fetch_initial_data.py
Run from the backend/ directory with venv activated.
"""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal, Base
from app.models.stock import Stock, StockMetrics, IncomeStatement, CashFlowStatement
from app.services import fmp_service

# Top 100 US stocks by market cap (hardcoded since screener endpoint requires paid plan)
TOP_100_TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "BRK-B", "LLY", "AVGO", "TSM",
    "JPM", "TSLA", "WMT", "V", "UNH", "MA", "XOM", "ORCL", "COST", "PG",
    "JNJ", "HD", "NFLX", "ABBV", "BAC", "CRM", "CVX", "MRK", "KO", "AMD",
    "TMUS", "PEP", "LIN", "TMO", "ACN", "ADBE", "MCD", "CSCO", "ABT", "IBM",
    "WFC", "PM", "GE", "ISRG", "NOW", "DHR", "CAT", "QCOM", "INTU", "TXN",
    "GS", "AMGN", "VZ", "BKNG", "AXP", "BLK", "SPGI", "MS", "PFE", "RTX",
    "UBER", "NEE", "LOW", "T", "HON", "AMAT", "SYK", "UNP", "COP", "DE",
    "PLD", "BA", "SCHW", "ELV", "CB", "BSX", "LMT", "VRTX", "ADP", "MDLZ",
    "ADI", "GILD", "SBUX", "MMC", "PANW", "BMY", "FI", "CI", "SO", "MO",
    "CME", "LRCX", "DUK", "ICE", "CL", "ZTS", "MCK", "WM", "REGN", "SHW",
]


def calc_score(m: dict) -> int:
    """Calculate stock score (0-100) based on fundamentals."""
    score = 50
    peg = m.get("peg")
    per = m.get("per")
    roic = m.get("roic")
    roe = m.get("roe")
    eps_growth = m.get("eps_growth_5y")
    rev_growth = m.get("rev_growth_5y")
    fcf_yield = m.get("fcf_yield")
    alpha = m.get("alpha")

    if peg is not None:
        if peg < 1.0: score += 15
        elif peg < 2.0: score += 8
    if per is not None:
        if per < 15: score += 10
        elif per < 25: score += 5
        elif per > 50: score -= 10
    if roic is not None:
        if roic > 25: score += 10
        elif roic > 15: score += 5
    if roe is not None:
        if roe > 20: score += 10
        elif roe > 12: score += 5
    if eps_growth is not None:
        if eps_growth > 20: score += 10
        elif eps_growth > 10: score += 5
    if rev_growth is not None:
        if rev_growth > 15: score += 10
        elif rev_growth > 8: score += 5
    if fcf_yield is not None:
        if fcf_yield > 6: score += 10
        elif fcf_yield > 3: score += 5
    if alpha is not None:
        if alpha > 5: score += 15
        elif alpha > 2: score += 8
        elif alpha < -5: score -= 10

    return max(0, min(100, round(score)))


async def fetch_and_save():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        total = len(TOP_100_TICKERS)
        success = 0
        errors = []

        for i, ticker in enumerate(TOP_100_TICKERS):
            print(f"[{i+1}/{total}] {ticker}...", end=" ", flush=True)

            # Skip if already in DB with metrics
            existing = db.query(StockMetrics).filter(StockMetrics.ticker == ticker).first()
            if existing and existing.price:
                print("SKIP (already in DB)")
                success += 1
                continue

            try:
                profile = await fmp_service.get_company_profile(ticker)
                time.sleep(1.0)

                ratios = await fmp_service.get_ratios_ttm(ticker)
                time.sleep(1.0)

                income_stmts = await fmp_service.get_income_statements(ticker, limit=5)
                time.sleep(1.0)

                cf_stmts = await fmp_service.get_cash_flow_statements(ticker, limit=5)
                time.sleep(1.0)

                if not profile:
                    print("SKIP (no profile)")
                    errors.append(ticker)
                    continue

                # -- Stock --
                stock = db.query(Stock).filter(Stock.ticker == ticker).first()
                if not stock:
                    stock = Stock(ticker=ticker)
                    db.add(stock)

                stock.name = profile.get("companyName")
                stock.sector = profile.get("sector")
                stock.industry = profile.get("industry")
                stock.market = "US"
                stock.exchange = profile.get("exchangeShortName")
                stock.description = (profile.get("description") or "")[:2000]

                # -- StockMetrics --
                metrics = db.query(StockMetrics).filter(StockMetrics.ticker == ticker).first()
                if not metrics:
                    metrics = StockMetrics(ticker=ticker)
                    db.add(metrics)

                metrics.price = profile.get("price")
                metrics.change_pct = profile.get("changes")
                metrics.market_cap = profile.get("mktCap")

                if ratios:
                    metrics.per = ratios.get("peRatioTTM")
                    metrics.pbr = ratios.get("priceToBookRatioTTM")
                    metrics.psr = ratios.get("priceToSalesRatioTTM")
                    metrics.ev_ebitda = ratios.get("enterpriseValueOverEBITDATTM")
                    metrics.peg = ratios.get("pegRatioTTM")
                    metrics.gross_margin = ratios.get("grossProfitMarginTTM")
                    metrics.operating_margin = ratios.get("operatingProfitMarginTTM")
                    metrics.net_margin = ratios.get("netProfitMarginTTM")
                    metrics.roe = ratios.get("returnOnEquityTTM")
                    metrics.roa = ratios.get("returnOnAssetsTTM")
                    metrics.roic = ratios.get("returnOnCapitalEmployedTTM")
                    metrics.div_yield = ratios.get("dividendYielPercentageTTM")
                    metrics.de_ratio = ratios.get("debtEquityRatioTTM")
                    metrics.current_ratio = ratios.get("currentRatioTTM")
                    metrics.interest_coverage = ratios.get("interestCoverageTTM")
                    metrics.fcf_yield = ratios.get("freeCashFlowYieldTTM")

                metrics.eps = profile.get("eps") if profile.get("eps") else None
                metrics.score = calc_score({
                    "peg": metrics.peg, "per": metrics.per, "roic": metrics.roic,
                    "roe": metrics.roe, "eps_growth_5y": metrics.eps_growth_5y,
                    "rev_growth_5y": metrics.rev_growth_5y, "fcf_yield": metrics.fcf_yield,
                    "alpha": metrics.alpha,
                })

                # -- Income Statements --
                for stmt in income_stmts:
                    year = stmt.get("calendarYear")
                    if not year:
                        continue
                    year = int(year)
                    existing = (
                        db.query(IncomeStatement)
                        .filter(IncomeStatement.ticker == ticker, IncomeStatement.fiscal_year == year)
                        .first()
                    )
                    if not existing:
                        db.add(IncomeStatement(
                            ticker=ticker, fiscal_year=year, period="annual",
                            revenue=stmt.get("revenue"), gross_profit=stmt.get("grossProfit"),
                            operating_income=stmt.get("operatingIncome"),
                            net_income=stmt.get("netIncome"),
                            eps=stmt.get("eps"), eps_diluted=stmt.get("epsdiluted"),
                        ))

                # -- Cash Flow Statements --
                for stmt in cf_stmts:
                    year = stmt.get("calendarYear")
                    if not year:
                        continue
                    year = int(year)
                    existing = (
                        db.query(CashFlowStatement)
                        .filter(CashFlowStatement.ticker == ticker, CashFlowStatement.fiscal_year == year)
                        .first()
                    )
                    if not existing:
                        db.add(CashFlowStatement(
                            ticker=ticker, fiscal_year=year,
                            operating_cash_flow=stmt.get("operatingCashFlow"),
                            capex=stmt.get("capitalExpenditure"),
                            free_cash_flow=stmt.get("freeCashFlow"),
                            dividends_paid=stmt.get("dividendsPaid"),
                            buybacks=stmt.get("commonStockRepurchased"),
                        ))

                success += 1
                print("OK")

            except Exception as e:
                print(f"ERROR: {e}")
                errors.append(ticker)

            if (i + 1) % 10 == 0:
                db.commit()
                print(f"  --- Committed {i+1}/{total} ---")

        db.commit()
        print(f"\nDone! {success}/{total} stocks saved. Errors: {errors or 'none'}")

    except Exception as e:
        db.rollback()
        print(f"FATAL ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(fetch_and_save())
