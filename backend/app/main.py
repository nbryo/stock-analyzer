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


async def _seed_if_empty():
    """Run initial data fetch if DB is empty (background task, non-blocking)."""
    from app.models.stock import Stock
    db = SessionLocal()
    try:
        count = db.query(Stock).count()
        if count == 0:
            logger.info("DB empty — seeding initial stock data in background...")
            try:
                from scripts.fetch_initial_data import fetch_and_save
                await fetch_and_save()
                logger.info("Initial stock data seeded successfully.")
            except Exception as e:
                logger.error(f"Seed error: {e}")
        else:
            logger.info(f"DB has {count} stocks, skipping seed.")
    except Exception as e:
        logger.warning(f"Seed check error (non-fatal): {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all DB tables on startup
    Base.metadata.create_all(bind=engine)
    # Kick off background seed (won't block request handling)
    asyncio.create_task(_seed_if_empty())
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
