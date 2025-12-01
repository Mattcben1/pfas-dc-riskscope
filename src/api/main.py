from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routes import router as simulation_router
from .location_service import router as location_router

app = FastAPI(title="PFAS DC RiskScope")

# ------------------------------
# 1) Mount UI Static Files
# ------------------------------
app.mount(
    "/ui", StaticFiles(directory="src/ui"), name="ui"
)

# ------------------------------
# 2) Serve main UI page
# ------------------------------
@app.get("/map")
def serve_map_ui():
    return FileResponse("src/ui/location_picker.html")

# ------------------------------
# Routers
# ------------------------------
app.include_router(simulation_router)
app.include_router(location_router)

@app.get("/")
def root():
    return {"message": "PFAS DC RiskScope API running"}
