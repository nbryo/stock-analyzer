import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import screener, stocks, capm, scraper
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
import app.models.stock  # noqa: F401

logger = logging.getLogger(__name__)

_seed_running = False
_seed_result: dict = {}


async def _run_seed(force: bool = False):
    """Run seed. If force=False, skip when DB already has data."""
    global _seed_running, _seed_result
    from app.models.stock import Stock
    db = SessionLocal()
    try:
        count = db.query(Stock).count()
        if not force and count > 0:
            logger.info(f"DB has {count} stocks, skipping seed.")
            return
    except Exception as e:
        logger.warning(f"Seed check error: {e}")
    finally:
        db.close()

    _seed_running = True
    _seed_result = {}
    try:
        logger.info("Starting DB seed via yfinance...")
        from scripts.fetch_initial_data import fetch_and_save
        result = await fetch_and_save()
        _seed_result = result
        logger.info(f"Seed complete: {result}")
    except Exception as e:
        logger.error(f"Seed error: {e}")
        _seed_result = {"error": str(e)}
    finally:
        _seed_running = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    asyncio.create_task(_run_seed(force=False))
    yield


app = FastAPI(
    title="Stock Analyzer API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(screener.router, prefix="/api/v1", tags=["Screener"])
app.include_router(stocks.router, prefix="/api/v1", tags=["Stocks"])
app.include_router(capm.router, prefix="/api/v1", tags=["CAPM"])
app.include_router(scraper.router, prefix="/api/v1", tags=["Scraper"])


@app.get("/")
async def root():
    return {"message": "Stock Analyzer API", "version": "1.0.0"}


@app.get("/health")
async def health():
    from app.models.stock import Stock
    db = SessionLocal()
    try:
        stock_count = db.query(Stock).count()
    except Exception:
        stock_count = -1
    finally:
        db.close()
    return {
        "status": "ok",
        "stocks_in_db": stock_count,
        "seed_running": _seed_running,
        "seed_result": _seed_result,
    }


@app.post("/admin/seed")
async def admin_seed(force: bool = True):
    """Trigger DB seeding as a background task. Poll /health for progress."""
    global _seed_running
    if _seed_running:
        return {"status": "already_running"}
    asyncio.create_task(_run_seed(force=force))
    return {"status": "started", "message": "Seeding in background. Poll /health for stocks_in_db count."}
