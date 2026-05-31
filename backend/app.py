from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from backend.agent import process_query

app = FastAPI(title="FinQuery API")

# Allow Streamlit frontend to call from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str
    session_id: str = "default"

class QueryResponse(BaseModel):
    answer: str
    sql: str
    chart_json: Optional[str] = None
    error: Optional[str] = None

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    result = process_query(req.question, req.session_id)
    return result

@app.get("/schema")
async def schema_info():
    """Return table descriptions for the frontend expander."""
    return {
        "tables": {
            "stock_prices": "date, ticker, open, high, low, close, volume, sector",
            "companies": "ticker, name, sector, market_cap, index_name",
            "stock_metrics": "ticker, week_ending, avg_volume, price_change_pct, volatility, rsi_14"
        },
        "stocks": "20 major NSE stocks across sectors (Reliance, Infy, BEL, HAL, etc.)"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)