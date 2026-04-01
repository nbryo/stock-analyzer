"""Fetch initial US stock data using yfinance (free, no API key needed).

Usage: python scripts/fetch_initial_data.py
Run from the backend/ directory.
"""

import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yfinance as yf
from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal, Base
from app.models.stock import Stock, StockMetrics, IncomeStatement, CashFlowStatement

logger = logging.getLogger(__name__)

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


def _safe(val):
    """Return None if val is NaN/None, else the value."""
    try:
        import math
        if val is None:
            return None
        if isinstance(val, float) and math.isnan(val):
            return None
        return val
    except Exception:
        return None


def calc_score(m: dict) -> int:
    score = 50
    peg = m.get("peg")
    per = m.get("per")
    roic = m.get("roic")
    roe = m.get("roe")
    fcf_yield = m.get("fcf_yield")

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
    if fcf_yield is not None:
        if fcf_yield > 6: score += 10
        elif fcf_yield > 3: score += 5
    return max(0, min(100, round(score)))


async def fetch_and_save(log_list=None):
    """Fetch yfinance data for top 100 US stocks and save to DB."""
    def log(msg):
        logger.info(msg)
        print(msg, flush=True)
        if log_list is not None:
            log_list.append(msg)

    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    success = 0
    errors = []

    try:
        total = len(TOP_100_TICKERS)
        for i, ticker in enumerate(TOP_100_TICKERS):
            log(f"[{i+1}/{total}] {ticker}...")

            # Skip if already saved
            existing = db.query(StockMetrics).filter(StockMetrics.ticker == ticker).first()
            if existing and existing.price:
                log(f"  SKIP (already in DB)")
                success += 1
                continue

            try:
                # yfinance is sync — run in thread executor to avoid blocking
                loop = asyncio.get_event_loop()
                t = await loop.run_in_executor(None, lambda tk=ticker: yf.Ticker(tk))
                info = await loop.run_in_executor(None, lambda: t.info)

                if not info or info.get("trailingPegRatio") is None and info.get("currentPrice") is None and info.get("regularMarketPrice") is None:
                    # Try to see if we at least got a symbol back
                    if not info or not info.get("symbol"):
                        log(f"  SKIP (no data)")
                        errors.append(ticker)
                        continue

                # -- Stock --
                stock = db.query(Stock).filter(Stock.ticker == ticker).first()
                if not stock:
                    stock = Stock(ticker=ticker)
                    db.add(stock)
                stock.name = info.get("longName") or info.get("shortName")
                stock.sector = info.get("sector")
                stock.industry = info.get("industry")
                stock.market = "US"
                stock.exchange = info.get("exchange")
                stock.description = (info.get("longBusinessSummary") or "")[:2000]

                # -- StockMetrics --
                metrics = db.query(StockMetrics).filter(StockMetrics.ticker == ticker).first()
                if not metrics:
                    metrics = StockMetrics(ticker=ticker)
                    db.add(metrics)

                price = _safe(info.get("currentPrice") or info.get("regularMarketPrice"))
                metrics.price = price
                metrics.change_pct = _safe(info.get("regularMarketChangePercent"))
                metrics.market_cap = _safe(info.get("marketCap"))
                metrics.per = _safe(info.get("trailingPE"))
                metrics.pbr = _safe(info.get("priceToBook"))
                metrics.psr = _safe(info.get("priceToSalesTrailing12Months"))
                metrics.ev_ebitda = _safe(info.get("enterpriseToEbitda"))
                metrics.peg = _safe(info.get("trailingPegRatio") or info.get("pegRatio"))
                metrics.gross_margin = _safe(info.get("grossMargins"))
                metrics.operating_margin = _safe(info.get("operatingMargins"))
                metrics.net_margin = _safe(info.get("profitMargins"))
                metrics.roe = _safe(info.get("returnOnEquity"))
                metrics.roa = _safe(info.get("returnOnAssets"))
                metrics.div_yield = _safe(info.get("dividendYield"))
                metrics.de_ratio = _safe(info.get("debtToEquity"))
                metrics.current_ratio = _safe(info.get("currentRatio"))
                metrics.eps = _safe(info.get("trailingEps"))

                # FCF yield = free cash flow / market cap
                fcf = _safe(info.get("freeCashflow"))
                mktcap = metrics.market_cap
                if fcf and mktcap and mktcap > 0:
                    metrics.fcf_yield = round(fcf / mktcap * 100, 2)

                metrics.score = calc_score({
                    "peg": metrics.peg, "per": metrics.per,
                    "roic": metrics.roic, "roe": metrics.roe,
                    "fcf_yield": metrics.fcf_yield,
                })

                # -- Income Statements (annual) --
                try:
                    fin = await loop.run_in_executor(None, lambda: t.financials)
                    if fin is not None and not fin.empty:
                        for col in fin.columns[:5]:  # last 5 years
                            year = col.year
                            ex = db.query(IncomeStatement).filter(
                                IncomeStatement.ticker == ticker,
                                IncomeStatement.fiscal_year == year
                            ).first()
                            if not ex:
                                def _g(df, row):
                                    try: return _safe(float(df.loc[row, col]))
                                    except: return None
                                db.add(IncomeStatement(
                                    ticker=ticker, fiscal_year=year, period="annual",
                                    revenue=_g(fin, "Total Revenue"),
                                    gross_profit=_g(fin, "Gross Profit"),
                                    operating_income=_g(fin, "Operating Income"),
                                    net_income=_g(fin, "Net Income"),
                                    eps=_safe(info.get("trailingEps")),
                                ))
                except Exception as fe:
                    log(f"  income stmt warn: {fe}")

                # -- Cash Flow Statements --
                try:
                    cf = await loop.run_in_executor(None, lambda: t.cashflow)
                    if cf is not None and not cf.empty:
                        for col in cf.columns[:5]:
                            year = col.year
                            ex = db.query(CashFlowStatement).filter(
                                CashFlowStatement.ticker == ticker,
                                CashFlowStatement.fiscal_year == year
                            ).first()
                            if not ex:
                                def _gc(df, row):
                                    try: return _safe(float(df.loc[row, col]))
                                    except: return None
                                db.add(CashFlowStatement(
                                    ticker=ticker, fiscal_year=year,
                                    operating_cash_flow=_gc(cf, "Operating Cash Flow"),
                                    capex=_gc(cf, "Capital Expenditure"),
                                    free_cash_flow=_gc(cf, "Free Cash Flow"),
                                ))
                except Exception as ce:
                    log(f"  cashflow warn: {ce}")

                success += 1
                log(f"  OK (price={price})")

            except Exception as e:
                log(f"  ERROR: {e}")
                errors.append(ticker)

            # Commit every 10 tickers
            if (i + 1) % 10 == 0:
                db.commit()
                log(f"--- committed {i+1}/{total} ---")

            # Small yield to keep event loop responsive
            await asyncio.sleep(0.1)

        db.commit()
        msg = f"Done! {success}/{total} saved. Errors ({len(errors)}): {errors[:10]}"
        log(msg)
        return {"success": success, "total": total, "errors": errors}

    except Exception as e:
        db.rollback()
        log(f"FATAL: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(fetch_and_save())
