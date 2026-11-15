from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.cases import router as cases_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.logs import router as logs_router
from app.api.v1.timeline import router as timeline_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.reports import router as reports_router
from app.api.v1.audit import router as audit_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(cases_router)
api_v1_router.include_router(evidence_router)
api_v1_router.include_router(logs_router)
api_v1_router.include_router(timeline_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(audit_router)
