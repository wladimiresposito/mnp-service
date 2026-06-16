from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.api.dependencies import require_api_key
from app.dashboard.page import DASHBOARD_HTML

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(_: None = Depends(require_api_key)) -> HTMLResponse:
    return HTMLResponse(DASHBOARD_HTML)
