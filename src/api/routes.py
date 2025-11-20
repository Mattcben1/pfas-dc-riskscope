"""
routes.py

API route definitions for PFAS-DC RiskScope.
"""

from fastapi import APIRouter, HTTPException
from .middleware.payload_validator import validate_simulation_payload
from ..simulation.simulator import PFASRiskSimulator

router = APIRouter()
simulator = PFASRiskSimulator()


@router.post("/simulate")
def run_simulation(payload: dict):
    """
    Run a PFAS regulatory risk simulation.
    """
    is_valid, message = validate_simulation_payload(payload)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    result = simulator.simulate(payload)
    return result


@router.get("/health")
def health_check():
    return {"status": "ok", "message": "PFAS-DC RiskScope API running"}
