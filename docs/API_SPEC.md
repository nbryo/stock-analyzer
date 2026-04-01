# API仕様書 — 株式ファンダメンタル分析バックエンド

## Base URL
- 開発: `http://localhost:8000`
- 本番: `https://stock-analyzer-api.railway.app`（予定）

---

## エンドポイント一覧

### 1. スクリーナー

#### `GET /api/v1/screener`
銘柄スクリーニング＆ランキング取得

**Query Parameters:**
| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| market | string | "US" | "US" or "JP" |
| sort_by | string | "score" | score/per/peg/fcf_yield/roic/eps_growth/alpha |
| order | string | "desc" | desc/asc |
| min_market_cap | float | 1000 | 最小時価総額（USD億, JPY百億）|
| sector | string | null | セクターフィルター |
| min_score | int | 0 | 最小スコア |
| page | int | 1 | ページ番号 |
| per_page | int | 50 | 1ページあたり件数 |

**Response:**
```json
{
  "total": 1000,
  "page": 1,
  "per_page": 50,
  "stocks": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "sector": "Technology",
      "market": "US",
      "price": 189.50,
      "change_pct": 0.64,
      "market_cap": 2950000000000,
      "score": 82,
      "per": 28.4,
      "pbr": 45.2,
      "peg": 2.1,
      "eps": 6.43,
      "eps_growth_5y": 12.3,
      "rev_growth_5y": 8.1,
      "fcf_yield": 4.2,
      "roic": 54.2,
      "roe": 160.1,
      "div_yield": 0.5,
      "beta": 1.24,
      "alpha": 3.2,
      "sharpe": 1.45
    }
  ]
}
```

---

### 2. 銘柄詳細

#### `GET /api/v1/stocks/{ticker}`
銘柄の全指標詳細取得

**Response:**
```json
{
  "ticker": "AAPL",
  "name": "Apple Inc.",
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "market": "US",
  "exchange": "NASDAQ",
  "description": "...",
  "price": 189.50,
  "change": 1.21,
  "change_pct": 0.64,
  "market_cap": 2950000000000,
  "enterprise_value": 2980000000000,
  "score": 82,

  "valuation": {
    "per": 28.4,
    "pbr": 45.2,
    "psr": 7.8,
    "ev_ebitda": 22.1,
    "peg": 2.1
  },

  "profitability": {
    "gross_margin": 44.1,
    "operating_margin": 29.8,
    "net_margin": 25.3,
    "roe": 160.1,
    "roa": 28.3,
    "roic": 54.2
  },

  "growth": {
    "eps_growth_1y": 8.2,
    "eps_growth_3y": 10.5,
    "eps_growth_5y": 12.3,
    "rev_growth_1y": 2.8,
    "rev_growth_3y": 7.4,
    "rev_growth_5y": 8.1,
    "fcf_growth_5y": 9.3
  },

  "financial_health": {
    "de_ratio": 1.87,
    "current_ratio": 0.99,
    "quick_ratio": 0.97,
    "interest_coverage": 40.2
  },

  "cashflow": {
    "fcf_yield": 4.2,
    "fcf_conversion": 103.1,
    "capex_ratio": 2.8
  },

  "shareholder_returns": {
    "div_yield": 0.5,
    "buyback_yield": 3.1,
    "total_yield": 3.6,
    "share_change_pct": -3.1
  },

  "capm": {
    "beta": 1.24,
    "alpha": 3.2,
    "expected_return": 10.8,
    "actual_return_1y": 14.0,
    "sharpe_ratio": 1.45,
    "treynor_ratio": 8.32,
    "r_squared": 0.72
  }
}
```

---

### 3. 財務諸表

#### `GET /api/v1/stocks/{ticker}/financials`
過去5年間の財務諸表データ

**Query Parameters:**
| パラメータ | 型 | デフォルト |
|-----------|-----|-----------|
| years | int | 5 |
| period | string | "annual" | annual/quarter |

**Response:**
```json
{
  "ticker": "AAPL",
  "income_statements": [
    {
      "year": 2024,
      "revenue": 391035000000,
      "gross_profit": 172350000000,
      "operating_income": 123216000000,
      "net_income": 97290000000,
      "eps": 6.43,
      "eps_diluted": 6.42
    }
  ],
  "balance_sheets": [
    {
      "year": 2024,
      "total_assets": 364480000000,
      "total_equity": 56950000000,
      "total_debt": 101304000000,
      "cash": 29965000000
    }
  ],
  "cash_flow_statements": [
    {
      "year": 2024,
      "operating_cash_flow": 118254000000,
      "capex": -9447000000,
      "free_cash_flow": 108807000000,
      "dividends_paid": -15025000000,
      "buybacks": -95023000000
    }
  ]
}
```

