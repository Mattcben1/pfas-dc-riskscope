# src/api/location_service.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests

from src.etl.ucmr5_ingest import load_ucmr5_background

router = APIRouter()

BACKGROUND = load_ucmr5_background()


class LocationRequest(BaseModel):
    lat: float
    lon: float


@router.post("/simulate-location")
def simulate_location(payload: LocationRequest):
    lat = payload.lat
    lon = payload.lon

    # -------------------------
    # Reverse Geocode → State name
    # -------------------------
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        resp = requests.get(url, headers={"User-Agent": "RiskScope"})
        data = resp.json()
        full_state = data.get("address", {}).get("state", "UNKNOWN")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Reverse geocode error: {str(e)}")

    # -------------------------
    # State name → USPS abbreviation
    # -------------------------
    state_name_to_abbrev = {
        "Virginia": "VA",
        "Maryland": "MD",
        "Pennsylvania": "PA",
        "West Virginia": "WV",
        "Delaware": "DE",
    }
    abbrev = state_name_to_abbrev.get(full_state, "US")

    # -------------------------
    # Abbrev → FIPS (matches UCMR5)
    # -------------------------
    abbrev_to_fips = {
        "AL": "01","AK": "02","AZ": "04","AR": "05",
        "CA": "06","CO": "08","CT": "09","DE": "10",
        "FL": "12","GA": "13","HI": "15","ID": "16",
        "IL": "17","IN": "18","IA": "19","KS": "20",
        "KY": "21","LA": "22","ME": "23","MD": "24",
        "MA": "25","MI": "26","MN": "27","MS": "28",
        "MO": "29","MT": "30","NE": "31","NV": "32",
        "NH": "33","NJ": "34","NM": "35","NY": "36",
        "NC": "37","ND": "38","OH": "39","OK": "40",
        "OR": "41","PA": "42","RI": "44","SC": "45",
        "SD": "46","TN": "47","TX": "48","UT": "49",
        "VT": "50","VA": "51","WA": "53","WV": "54",
        "WI": "55","WY": "56","US": "US"
    }
    fips = abbrev_to_fips.get(abbrev, "US")

    # -------------------------
    # Per-state PFAS background (ppt)
    # -------------------------
    chem_map = BACKGROUND.get(fips) or BACKGROUND.get("US", {})

    bg_pfoa = float(chem_map.get("PFOA", 0.0))
    bg_pfos = float(chem_map.get("PFOS", 0.0))

    # If both zero, fall back to national medians if present
    if bg_pfoa == 0.0 and bg_pfos == 0.0:
        us_map = BACKGROUND.get("US", {})
        bg_pfoa = float(us_map.get("PFOA", bg_pfoa))
        bg_pfos = float(us_map.get("PFOS", bg_pfos))

    combined_bg = (bg_pfoa + bg_pfos) / 2.0 if (bg_pfoa or bg_pfos) else 0.0

    return {
        "lat": lat,
        "lon": lon,
        "state": fips,  # FIPS for simulator
        "state_abbrev": abbrev,
        "background_pfoa_ppt": bg_pfoa,
        "background_pfos_ppt": bg_pfos,
        "background_pfas_median_ppt": combined_bg,
        "background_source": "UCMR5 state-level medians (with national fallback)",
        "receiving_flow_mgd": 50.0,
        "discharge_flow_mgd": 3.0,
    }
