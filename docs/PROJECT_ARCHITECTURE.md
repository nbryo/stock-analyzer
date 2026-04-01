# 株式ファンダメンタル分析アプリ — 全体設計書

## プロジェクト概要
- **対象銘柄**: 米国株1000銘柄 + 日本株1000銘柄
- **分析手法**: ファンダメンタル分析 + CAPM理論
- **プラットフォーム**: Android / iOS（Flutter）
- **バックエンド**: Python（FastAPI）

---

## システム全体構成

```
┌─────────────────────────────────────────────────────────┐
│                   Flutter Mobile App                     │
│         (Android + iOS / Dart)                          │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS / REST API
┌──────────────────────▼──────────────────────────────────┐
│              Python FastAPI Backend                      │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│   │  Screener    │  │    CAPM      │  │  Fundamental │ │
│   │  Service     │  │   Service    │  │   Service    │ │
│   └──────────────┘  └──────────────┘  └──────────────┘ │
│   ┌──────────────────────────────────────────────────┐  │
│   │              Cache Layer (Redis)                 │  │
│   └──────────────────────────────────────────────────┘  │
│   ┌──────────────────────────────────────────────────┐  │
│   │              PostgreSQL Database                  │  │
│   └──────────────────────────────────────────────────┘  │
└────────┬─────────────────────────┬───────────────────────┘
         │                         │
┌────────▼──────────┐   ┌──────────▼──────────┐
│   FMP API         │   │   J-Quants API       │
│  (米国株1000)     │   │  (日本株1000)        │
└───────────────────┘   └─────────────────────┘
```

---

## データソース

| ソース | 対象 | 取得データ |
|--------|------|-----------|
| Financial Modeling Prep (FMP) | 米国株1000銘柄 | 株価・財務諸表・比率・スクリーナー |
| J-Quants API | 日本株1000銘柄 | 株価・財務諸表・指標 |
| FMP / FRED | リスクフリーレート | 米国10年国債利回り |
| J-Quants / 日銀 | 日本リスクフリーレート | 日本10年国債利回り |

### 米国株スクリーナー基準（FMP）
- 時価総額 > $1B（大型・中型株）
- 上場市場: NYSE / NASDAQ
- セクター分散（各セクター上位銘柄）

### 日本株スクリーナー基準（J-Quants）
- 時価総額 > 500億円
- 東証プライム市場
- セクター分散

---

## 分析指標一覧

### バリュエーション指標
| 指標 | 説明 | 良い水準 |
|------|------|---------|
| PER（株価収益率） | 株価 / EPS | < 15倍 割安 |
| PBR（株価純資産倍率） | 株価 / BPS | < 1.5倍 割安 |
| PSR（株価売上倍率） | 時価総額 / 売上 | セクター比較 |
| EV/EBITDA | 企業価値 / EBITDA | < 10倍 |
| PEGレシオ | PER / EPS成長率 | < 1.0 超割安 |

### 収益性指標
| 指標 | 説明 | 良い水準 |
|------|------|---------|
| ROE（自己資本利益率） | 純利益 / 純資産 | > 15% |
| ROA（総資産利益率） | 純利益 / 総資産 | > 5% |
| ROIC（投下資本利益率） | NOPAT / 投下資本 | > 10% |
| 売上総利益率 | 粗利 / 売上 | > 40% |
| 営業利益率 | 営業利益 / 売上 | > 15% |
| 純利益率 | 純利益 / 売上 | > 10% |

### 成長性指標
| 指標 | 説明 | 良い水準 |
|------|------|---------|
| EPS成長率（5年CAGR） | 1株利益成長 | > 10% |
| 売上成長率（5年CAGR） | 売上成長 | > 8% |
| FCF成長率 | フリーキャッシュフロー成長 | > 8% |

### 財務健全性指標
| 指標 | 説明 | 良い水準 |
|------|------|---------|
| D/Eレシオ | 有利子負債 / 純資産 | < 1.0 |
| 流動比率 | 流動資産 / 流動負債 | > 1.5 |
| インタレストカバレッジ | 営業利益 / 支払利息 | > 5倍 |

### キャッシュフロー指標
| 指標 | 説明 | 良い水準 |
|------|------|---------|
| FCFイールド | FCF / 時価総額 | > 4% |
| FCF転換率 | FCF / 純利益 | > 80% |
| CapEx比率 | 設備投資 / 売上 | セクター比較 |

