from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from src.simulation.simulator import PFASRiskSimulator
from src.api.middleware.payload_validator import validate_simulation_payload

router = APIRouter()

simulator = PFASRiskSimulator()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/simulate")
def simulate(payload: dict):
    """
    Main simulation endpoint
    """
    try:
        validate_simulation_payload(payload)
        result = simulator.simulate(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-pdf")
def export_pdf(payload: dict):
    """
    Generate PDF from simulation results
    """
    from src.api.pdf_exporter import generate_pdf_report

    try:
        validate_simulation_payload(payload)
        result = simulator.simulate(payload)
        pdf_path = generate_pdf_report(result)
        return FileResponse(pdf_path, filename="pfas_report.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

