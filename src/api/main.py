from fastapi import FastAPI
from .routes import router as simulation_router
from .location_service import router as location_router

app = FastAPI(title="PFAS DC RiskScope")

# Register routers **AFTER** 'app' is created
app.include_router(simulation_router)
app.include_router(location_router)


@app.get("/")
def root():
    return {"message": "PFAS DC RiskScope API running"}
