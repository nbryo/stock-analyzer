from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    ticker = Column(String, primary_key=True)
    name = Column(String)
    sector = Column(String)
    industry = Column(String)
    market = Column(String)  # "US" or "JP"
    exchange = Column(String)
    description = Column(Text)
    last_updated = Column(DateTime)

    metrics = relationship("StockMetrics", back_populates="stock", uselist=False)
    income_statements = relationship("IncomeStatement", back_populates="stock")
    cash_flow_statements = relationship("CashFlowStatement", back_populates="stock")
    price_history = relationship("PriceHistory", back_populates="stock")


class StockMetrics(Base):
    __tablename__ = "stock_metrics"

    ticker = Column(String, ForeignKey("stocks.ticker"), primary_key=True)
    price = Column(Float)
    change_pct = Column(Float)
    market_cap = Column(Float)
    enterprise_value = Column(Float)
    # Valuation
    per = Column(Float)
    pbr = Column(Float)
    psr = Column(Float)
    ev_ebitda = Column(Float)
    peg = Column(Float)
    # Profitability
    gross_margin = Column(Float)
    operating_margin = Column(Float)
    net_margin = Column(Float)
    roe = Column(Float)
    roa = Column(Float)
    roic = Column(Float)
    # Growth
    eps = Column(Float)
    eps_growth_1y = Column(Float)
    eps_growth_3y = Column(Float)
    eps_growth_5y = Column(Float)
    rev_growth_1y = Column(Float)
    rev_growth_3y = Column(Float)
    rev_growth_5y = Column(Float)
    fcf_growth_5y = Column(Float)
    # Cash flow
    fcf_yield = Column(Float)
    fcf_conversion = Column(Float)
    capex_ratio = Column(Float)
    # Financial health
    de_ratio = Column(Float)
    current_ratio = Column(Float)
    quick_ratio = Column(Float)
    interest_coverage = Column(Float)
    # Shareholder returns
    div_yield = Column(Float)
    buyback_yield = Column(Float)
    total_yield = Column(Float)
    share_change_pct = Column(Float)
    # CAPM
    beta = Column(Float)
    alpha = Column(Float)
    sharpe_ratio = Column(Float)
    treynor_ratio = Column(Float)
    r_squared = Column(Float)
    volatility = Column(Float)
    # Score
    score = Column(Integer)
    score_updated = Column(DateTime)

    stock = relationship("Stock", back_populates="metrics")


class IncomeStatement(Base):
    __tablename__ = "income_statements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, ForeignKey("stocks.ticker"))
    fiscal_year = Column(Integer)
    period = Column(String)  # "annual" or "Q1/Q2/Q3/Q4"
    revenue = Column(Float)
    gross_profit = Column(Float)
    operating_income = Column(Float)
    net_income = Column(Float)
    eps = Column(Float)
    eps_diluted = Column(Float)

    stock = relationship("Stock", back_populates="income_statements")


class CashFlowStatement(Base):
    __tablename__ = "cash_flow_statements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, ForeignKey("stocks.ticker"))
    fiscal_year = Column(Integer)
    operating_cash_flow = Column(Float)
    capex = Column(Float)
    free_cash_flow = Column(Float)
    dividends_paid = Column(Float)
    buybacks = Column(Float)

    stock = relationship("Stock", back_populates="cash_flow_statements")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, ForeignKey("stocks.ticker"))
    date = Column(Date)
    close = Column(Float)
    volume = Column(Float)
    interval = Column(String)  # "daily"/"weekly"

    stock = relationship("Stock", back_populates="price_history")
