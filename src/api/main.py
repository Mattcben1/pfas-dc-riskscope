from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .routes import router as simulation_router
from .location_service import router as location_router

app = FastAPI(title="PFAS DC RiskScope")

# ------------------------------------------------------------------
# Attach backend routes (simulation + location lookup)
# ------------------------------------------------------------------
app.include_router(simulation_router)
app.include_router(location_router)


# ------------------------------------------------------------------
# Serve the homepage
# ------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "PFAS DC RiskScope API running"}


# ------------------------------------------------------------------
# Helper to safely load HTML files inside Docker
# ------------------------------------------------------------------
def load_html(file_path: str) -> str:
    """
    Utility to safely load HTML files even when running inside Docker.
    Looks for files relative to /app/src/ui/
    """
    full_path = Path("/app/src/ui") / file_path
    if not full_path.exists():
        return f"<h3 style='color:red;'>ERROR: UI file not found: {full_path}</h3>"
    return full_path.read_text()


# ------------------------------------------------------------------
# Serve the MAP UI (Leaflet map where user clicks a site)
# ------------------------------------------------------------------
@app.get("/map", response_class=HTMLResponse)
def serve_map():
    return load_html("location_picker.html")


# ------------------------------------------------------------------
# Serve the DASHBOARD UI (Run Simulation + Export PDF)
# ------------------------------------------------------------------
@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    return load_html("dashboard.html")
