from fastapi import APIRouter

router = APIRouter()


@router.get("/capm/{ticker}")
async def get_capm_analysis(ticker: str):
    return {"ticker": ticker.upper(), "message": "CAPM endpoint - to be implemented in Phase 2"}
