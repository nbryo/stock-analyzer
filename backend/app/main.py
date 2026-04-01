from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import screener, stocks, capm
from app.core.config import settings

app = FastAPI(
    title="Stock Analyzer API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
    return {"status": "ok"}
