"""
model_schema.py

This file defines the core PFAS risk model schema used by the simulator,
API, and UI layers.

It acts as a single source of truth for:
- which PFAS chemicals we track
- which environmental factors matter
- which data-center properties are modeled
- which regulatory flags and parameters are used
- which scenario settings are available
- which output fields the simulator should return

All other parts of the system should treat this schema as a contract.
"""

from typing import Dict, Any, List

# ---------------------------------------------------------------------
# 1) Core chemical universe for the model
# ---------------------------------------------------------------------

PFAS_CHEMICALS: List[str] = [
    "PFOA",
    "PFOS",
    "PFHxS",
    "PFNA",
    "HFPO-DA",  # GenX
    "PFBS",
]


# ---------------------------------------------------------------------
# 2) Master model schema
# ---------------------------------------------------------------------

PFAS_RISK_MODEL_SCHEMA: Dict[str, Dict[str, Any]] = {
    "chemicals": {
        "description": "PFAS chemical concentrations at or near the proposed site.",
        "fields": {
            "concentrations_ppt": {
                "type": "dict[str, float]",
                "required": True,
                "allowed_keys": PFAS_CHEMICALS,
                "units": "parts per trillion (ppt)",
                "example": {
                    "PFOA": 3.5,
                    "PFOS": 2.1,
                    "PFHxS": 0.7,
                },
            },
        },
    },

    "environmental_factors": {
        "description": "Hydrological and contextual factors that influence PFAS fate and transport.",
        "fields": {
            "groundwater_vulnerability_index": {
                "type": "float",
                "range": [0.0, 1.0],
                "required": True,
                "description": "0 = very low vulnerability, 1 = very high vulnerability.",
            },
            "surface_water_distance_km": {
                "type": "float",
                "required": True,
                "description": "Distance from site to nearest surface water body.",
            },
            "drinking_water_intake_distance_km": {
                "type": "float",
                "required": False,
                "description": "Distance to nearest downstream drinking-water intake.",
            },
            "water_stress_category": {
                "type": "str",
                "required": True,
                "allowed_values": ["low", "moderate", "high", "extreme"],
                "description": "Regional water stress classification.",
            },
            "ej_score": {
                "type": "float",
                "range": [0.0, 1.0],
                "required": False,
                "description": "Environmental justice / overburdened community index.",
            },
        },
    },

    "data_center": {
        "description": "Data-center design and operational characteristics.",
        "fields": {
            "cooling_type": {
                "type": "str",
                "required": True,
                "allowed_values": [
                    "evaporative",
                    "closed_loop",
                    "hybrid",
                    "air_cooled",
                ],
                "description": "Primary cooling technology.",
            },
            "max_daily_water_withdrawal_mgd": {
                "type": "float",
                "required": True,
                "units": "million gallons per day",
                "description": "Peak daily water withdrawal for cooling.",
            },
            "average_daily_water_withdrawal_mgd": {
                "type": "float",
                "required": False,
                "units": "million gallons per day",
            },
            "backup_generator_capacity_MW": {
                "type": "float",
                "required": False,
                "units": "megawatts",
                "description": "Backup diesel/gas generator capacity (for air/health co-impacts).",
            },
            "annual_energy_use_MWh": {
                "type": "float",
                "required": False,
                "units": "megawatt-hours per year",
                "description": "Total annual energy use estimate.",
            },
        },
    },

    "regulatory": {
        "description": "Regulatory parameters and flags tying the model to EPA PFAS rules.",
        "fields": {
            "use_hazard_index": {
                "type": "bool",
                "required": True,
                "default": True,
                "description": "Whether to apply the PFAS Hazard Index mixture approach.",
            },
            "use_mcl_check": {
                "type": "bool",
                "required": True,
                "default": True,
                "description": "Whether to enforce PFOA/PFOS MCL checks.",
            },
            "regulation_source": {
                "type": "str",
                "required": True,
                "default": "EPA Final PFAS NPDWR (2024–2025)",
            },
            "uncertainty_factor": {
                "type": "float",
                "required": False,
                "description": "Generic uncertainty margin applied to concentration or risk.",
            },
        },
    },

    "scenario_parameters": {
        "description": "Forward-looking assumptions for simulations.",
        "fields": {
            "time_horizon_years": {
                "type": "int",
                "required": True,
                "default": 10,
                "description": "Number of years to simulate PFAS behavior around the site.",
            },
            "pfas_decay_rate_per_year": {
                "type": "float",
                "required": False,
                "default": 0.0,
                "description": "Modeled annual decay/removal rate of PFAS (often near zero).",
            },
            "climate_change_factor": {
                "type": "float",
                "required": False,
                "default": 1.0,
                "description": "Multiplier for extreme events / runoff potential.",
            },
        },
    },

    "output_fields": {
        "description": "Fields the simulator should return to the API/UI and PDF exporter.",
        "fields": {
            "overall_risk_score_0_100": {
                "type": "float",
                "description": "Composite PFAS regulatory risk score (0 = minimal, 100 = severe).",
            },
            "risk_category": {
                "type": "str",
                "allowed_values": ["low", "moderate", "high", "severe"],
                "description": "Binned interpretation of the overall risk score.",
            },
            "mcl_violation_flag": {
                "type": "bool",
                "description": "True if any individual PFAS exceeds its MCL.",
            },
            "hazard_index_value": {
                "type": "float",
                "description": "Computed hazard index value for the PFAS mixture.",
            },
            "hazard_index_exceeds_1": {
                "type": "bool",
                "description": "True if HI > 1, indicating potential health concern.",
            },
            "dominant_pathway": {
                "type": "str",
                "description": "Which exposure pathway is most influential (e.g., 'groundwater', 'surface_water').",
            },
            "notes": {
                "type": "str",
                "description": "Free-text explanation or caveats for planners/regulators.",
            },
        },
    },
}


def get_schema_section(section_name: str) -> Dict[str, Any]:
    """
    Convenience helper to retrieve a named section of the schema.
    """
    return PFAS_RISK_MODEL_SCHEMA.get(section_name, {})


def list_all_fields() -> Dict[str, Dict[str, Any]]:
    """
    Flatten all schema fields into a single dict:
    { 'section.field_name': field_metadata }
    This can be used later for validation or documentation.
    """
    flattened: Dict[str, Dict[str, Any]] = {}
    for section_name, section in PFAS_RISK_MODEL_SCHEMA.items():
        fields = section.get("fields", {})
        for field_name, meta in fields.items():
            key = f"{section_name}.{field_name}"
            flattened[key] = meta
    return flattened


if __name__ == "__main__":
    # Simple debug print if you run: python src/simulation/model_schema.py
    import pprint

    print("PFAS chemicals:", PFAS_CHEMICALS)
    print("\nFlattened schema fields:")
    pprint.pprint(list_all_fields())
