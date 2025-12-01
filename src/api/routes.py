from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from .middleware.payload_validator import validate_simulation_payload
from .pdf_exporter import generate_pdf_report
from src.simulation.simulator import PFASRiskSimulator

router = APIRouter()

simulator = PFASRiskSimulator()

@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/simulate")
async def simulate(payload: dict):
    try:
        result = simulator.simulate(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-pdf")
async def export_pdf(payload: dict):
    """
    Runs the simulation and returns a PDF file.
    Uses the exact same payload as /simulate.
    """
    try:
        validate_simulation_payload(payload)

        result = simulator.simulate(payload)

        pdf_path = generate_pdf_report(result)

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=Path(pdf_path).name,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
