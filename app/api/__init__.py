from fastapi import APIRouter, Depends

from app.core.auth import require_api_key

from . import forecast, sales, skus, staffing, stores, util

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(util.router, tags=["util"])

_protected = [Depends(require_api_key)]
api_router.include_router(stores.router, prefix="/stores", tags=["stores"], dependencies=_protected)
api_router.include_router(skus.router, prefix="/skus", tags=["skus"], dependencies=_protected)
api_router.include_router(sales.router, prefix="/sales", tags=["sales"], dependencies=_protected)
api_router.include_router(forecast.router, prefix="/forecast", tags=["forecast"], dependencies=_protected)
api_router.include_router(staffing.router, prefix="/staffing", tags=["staffing"], dependencies=_protected)
