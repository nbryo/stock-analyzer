import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://financialmodelingprep.com"
TIMEOUT = 30.0


async def _get(url: str, params: dict | None = None) -> dict | list | None:
    params = params or {}
    params["apikey"] = settings.FMP_API_KEY
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.TimeoutException:
        logger.error("FMP API timeout: %s", url)
        return None
    except httpx.HTTPStatusError as e:
        logger.error("FMP API error %s: %s", e.response.status_code, url)
        return None
    except Exception as e:
        logger.error("FMP API unexpected error: %s", e)
        return None


async def get_company_profile(ticker: str) -> Optional[dict]:
    """Get company basic info via /stable/profile."""
    result = await _get(f"{BASE_URL}/stable/profile", params={"symbol": ticker})
    if isinstance(result, list) and result:
        return result[0]
    return None


async def get_ratios_ttm(ticker: str) -> Optional[dict]:
    """Get TTM financial ratios (PER, PBR, ROE, ROIC, etc.)."""
    result = await _get(f"{BASE_URL}/stable/ratios-ttm", params={"symbol": ticker})
    if isinstance(result, list) and result:
        return result[0]
    return None


async def get_income_statements(ticker: str, limit: int = 5) -> list[dict]:
    """Get income statements (up to 5 years)."""
    result = await _get(
        f"{BASE_URL}/stable/income-statement",
        params={"symbol": ticker, "period": "annual", "limit": limit},
    )
    return result if isinstance(result, list) else []


async def get_cash_flow_statements(ticker: str, limit: int = 5) -> list[dict]:
    """Get cash flow statements (up to 5 years)."""
    result = await _get(
        f"{BASE_URL}/stable/cash-flow-statement",
        params={"symbol": ticker, "period": "annual", "limit": limit},
    )
    return result if isinstance(result, list) else []


async def get_price_history(
    ticker: str,
    from_date: str = "",
    to_date: str = "",
) -> list[dict]:
    """Get historical daily prices via /stable/historical-price-eod/full."""
    params: dict = {"symbol": ticker}
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    result = await _get(f"{BASE_URL}/stable/historical-price-eod/full", params)
    return result if isinstance(result, list) else []
