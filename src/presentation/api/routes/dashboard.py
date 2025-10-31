"""Dashboard routes for Grafana integration."""

from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Setup router
router = APIRouter()

# Setup templates directory
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """
    Serve dashboard HTML page for embedding in Grafana.

    This dashboard shows the latest performance insights with stats cards
    and a table of recent analysis results.
    """
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )


@router.get("/dashboard/llm", response_class=HTMLResponse)
async def llm_dashboard(request: Request):
    """
    Serve LLM-powered insights dashboard for Grafana.

    This dashboard shows AI-generated performance insights using the
    MiniMax-M2 language model via Ollama. Analysis may take 30-60 seconds.
    """
    return templates.TemplateResponse(
        "llm_dashboard.html",
        {"request": request}
    )
