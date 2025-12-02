# src/api/routes.py

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from src.simulation.simulator import PFASRiskSimulator
from src.api.middleware.payload_validator import validate_simulation_payload
from src.api.pdf_exporter import generate_pdf_report

router = APIRouter()
simulator = PFASRiskSimulator()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/simulate")
def simulate(payload: dict):
    """
    Main simulation endpoint.
    """
    try:
        validate_simulation_payload(payload)
        result = simulator.simulate(payload)

        # carry through lat/lon if sent
        result["lat"] = payload.get("lat")
        result["lon"] = payload.get("lon")

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-pdf")
def export_pdf(payload: dict):
    """
    Runs simulation and returns a PDF file summarizing results.
    """
    try:
        validate_simulation_payload(payload)
        result = simulator.simulate(payload)

        # attach location + state info for PDF
        result["lat"] = payload.get("lat")
        result["lon"] = payload.get("lon")
        if "state" not in result:
            result["state"] = payload.get("state")

        pdf_path_str = generate_pdf_report(result)
        pdf_path = Path(pdf_path_str)

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=pdf_path.name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
