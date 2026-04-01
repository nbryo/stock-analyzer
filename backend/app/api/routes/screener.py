import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, asc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.stock import Stock, StockMetrics
from app.models.schemas import ScreenerResponse, StockScreenerItem

logger = logging.getLogger(__name__)
router = APIRouter()

# Sort column mapping
SORT_COLUMNS = {
    "score": StockMetrics.score,
    "per": StockMetrics.per,
    "peg": StockMetrics.peg,
    "fcf_yield": StockMetrics.fcf_yield,
    "roic": StockMetrics.roic,
    "eps_growth": StockMetrics.eps_growth_5y,
    "alpha": StockMetrics.alpha,
}


def _get_redis():
    """Get Redis client, return None if unavailable."""
    try:
        import redis
        return redis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception:
        return None


@router.get("/screener", response_model=ScreenerResponse)
async def screener(
    market: str = Query(default="US", pattern="^(US|JP)$"),
    sort_by: str = Query(default="score"),
    order: str = Query(default="desc", pattern="^(desc|asc)$"),
    sector: Optional[str] = Query(default=None),
    min_score: int = Query(default=0, ge=0),
    min_market_cap: float = Query(default=1000),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    # Redis cache key
    cache_key = f"screener:{market}:{sort_by}:{order}:{sector}:{min_score}:{min_market_cap}:{page}:{per_page}"
    r = _get_redis()

    # Check cache
    if r:
        try:
            cached = r.get(cache_key)
            if cached:
                return ScreenerResponse(**json.loads(cached))
        except Exception:
            pass

    # Build query
    query = (
        db.query(Stock, StockMetrics)
        .join(StockMetrics, Stock.ticker == StockMetrics.ticker)
        .filter(Stock.market == market)
    )

    if sector:
        query = query.filter(Stock.sector == sector)
    if min_score > 0:
        query = query.filter(StockMetrics.score >= min_score)

    # Sort
    sort_col = SORT_COLUMNS.get(sort_by, StockMetrics.score)
    if order == "desc":
        query = query.order_by(desc(sort_col).nulls_last())
    else:
        query = query.order_by(asc(sort_col).nulls_last())

    # Count
    total = query.count()

    # Paginate
    offset = (page - 1) * per_page
    results = query.offset(offset).limit(per_page).all()

    stocks = [
        StockScreenerItem(
            ticker=stock.ticker,
            name=stock.name,
            sector=stock.sector,
            market=stock.market,
            price=m.price,
            change_pct=m.change_pct,
            market_cap=m.market_cap,
            score=m.score,
            per=m.per,
            pbr=m.pbr,
            peg=m.peg,
            eps=m.eps,
            eps_growth_5y=m.eps_growth_5y,
            rev_growth_5y=m.rev_growth_5y,
            fcf_yield=m.fcf_yield,
            roic=m.roic,
            roe=m.roe,
            div_yield=m.div_yield,
            beta=m.beta,
            alpha=m.alpha,
            sharpe=m.sharpe_ratio,
        )
        for stock, m in results
    ]

    response = ScreenerResponse(
        total=total,
        page=page,
        per_page=per_page,
        stocks=stocks,
    )

    # Save to cache (TTL: 1 hour)
    if r:
        try:
            r.setex(cache_key, 3600, response.model_dump_json())
        except Exception:
            pass

    return response
