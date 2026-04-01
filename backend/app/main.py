import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import screener, stocks, capm
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal

# Import all models so Base knows about them before create_all
import app.models.stock  # noqa: F401

logger = logging.getLogger(__name__)


async def _seed_initial_data():
    """Run initial data fetch if DB is empty (non-blocking background task)."""
    from app.models.stock import Stock
    db = SessionLocal()
    try:
        count = db.query(Stock).count()
        if count == 0:
            logger.info("DB empty — running initial data seed in background...")
            from scripts.fetch_initial_data import main as fetch_main
            await asyncio.to_thread(fetch_main)
            logger.info("Initial data seed complete.")
        else:
            logger.info(f"DB already has {count} stocks, skipping seed.")
    except Exception as e:
        logger.warning(f"Seed task error (non-fatal): {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    Base.metadata.create_all(bind=engine)
    # Seed initial data in background (doesn't block startup)
    asyncio.create_task(_seed_initial_data())
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
    return {"status": "ok", "stocks_in_db": stock_count}