### 株主還元指標
| 指標 | 説明 |
|------|------|
| 配当利回り | 配当 / 株価 |
| 自社株買い利回り | 自社株買い額 / 時価総額 |
| 総株主利回り | 配当利回り + 自社株買い利回り |
| 希薄化率 | 株式数増減率（マイナスが良い）|

---

## CAPM理論分析

### 計算式
```
期待リターン = Rf + β × (Rm - Rf)

Rf  = リスクフリーレート（10年国債利回り）
β   = 銘柄ベータ（過去52週週次リターンの市場への回帰係数）
Rm  = 市場リターン（米国: S&P500, 日本: TOPIX）
```

### 算出指標
| 指標 | 計算式 | 意味 |
|------|--------|------|
| β（ベータ） | Cov(Ri,Rm) / Var(Rm) | 市場感応度 |
| α（ジェンセンのアルファ） | 実績リターン - CAPM期待リターン | 超過リターン |
| シャープレシオ | (Rp - Rf) / σp | リスク調整後リターン |
| トレイナーレシオ | (Rp - Rf) / β | β1単位あたりリターン |
| 情報レシオ | α / トラッキングエラー | アクティブ運用の効率 |

### CAPMスクリーニング例
- **割安銘柄**: α > 0（CAPMより実績が上回る）
- **低リスク高リターン**: β < 1 かつ α > 0
- **市場アウトパフォーム**: 実績リターン > CAPM期待リターン

---

## スコアリングアルゴリズム（0〜100点）

```python
def calc_score(stock):
    score = 50  # ベーススコア

    # バリュエーション（最大+30）
    if stock.peg < 1.0:   score += 15
    elif stock.peg < 2.0: score += 8
    if stock.per < 15:    score += 10
    elif stock.per < 25:  score += 5
    elif stock.per > 50:  score -= 10

    # 収益性（最大+20）
    if stock.roic > 25:  score += 10
    elif stock.roic > 15: score += 5
    if stock.roe > 20:   score += 10
    elif stock.roe > 12: score += 5

    # 成長性（最大+20）
    if stock.eps_growth > 20:  score += 10
    elif stock.eps_growth > 10: score += 5
    if stock.rev_growth > 15:  score += 10
    elif stock.rev_growth > 8:  score += 5

    # キャッシュフロー（最大+15）
    if stock.fcf_yield > 6:  score += 10
    elif stock.fcf_yield > 3: score += 5
    if stock.fcf_conversion > 90: score += 5

    # CAPM α（最大+15）
    if stock.alpha > 5:  score += 15
    elif stock.alpha > 2: score += 8
    elif stock.alpha < -5: score -= 10

    return max(0, min(100, round(score)))
```

---

## プロジェクト構成（リポジトリ）

```
stock-analyzer/
├── backend/                    # Python FastAPI
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── stocks.py      # 銘柄一覧・検索
│   │   │   │   ├── screener.py    # スクリーナー
│   │   │   │   ├── capm.py        # CAPM計算
│   │   │   │   └── fundamentals.py # 財務指標
│   │   ├── core/
│   │   │   ├── config.py          # 環境変数
│   │   │   └── database.py        # DB接続
│   │   ├── models/
│   │   │   ├── stock.py           # SQLAlchemy models
│   │   │   └── schemas.py         # Pydantic schemas
│   │   ├── services/
│   │   │   ├── fmp_service.py     # FMP APIクライアント
│   │   │   ├── jquants_service.py # J-Quants APIクライアント
│   │   │   ├── capm_service.py    # CAPM計算ロジック
│   │   │   └── cache_service.py   # Redisキャッシュ
│   │   └── main.py
│   ├── scripts/
│   │   └── fetch_stocks.py        # 初期データ取得スクリプト
│   ├── requirements.txt
│   └── Dockerfile
│
├── flutter_app/                # Flutter
│   ├── lib/
│   │   ├── models/
│   │   │   ├── stock.dart
│   │   │   └── capm_result.dart
│   │   ├── screens/
│   │   │   ├── home_screen.dart       # ランキング画面
│   │   │   ├── screener_screen.dart   # スクリーナー
│   │   │   ├── detail_screen.dart     # 銘柄詳細
│   │   │   ├── capm_screen.dart       # CAPM分析
│   │   │   └── watchlist_screen.dart  # ウォッチリスト
│   │   ├── widgets/
│   │   │   ├── stock_card.dart
│   │   │   ├── metric_chip.dart
│   │   │   ├── bar_chart.dart         # fl_chart使用
│   │   │   └── score_badge.dart
│   │   ├── services/
│   │   │   └── api_service.dart       # バックエンドAPI呼び出し
│   │   ├── providers/
│   │   │   └── stock_provider.dart    # Riverpod
│   │   └── main.dart
│   └── pubspec.yaml
│
├── docs/
│   ├── PROJECT_ARCHITECTURE.md  ← このファイル
│   ├── API_SPEC.md
│   └── SPRINT_PLAN.md
└── README.md
```

