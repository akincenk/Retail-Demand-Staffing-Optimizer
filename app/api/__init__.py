from fastapi import APIRouter
from . import stores, skus, sales, forecast, staffing, util

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(util.router, tags=["util"])
api_router.include_router(stores.router, prefix="/stores", tags=["stores"])
api_router.include_router(skus.router, prefix="/skus", tags=["skus"])
api_router.include_router(sales.router, prefix="/sales", tags=["sales"])
api_router.include_router(forecast.router, prefix="/forecast", tags=["forecast"])
api_router.include_router(staffing.router, prefix="/staffing", tags=["staffing"])
