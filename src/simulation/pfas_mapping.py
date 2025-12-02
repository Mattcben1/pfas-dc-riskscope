"""
pfas_mapping.py

Defines metadata for PFAS contaminants found in the UCMR5 dataset.

Each key is the EXACT uppercase name from the UCMR5 "Contaminant" column.
"""

from typing import Dict, Literal, TypedDict

Category = Literal[
    "MCL",
    "HazardIndex",
    "OtherPFAS",
    "ReplacementPFAS",
    "Fluorotelomer",
    "Precursor",
]

class PFASInfo(TypedDict):
    canonical_name: str
    category: Category
    include_in_medians: bool
    include_in_reg_risk: bool


PFAS_CHEM_INFO: Dict[str, PFASInfo] = {
    # --- MCL & Hazard Index PFAS (EPA-regulated set) ---
    "PFOA": {
        "canonical_name": "PFOA",
        "category": "MCL",
        "include_in_medians": True,
        "include_in_reg_risk": True,
    },
    "PFOS": {
        "canonical_name": "PFOS",
        "category": "MCL",
        "include_in_medians": True,
        "include_in_reg_risk": True,
    },
    "PFHXS": {
        "canonical_name": "PFHxS",
        "category": "HazardIndex",
        "include_in_medians": True,
        "include_in_reg_risk": True,
    },
    "PFNA": {
        "canonical_name": "PFNA",
        "category": "HazardIndex",
        "include_in_medians": True,
        "include_in_reg_risk": True,
    },
    "PFBS": {
        "canonical_name": "PFBS",
        "category": "HazardIndex",
        "include_in_medians": True,
        "include_in_reg_risk": True,
    },
    "HFPO-DA": {
        "canonical_name": "HFPO-DA",  # GenX
        "category": "HazardIndex",
        "include_in_medians": True,
        "include_in_reg_risk": True,
    },

    # --- Other carboxylic acids and sulfonic acids in UCMR5 ---
    "PFHPS": {
        "canonical_name": "PFHpS",
        "category": "OtherPFAS",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "PFPES": {
        "canonical_name": "PFPeS",
        "category": "OtherPFAS",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "PFPEA": {
        "canonical_name": "PFPeA",
        "category": "OtherPFAS",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "PFBA": {
        "canonical_name": "PFBA",
        "category": "OtherPFAS",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "PFHXA": {
        "canonical_name": "PFHxA",
        "category": "OtherPFAS",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "PFHPA": {
        "canonical_name": "PFHpA",
        "category": "OtherPFAS",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "PFDA": {
        "canonical_name": "PFDA",
        "category": "OtherPFAS",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "PFDOA": {
        "canonical_name": "PFDoA",
        "category": "OtherPFAS",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "PFUNA": {
        "canonical_name": "PFUnA",
        "category": "OtherPFAS",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "PFTRDA": {
        "canonical_name": "PFTrDA",
        "category": "OtherPFAS",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "PFTA": {
        "canonical_name": "PFTA",
        "category": "OtherPFAS",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "PFMPA": {
        "canonical_name": "PFMPA",
        "category": "OtherPFAS",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },

    # --- Replacement PFAS / novel chemistries ---
    "ADONA": {
        "canonical_name": "ADONA",
        "category": "ReplacementPFAS",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "NFDHA": {
        "canonical_name": "NFDHA",
        "category": "ReplacementPFAS",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "PFEESA": {
        "canonical_name": "PFEESA",
        "category": "ReplacementPFAS",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "PFMBA": {
        "canonical_name": "PFMBA",
        "category": "ReplacementPFAS",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },

    # --- Fluorotelomer & precursors ---
    "4:2 FTS": {
        "canonical_name": "4:2 FTS",
        "category": "Fluorotelomer",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "6:2 FTS": {
        "canonical_name": "6:2 FTS",
        "category": "Fluorotelomer",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "8:2 FTS": {
        "canonical_name": "8:2 FTS",
        "category": "Fluorotelomer",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "NETFOSAA": {
        "canonical_name": "NETFOSAA",
        "category": "Precursor",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "NMEFOSAA": {
        "canonical_name": "NMEFOSAA",
        "category": "Precursor",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "9CL-PF3ONS": {
        "canonical_name": "9Cl-PF3ONS",
        "category": "Precursor",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },
    "11CL-PF3OUDS": {
        "canonical_name": "11Cl-PF3OUDS",
        "category": "Precursor",
        "include_in_medians": True,
        "include_in_reg_risk": False,
    },

    # We explicitly DO NOT treat LITHIUM as PFAS.
}


def is_pfas(name: str) -> bool:
    return name.upper().strip() in PFAS_CHEM_INFO
def map_point_to_region(lat: float, lon: float) -> str:
    """
    Classify the clicked location into a region label.
    Placeholder logic for now.
    """

    if 37.8 <= lat <= 39.5 and -79 <= lon <= -76:
        return "Northern VA"

    if 38 <= lat <= 40 and -77.5 <= lon <= -74:
        return "Maryland"

    return "US-OTHER"
