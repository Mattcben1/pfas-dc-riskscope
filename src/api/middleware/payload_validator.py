"""
payload_validator.py

Minimal validation for simulation payload structure.
This prevents invalid/broken requests from reaching the simulation engine.
"""

from typing import Dict, Any


REQUIRED_TOP_LEVEL_KEYS = [
    "chemicals",
    "environmental_factors",
    "data_center",
    "scenario_parameters",
]


def validate_simulation_payload(payload: Dict[str, Any]) -> (bool, str):
    """
    Returns (is_valid, error_message)
    """
    # Check required sections exist
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in payload:
            return False, f"Missing required field: '{key}'"

    # Check chemical concentrations
    if "concentrations_ppt" not in payload["chemicals"]:
        return False, "Missing 'chemicals.concentrations_ppt'"

    # Check environmental factors exist
    if "groundwater_vulnerability_index" not in payload["environmental_factors"]:
        return False, "Missing groundwater vulnerability index"

    return True, "OK"

def validate_location_payload(payload: dict) -> None:
    """
    Validate payload for location-based simulation endpoints.

    Expected shape:

    {
      "lat": 38.95,
      "lon": -77.3,
      "receiving_flow_mgd": 42.0,
      "discharge_flow_mgd": 3.5,
      "discharge_pfas_ppt": {
        "PFOA": 7.5,
        "PFOS": 6.2,
        "HFPO-DA": 5.0
      }
    }
    """
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON object")

    required_keys = [
        "lat",
        "lon",
        "receiving_flow_mgd",
        "discharge_flow_mgd",
        "discharge_pfas_ppt",
    ]

    missing = [k for k in required_keys if k not in payload]
    if missing:
        raise ValueError(f"Missing required keys: {', '.join(missing)}")

    # Lat / lon numeric
    try:
        float(payload["lat"])
        float(payload["lon"])
    except Exception:
        raise ValueError("'lat' and 'lon' must be numeric")

    # Flows numeric
    try:
        float(payload["receiving_flow_mgd"])
        float(payload["discharge_flow_mgd"])
    except Exception:
        raise ValueError("'receiving_flow_mgd' and 'discharge_flow_mgd' must be numeric")

    # PFAS dict
    pfas = payload["discharge_pfas_ppt"]
    if not isinstance(pfas, dict) or not pfas:
        raise ValueError("'discharge_pfas_ppt' must be a non-empty object")

    for chem, value in pfas.items():
        if not isinstance(chem, str) or not chem.strip():
            raise ValueError("PFAS keys must be non-empty strings")
        try:
            float(value)
        except Exception:
            raise ValueError(f"PFAS value for '{chem}' must be numeric")
