from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.stock import Stock, StockMetrics, IncomeStatement, CashFlowStatement
from app.models.schemas import (
    StockDetailResponse,
    ValuationDetail,
    ProfitabilityDetail,
    GrowthDetail,
    FinancialHealthDetail,
    CashflowDetail,
    ShareholderReturnsDetail,
    CAPMDetail,
    FinancialsResponse,
    IncomeStatementSchema,
    CashFlowStatementSchema,
    SearchResult,
)

router = APIRouter()


@router.get("/stocks/{ticker}", response_model=StockDetailResponse)
async def get_stock_detail(ticker: str, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.ticker == ticker.upper()).first()
    if not stock:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Stock not found")

    m = stock.metrics
    if not m:
        return StockDetailResponse(ticker=stock.ticker, name=stock.name)

    return StockDetailResponse(
        ticker=stock.ticker,
        name=stock.name,
        sector=stock.sector,
        industry=stock.industry,
        market=stock.market,
        exchange=stock.exchange,
        description=stock.description,
        price=m.price,
        change_pct=m.change_pct,
        market_cap=m.market_cap,
        enterprise_value=m.enterprise_value,
        score=m.score,
        valuation=ValuationDetail(per=m.per, pbr=m.pbr, psr=m.psr, ev_ebitda=m.ev_ebitda, peg=m.peg),
        profitability=ProfitabilityDetail(
            gross_margin=m.gross_margin, operating_margin=m.operating_margin,
            net_margin=m.net_margin, roe=m.roe, roa=m.roa, roic=m.roic,
        ),
        growth=GrowthDetail(
            eps_growth_1y=m.eps_growth_1y, eps_growth_3y=m.eps_growth_3y,
            eps_growth_5y=m.eps_growth_5y, rev_growth_1y=m.rev_growth_1y,
            rev_growth_3y=m.rev_growth_3y, rev_growth_5y=m.rev_growth_5y,
            fcf_growth_5y=m.fcf_growth_5y,
        ),
        financial_health=FinancialHealthDetail(
            de_ratio=m.de_ratio, current_ratio=m.current_ratio,
            quick_ratio=m.quick_ratio, interest_coverage=m.interest_coverage,
        ),
        cashflow=CashflowDetail(fcf_yield=m.fcf_yield, fcf_conversion=m.fcf_conversion, capex_ratio=m.capex_ratio),
        shareholder_returns=ShareholderReturnsDetail(
            div_yield=m.div_yield, buyback_yield=m.buyback_yield,
            total_yield=m.total_yield, share_change_pct=m.share_change_pct,
        ),
        capm=CAPMDetail(
            beta=m.beta, alpha=m.alpha, sharpe_ratio=m.sharpe_ratio,
            treynor_ratio=m.treynor_ratio, r_squared=m.r_squared,
        ),
    )


@router.get("/stocks/{ticker}/financials", response_model=FinancialsResponse)
async def get_stock_financials(
    ticker: str,
    years: int = Query(default=5, ge=1, le=10),
    period: str = Query(default="annual"),
    db: Session = Depends(get_db),
):
    income = (
        db.query(IncomeStatement)
        .filter(IncomeStatement.ticker == ticker.upper())
        .order_by(IncomeStatement.fiscal_year.desc())
        .limit(years)
        .all()
    )
    cashflow = (
        db.query(CashFlowStatement)
        .filter(CashFlowStatement.ticker == ticker.upper())
        .order_by(CashFlowStatement.fiscal_year.desc())
        .limit(years)
        .all()
    )

    return FinancialsResponse(
        ticker=ticker.upper(),
        income_statements=[
            IncomeStatementSchema(
                year=i.fiscal_year, revenue=i.revenue, gross_profit=i.gross_profit,
                operating_income=i.operating_income, net_income=i.net_income,
                eps=i.eps, eps_diluted=i.eps_diluted,
            )
            for i in income
        ],
        cash_flow_statements=[
            CashFlowStatementSchema(
                year=c.fiscal_year, operating_cash_flow=c.operating_cash_flow,
                capex=c.capex, free_cash_flow=c.free_cash_flow,
                dividends_paid=c.dividends_paid, buybacks=c.buybacks,
            )
            for c in cashflow
        ],
    )


@router.get("/search", response_model=list[SearchResult])
async def search_stocks(
    q: str = Query(..., min_length=1),
    market: str = Query(default="US"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    results = (
        db.query(Stock)
        .filter(
            Stock.market == market,
            (Stock.ticker.ilike(f"%{q}%")) | (Stock.name.ilike(f"%{q}%")),
        )
        .limit(limit)
        .all()
    )
    return [
        SearchResult(ticker=s.ticker, name=s.name, sector=s.sector, market=s.market)
        for s in results
    ]