---

## 技術スタック

| レイヤー | 技術 | 理由 |
|----------|------|------|
| モバイル | Flutter 3.x | iOS/Android同時開発 |
| 状態管理 | Riverpod | Flutter標準的・テスト容易 |
| チャート | fl_chart | Flutter最良チャートライブラリ |
| API | FastAPI | Python最速・自動Swagger生成 |
| DB | PostgreSQL | 財務データの関係性管理 |
| キャッシュ | Redis | API制限対策・高速化 |
| ORM | SQLAlchemy + Alembic | マイグレーション管理 |
| 数値計算 | NumPy / pandas | CAPM回帰計算 |
| デプロイ | Railway (backend) | 無料枠・Dockerサポート |
| 認証 | JWT（将来） | ウォッチリスト保存用 |

---

## 開発フェーズ

### Phase 1 — バックエンドMVP（Claude Codeで実装）
- [ ] FastAPIプロジェクト初期セットアップ
- [ ] FMP APIサービス（米国株100銘柄でテスト）
- [ ] 財務指標計算ロジック
- [ ] スクリーナーエンドポイント
- [ ] Railway/Renderデプロイ

### Phase 2 — CAPM追加（Claude Codeで実装）
- [ ] 週次リターン計算
- [ ] ベータ回帰計算（NumPy）
- [ ] アルファ・シャープ比計算
- [ ] CAPMエンドポイント追加

### Phase 3 — Flutter MVP（Claude Codeで実装）
- [ ] 銘柄ランキング画面
- [ ] 銘柄詳細画面（財務指標）
- [ ] チャート（EPS/FCFトレンド）
- [ ] バックエンドAPI接続

### Phase 4 — 日本株追加（Claude Codeで実装）
- [ ] J-Quants APIサービス
- [ ] 日本株1000銘柄スクリーニング
- [ ] 円建て/ドル建て切替UI

### Phase 5 — 拡張機能（Claude Codeで実装）
- [ ] スクリーナーUI（カスタムフィルター）
- [ ] ウォッチリスト（ローカル保存）
- [ ] プッシュ通知（急騰・急落）
- [ ] App Store / Play Store 申請

---

## Cowork / Claude Code 分業体制

### Cowork（このチャット）の役割
- ✅ 全体アーキテクチャ設計・変更管理
- ✅ スプリント計画・タスク分解
- ✅ 仕様書・API設計ドキュメント作成
- ✅ デプロイ設定・環境変数管理（ブラウザ操作）
- ✅ Vercel / Railway デプロイ実行
- ✅ GitHub設定・Secrets設定
- ✅ 進捗管理・次のタスク指示

### Claude Code（VS Codeターミナル）の役割
- ✅ Python（FastAPI）コーディング
- ✅ Flutter（Dart）コーディング
- ✅ テスト作成・実行
- ✅ Git commit / push
- ✅ デバッグ・エラー修正
- ✅ リファクタリング

### 連携フロー
```
Cowork: 「Phase 1のFMPサービスを実装して」
  → API仕様書（API_SPEC.md）を参照指示
  → 実装完了後「デプロイしたいのでURLを教えて」

Claude Code: コード実装 → push
  → 「実装しました。Railway URLは○○です」

Cowork: RailwayにデプロイURLを確認
  → Flutter appの接続先に設定
  → 動作確認
```

---

## 即座に始めるべきこと（Phase 1 Step 1）

**VS Code + Claude Code でやること：**

```bash
# 1. リポジトリ作成
mkdir stock-analyzer && cd stock-analyzer
git init

# 2. バックエンドセットアップ
mkdir backend && cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary \
            redis httpx pandas numpy python-dotenv pydantic

# 3. Claude Codeに渡す指示
# 「API_SPEC.mdに従ってFastAPIのプロジェクト構造を作って。
#   まずfmp_service.pyでFMP APIから
#   スクリーナー・財務諸表・レシオを取得できるようにして」
```
