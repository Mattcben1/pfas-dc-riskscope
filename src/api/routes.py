from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path

from .middleware.payload_validator import (
    validate_simulation_payload,
    validate_location_payload,
)

from src.simulation.simulator import PFASSimulator
from .pdf_exporter import generate_pdf_report, generate_pdf_report_with_map
from src.ui.map_renderer import render_hotspot_map

router = APIRouter()

# -------------------------------
# GLOBAL SIMULATOR INSTANCE
# -------------------------------
sim = PFASSimulator()


# ============================================================
# 1) BASIC SIMULATION
# ============================================================
@router.post("/simulate")
async def simulate(payload: dict):
    """Run the PFAS simulation (state-based)."""
    try:
        validate_simulation_payload(payload)
        result = sim.simulate(payload)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 2) BASIC PDF EXPORT
# ============================================================
@router.post("/export-pdf")
async def export_pdf(payload: dict):
    """Export PDF from state-based simulation."""
    try:
        validate_simulation_payload(payload)

        result = sim.simulate(payload)
        pdf_path = generate_pdf_report(result)

        return FileResponse(
            pdf_path,
            filename=Path(pdf_path).name,
            media_type="application/pdf"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 3) LOCATION PICKER UI
# ============================================================
@router.get("/ui/location-picker", response_class=HTMLResponse)
async def location_picker_ui():
    """
    Serve HTML for users to click a real map and send coordinates to /simulate-location.
    """
    html_path = Path("assets/ui/location_map.html")
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="UI file not found.")

    return FileResponse(str(html_path), media_type="text/html")


# ============================================================
# 4) LOCATION-BASED SIMULATION
# ============================================================

@router.post("/simulate-location")
async def simulate_location(payload: dict):
    """
    Run a simulation using LAT/LON plus flows and discharge PFAS concentrations.
    """
    try:
        validate_location_payload(payload)

        lat = float(payload["lat"])
        lon = float(payload["lon"])

        # We do NOT use the missing "simulator" — we use sim
        result = sim.simulate({
            "location": {"lat": lat, "lon": lon},
            "receiving_flow_mgd": payload["receiving_flow_mgd"],
            "discharge_flow_mgd": payload["discharge_flow_mgd"],
            "discharge_pfas_ppt": payload["discharge_pfas_ppt"],
        })

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 5) LOCATION-BASED PDF EXPORT
# ============================================================

@router.post("/export-pdf-location")
async def export_pdf_location(payload: dict):
    """
    Run location model, generate hotspot map, embed in PDF.
    """
    try:
        validate_location_payload(payload)

        lat = float(payload["lat"])
        lon = float(payload["lon"])

        result = sim.simulate({
            "location": {"lat": lat, "lon": lon},
            "receiving_flow_mgd": payload["receiving_flow_mgd"],
            "discharge_flow_mgd": payload["discharge_flow_mgd"],
            "discharge_pfas_ppt": payload["discharge_pfas_ppt"],
        })

        # Generate map
        map_path = Path("assets/screenshots/location_map.png")
        render_hotspot_map(
            selected_lat=lat,
            selected_lon=lon,
            selected_label="Selected Site",
            output_path=map_path,
            state_filter=result.get("inputs", {}).get("state", "US")
        )

        # Export PDF
        pdf_path = generate_pdf_report_with_map(result, map_path)

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=Path(pdf_path).name,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
