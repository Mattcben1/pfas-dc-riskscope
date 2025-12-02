from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path

from src.api.routes import router as simulation_router
from src.api.location_service import router as location_router

app = FastAPI(title="PFAS DC RiskScope")


# Mount backend routers
app.include_router(simulation_router)
app.include_router(location_router)


def load_html(name: str) -> str:
    p = Path(__file__).resolve().parent.parent / "ui" / name
    if not p.exists():
        return f"<h2 style='color:red'>Missing UI file: {p}</h2>"
    return p.read_text()


@app.get("/", response_class=HTMLResponse)
def index():
    return load_html("app.html")


@app.get("/map", response_class=HTMLResponse)
def map_ui():
    return load_html("location_picker.html")


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_ui():
    return load_html("dashboard.html")
