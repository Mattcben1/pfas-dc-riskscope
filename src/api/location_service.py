from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests

router = APIRouter()

class LocationRequest(BaseModel):
    lat: float
    lon: float

@router.post("/simulate-location")
def simulate_location(payload: LocationRequest):
    lat = payload.lat
    lon = payload.lon

    # 1. Reverse geocode to state abbreviation
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        data = requests.get(url, headers={"User-Agent": "RiskScope"}).json()
        state = data.get("address", {}).get("state", "UNKNOWN")

        # Make into proper 2-letter state code manually if needed
        # Example: “Virginia” → “VA”
        state_map = {
            "Virginia": "VA",
            "Maryland": "MD",
            "Pennsylvania": "PA",
            "West Virginia": "WV",
            "Delaware": "DE"
        }
        state_code = state_map.get(state, "US")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Return auto-fill material
    return {
        "state": state_code,
        "receiving_flow_mgd": 42.0,        # default placeholder
        "discharge_flow_mgd": 3.5,         # default placeholder
        "background_source": "auto-filled"
    }
