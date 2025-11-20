"""
main.py

FastAPI application entry point for PFAS-DC RiskScope.
"""

from fastapi import FastAPI
from .routes import router as simulation_router

app = FastAPI(
    title="PFAS-DC RiskScope API",
    description="Regulatory PFAS simulation for data-center siting and environmental planning",
    version="0.1.0",
)

# Include all simulation routes
app.include_router(simulation_router)
