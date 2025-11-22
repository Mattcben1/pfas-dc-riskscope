"""
routes.py

API route definitions for PFAS-DC RiskScope.
"""
from .pdf_exporter import generate_pdf_report
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
@router.post("/export-pdf")
def export_pdf(payload: dict):
    """
    Runs the simulation and exports a PDF report.
    """

    is_valid, message = validate_simulation_payload(payload)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    result = simulator.simulate(payload)

    # Optional metadata (site name, district, operator, population served, etc.)
    metadata = payload.get("metadata", {})

    pdf_path = generate_pdf_report(result, metadata)

    return {
        "message": "PDF generated successfully",
        "path": pdf_path
    }
