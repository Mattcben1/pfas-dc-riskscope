from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from .middleware.payload_validator import validate_simulation_payload
from src.simulation.simulator import PFASSimulator, SimulationConfig
from .pdf_exporter import generate_pdf_report

router = APIRouter()

# Instantiate simulator once at startup
sim = PFASSimulator(SimulationConfig())


@router.post("/simulate")
async def simulate(payload: dict):
    try:
        validate_simulation_payload(payload)

        result = simulator.evaluate(
            state=payload["state"],
            receiving_flow_mgd=payload["receiving_flow_mgd"],
            discharge_flow_mgd=payload["discharge_flow_mgd"],
            discharge_pfas_ppt=payload["discharge_pfas_ppt"],
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-pdf")
async def export_pdf(payload: dict):
    """
    Generate a PFAS simulation PDF report.
    """
    try:
        validate_simulation_payload(payload)

        result = sim.run_simulation(
            state=payload["state"],
            receiving_flow_mgd=payload["receiving_flow_mgd"],
            discharge_flow_mgd=payload["discharge_flow_mgd"],
            discharge_pfas_ppt=payload["discharge_pfas_ppt"]
        )

        pdf_path = generate_pdf_report(result)

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=Path(pdf_path).name
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
