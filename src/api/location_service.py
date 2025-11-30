from fastapi import APIRouter
import requests

router = APIRouter()

@router.get("/location-info")
def location_info(lat: float, lon: float):
    """
    Given a latitude/longitude, return:
    - State (reverse geocode)
    - Default receiving + discharge flow (placeholder)
    - Default PFAS discharge values
    """

    # Reverse geocode to get state name
    url = (
        f"https://nominatim.openstreetmap.org/reverse?"
        f"format=jsonv2&lat={lat}&lon={lon}"
    )

    r = requests.get(url, headers={"User-Agent": "RiskScope"})
    data = r.json()

    state = data.get("address", {}).get("state", "Unknown")

    # Temporary placeholder hydrology values
    # (We will replace these with real watershed flow data next)
    return {
        "state": state,
        "receiving_flow_mgd": 42,
        "discharge_flow_mgd": 3.5,
        "pfas_default": {
            "PFOA": 7.5,
            "PFOS": 6.2,
            "HFPO-DA": 5.0
        }
    }
