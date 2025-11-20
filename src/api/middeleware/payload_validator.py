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
