from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests

from src.simulation.simulator import PFASRiskSimulator
from src.etl.ucmr5_ingest import load_ucmr5_background

router = APIRouter()

# Load UCMR5 medians ONCE
BACKGROUND = load_ucmr5_background()
sim = PFASRiskSimulator()


class LocationRequest(BaseModel):
    lat: float
    lon: float


@router.post("/simulate-location")
def simulate_location(payload: LocationRequest):
    lat = payload.lat
    lon = payload.lon

    # ----------------------------------------------------
    # Reverse Geocode → Full State Name
    # ----------------------------------------------------
    try:
        url = (
            f"https://nominatim.openstreetmap.org/reverse?"
            f"lat={lat}&lon={lon}&format=json"
        )
        resp = requests.get(url, headers={"User-Agent": "RiskScope"})
        data = resp.json()
        full_state = data.get("address", {}).get("state", "UNKNOWN")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Reverse geocode error: {str(e)}")

    # ----------------------------------------------------
    # State Name → Abbreviation
    # ----------------------------------------------------
    state_name_to_abbrev = {
        "Virginia": "VA",
        "Maryland": "MD",
        "Pennsylvania": "PA",
        "West Virginia": "WV",
        "Delaware": "DE",
    }
    abbrev = state_name_to_abbrev.get(full_state, "US")

    # ----------------------------------------------------
    # Abbrev → FIPS code (used in UCMR5 dataset)
    # ----------------------------------------------------
    abbrev_to_fips = {
        "AL": "01","AK": "02","AZ": "04","AR": "05","CA": "06","CO": "08",
        "CT": "09","DE": "10","FL": "12","GA": "13","HI": "15","ID": "16",
        "IL": "17","IN": "18","IA": "19","KS": "20","KY": "21","LA": "22",
        "ME": "23","MD": "24","MA": "25","MI": "26","MN": "27","MS": "28",
        "MO": "29","MT": "30","NE": "31","NV": "32","NH": "33","NJ": "34",
        "NM": "35","NY": "36","NC": "37","ND": "38","OH": "39","OK": "40",
        "OR": "41","PA": "42","RI": "44","SC": "45","SD": "46","TN": "47",
        "TX": "48","UT": "49","VT": "50","VA": "51","WA": "53","WV": "54",
        "WI": "55","WY": "56","US": "00"
    }

    fips = abbrev_to_fips.get(abbrev, "00")

    # ----------------------------------------------------
    # Retrieve PFAS background (all chemicals + TOTAL_PFAS)
    # ----------------------------------------------------
    chem_map = BACKGROUND.get(fips, {})

    # TOTAL_PFAS = realistic surrogate for background contamination burden
    total_pfas = float(chem_map.get("TOTAL_PFAS", 0.0))

    # Commonly displayed chemicals
    bg_pfoa = float(chem_map.get("PFOA", 0.0))
    bg_pfos = float(chem_map.get("PFOS", 0.0))

    # Display combined median (avoids zeros)
    combined_display = total_pfas if total_pfas > 0 else (bg_pfoa + bg_pfos) / 2

    # ----------------------------------------------------
    # Return results for dashboard autofill
    # ----------------------------------------------------
    return {
        "lat": lat,
        "lon": lon,
        "state": fips,               # Dashboard + simulator use FIPS
        "state_abbrev": abbrev,

        # Background PFAS
        "background_total_pfas_ppt": total_pfas,
        "background_pfoa_ppt": bg_pfoa,
        "background_pfos_ppt": bg_pfos,
        "background_pfas_median_ppt": combined_display,

        "background_source": "UCMR5 state-level medians (ppt)",

        # Default hydrology assumptions
        "receiving_flow_mgd": 50.0,
        "discharge_flow_mgd": 3.0
    }
