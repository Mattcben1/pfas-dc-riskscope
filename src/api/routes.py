"""
routes.py

API route definitions for PFAS-DC RiskScope.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from .middleware.payload_validator import validate_simulation_payload
from ..simulation.simulator import PFASRiskSimulator
from .pdf_exporter import generate_pdf_report

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
    Runs the simulation and returns a downloadable PDF report.
    """

    is_valid, message = validate_simulation_payload(payload)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    # Run simulation
    result = simulator.simulate(payload)

    # Optional metadata (site name, operator, watershed, etc.)
    metadata = payload.get("metadata", {})

    # Generate PDF on disk
    pdf_path = generate_pdf_report(result, metadata)
    pdf_path_obj = Path(pdf_path)

    if not pdf_path_obj.exists():
        raise HTTPException(status_code=500, detail="PDF generation failed")

    # Return as downloadable file
    return FileResponse(
        path=str(pdf_path_obj),
        media_type="application/pdf",
        filename=pdf_path_obj.name,
    )
