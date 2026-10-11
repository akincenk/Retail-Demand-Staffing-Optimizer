from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.api import api_router

app = FastAPI(
    title="Retail Demand & Staffing Optimizer",
    version="1.0.0",
    openapi_tags=[
        {"name": "util", "description": "Utility endpoints"},
        {"name": "stores", "description": "Stores CRUD"},
        {"name": "skus", "description": "SKUs CRUD"},
        {"name": "sales", "description": "Sales ingest"},
        {"name": "forecast", "description": "Forecasting operations"},
        {"name": "staffing", "description": "Staffing planner"},
    ],
)

@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})

app.include_router(api_router)