---

### 4. 株価履歴

#### `GET /api/v1/stocks/{ticker}/prices`
株価履歴（CAPM計算用）

**Query Parameters:**
| パラメータ | 型 | デフォルト |
|-----------|-----|-----------|
| period | string | "1y" | 1m/3m/6m/1y/3y/5y |
| interval | string | "weekly" | daily/weekly/monthly |

**Response:**
```json
{
  "ticker": "AAPL",
  "prices": [
    {"date": "2024-01-05", "open": 184.85, "high": 185.41, "low": 183.17, "close": 185.21, "volume": 58056200}
  ]
}
```

---

### 5. CAPM分析

#### `GET /api/v1/capm/{ticker}`
個別銘柄のCAPM詳細分析

**Response:**
```json
{
  "ticker": "AAPL",
  "market_index": "SPY",
  "risk_free_rate": 4.35,
  "market_return_1y": 24.2,
  "beta": 1.24,
  "alpha": 3.2,
  "expected_return_capm": 10.8,
  "actual_return_1y": 14.0,
  "residual_return": 3.2,
  "sharpe_ratio": 1.45,
  "treynor_ratio": 8.32,
  "information_ratio": 1.12,
  "r_squared": 0.72,
  "volatility_annualized": 24.8,
  "max_drawdown": -12.4,
  "regression_data": {
    "weekly_returns_stock": [...],
    "weekly_returns_market": [...],
    "dates": [...]
  }
}
```

---

### 6. セクター比較

#### `GET /api/v1/sectors`
セクター別集計データ

**Response:**
```json
{
  "sectors": [
    {
      "name": "Technology",
      "stock_count": 142,
      "avg_per": 31.2,
      "avg_roic": 28.4,
      "avg_eps_growth": 18.3,
      "avg_score": 72,
      "top_stocks": ["NVDA", "MSFT", "META"]
    }
  ]
}
```

---

### 7. 検索

#### `GET /api/v1/search`
ティッカー・銘柄名で検索

**Query Parameters:**
| パラメータ | 型 |
|-----------|-----|
| q | string |
| market | string |
| limit | int |

---

## データモデル（SQLAlchemy）

```python
# models/stock.py

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

class StockMetrics(Base):
    __tablename__ = "stock_metrics"
    ticker = Column(String, ForeignKey("stocks.ticker"), primary_key=True)
    price = Column(Float)
    market_cap = Column(Float)
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
    eps_growth_5y = Column(Float)
    rev_growth_5y = Column(Float)
    # CAPM
    beta = Column(Float)
    alpha = Column(Float)
    sharpe_ratio = Column(Float)
    # Score
    score = Column(Integer)
    score_updated = Column(DateTime)

class IncomeStatement(Base):
    __tablename__ = "income_statements"
    id = Column(Integer, primary_key=True)
    ticker = Column(String, ForeignKey("stocks.ticker"))
    fiscal_year = Column(Integer)
    period = Column(String)  # "annual" or "Q1/Q2/Q3/Q4"
    revenue = Column(Float)
    gross_profit = Column(Float)
    operating_income = Column(Float)
    net_income = Column(Float)
    eps = Column(Float)
    eps_diluted = Column(Float)

class CashFlowStatement(Base):
    __tablename__ = "cash_flow_statements"
    id = Column(Integer, primary_key=True)
    ticker = Column(String, ForeignKey("stocks.ticker"))
    fiscal_year = Column(Integer)
    operating_cash_flow = Column(Float)
    capex = Column(Float)
    free_cash_flow = Column(Float)
    dividends_paid = Column(Float)
    buybacks = Column(Float)

class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True)
    ticker = Column(String, ForeignKey("stocks.ticker"))
    date = Column(Date)
    close = Column(Float)
    volume = Column(Float)
    interval = Column(String)  # "daily"/"weekly"
```

---

## 環境変数（.env）

```env
# APIs
FMP_API_KEY=your_fmp_key
JQUANTS_EMAIL=your_email
JQUANTS_PASSWORD=your_password

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/stockanalyzer
REDIS_URL=redis://localhost:6379

# App
APP_ENV=development
API_KEY=your_internal_api_key  # Flutter→バックエンド認証用
```

---

## データ更新スケジュール

| データ | 更新頻度 | 方法 |
|--------|---------|------|
| 株価 | 日次（平日） | Cronジョブ |
| 財務諸表 | 四半期ごと | 決算発表後 |
| CAPM指標 | 週次（月曜） | 週次Cronジョブ |
| スコア | 週次 | 指標更新後に再計算 |
