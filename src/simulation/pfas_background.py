"""
pfas_background.py

Loads state-level PFAS background concentrations and statistics
from the processed UCMR5 dataset:

data/processed/ucmr5_state_medians.csv

Expected columns:
- STATE          (FIPS code like '01', '51', etc.)
- CONTAMINANT    (canonical PFAS name: PFOA, PFOS, HFPO-DA, etc.)
- MEDIAN_PPT
- MAX_PPT
- N_SAMPLES
- PCT_DETECTED
- PCT_CENSORED

We expose two main loaders:

- load_background() / load_background_medians():
    Returns state -> contaminant -> median_ppt (float)

- load_background_stats():
    Returns state -> contaminant -> {
        'median_ppt', 'max_ppt', 'n_samples',
        'pct_detected', 'pct_censored'
    }

We also synthesize a "US" profile as a simple national median
for each contaminant across all states.
"""

from pathlib import Path
from typing import Dict, Any

import pandas as pd

PFAS_MEDIANS_PATH = Path("data/processed/ucmr5_state_medians.csv")


# Basic FIPS → state abbreviation mapping for all 50 states + DC
FIPS_TO_STATE = {
    "01": "AL",
    "02": "AK",
    "04": "AZ",
    "05": "AR",
    "06": "CA",
    "08": "CO",
    "09": "CT",
    "10": "DE",
    "11": "DC",
    "12": "FL",
    "13": "GA",
    "15": "HI",
    "16": "ID",
    "17": "IL",
    "18": "IN",
    "19": "IA",
    "20": "KS",
    "21": "KY",
    "22": "LA",
    "23": "ME",
    "24": "MD",
    "25": "MA",
    "26": "MI",
    "27": "MN",
    "28": "MS",
    "29": "MO",
    "30": "MT",
    "31": "NE",
    "32": "NV",
    "33": "NH",
    "34": "NJ",
    "35": "NM",
    "36": "NY",
    "37": "NC",
    "38": "ND",
    "39": "OH",
    "40": "OK",
    "41": "OR",
    "42": "PA",
    "44": "RI",
    "45": "SC",
    "46": "SD",
    "47": "TN",
    "48": "TX",
    "49": "UT",
    "50": "VT",
    "51": "VA",
    "53": "WA",
    "54": "WV",
    "55": "WI",
    "56": "WY",
}


def _load_raw_background_df() -> pd.DataFrame:
    """
    Load the processed state-level PFAS stats file.
    """
    if not PFAS_MEDIANS_PATH.exists():
        raise FileNotFoundError(
            f"Processed PFAS medians file not found at {PFAS_MEDIANS_PATH}"
        )

    df = pd.read_csv(PFAS_MEDIANS_PATH)

    # Normalize column names we expect
    required_cols = {
        "STATE",
        "CONTAMINANT",
        "MEDIAN_PPT",
        "MAX_PPT",
        "N_SAMPLES",
        "PCT_DETECTED",
        "PCT_CENSORED",
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing columns in {PFAS_MEDIANS_PATH}: {', '.join(sorted(missing))}"
        )

    # Normalize state codes and contaminants
    df["STATE"] = df["STATE"].astype(str).str.zfill(2)  # '1' -> '01'
    df["STATE_ABBR"] = df["STATE"].map(FIPS_TO_STATE).fillna(df["STATE"])
    df["CONTAMINANT"] = df["CONTAMINANT"].astype(str).str.upper().str.strip()

    # Coerce numeric columns
    for col in [
        "MEDIAN_PPT",
        "MAX_PPT",
        "N_SAMPLES",
        "PCT_DETECTED",
        "PCT_CENSORED",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows with no contaminant or no samples
    df = df.dropna(subset=["CONTAMINANT", "N_SAMPLES"])
    df = df[df["N_SAMPLES"] > 0]

    return df


def load_background_medians() -> Dict[str, Dict[str, float]]:
    """
    Return a nested dict:

    {
      "VA": {
        "PFOA": 0.0,
        "PFOS": 0.0,
        ...
      },
      "CA": { ... },
      ...
      "US": { ... }   # national median per contaminant
    }

    Uses MEDIAN_PPT as the core value.
    """
    df = _load_raw_background_df()

    state_to_chem: Dict[str, Dict[str, float]] = {}

    for _, row in df.iterrows():
        state = row["STATE_ABBR"]
        chem = row["CONTAMINANT"]
        median = float(row["MEDIAN_PPT"]) if pd.notna(row["MEDIAN_PPT"]) else 0.0

        if state not in state_to_chem:
            state_to_chem[state] = {}
        state_to_chem[state][chem] = median

    # Build national medians ("US")
    nat: Dict[str, float] = {}
    for chem, sub in df.groupby("CONTAMINANT"):
        vals = sub["MEDIAN_PPT"].dropna()
        if not vals.empty:
            nat[chem] = float(vals.median())

    state_to_chem["US"] = nat

    return state_to_chem


def load_background_stats() -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    Return a richer nested dict:

    {
      "VA": {
        "PFOA": {
          "median_ppt": ...,
          "max_ppt": ...,
          "n_samples": ...,
          "pct_detected": ...,
          "pct_censored": ...,
        },
        "PFOS": { ... },
        ...
      },
      "CA": { ... },
      ...
      "US": { ... }   # national stats per contaminant
    }
    """
    df = _load_raw_background_df()

    state_stats: Dict[str, Dict[str, Dict[str, float]]] = {}

    for _, row in df.iterrows():
        state = row["STATE_ABBR"]
        chem = row["CONTAMINANT"]

        if state not in state_stats:
            state_stats[state] = {}

        state_stats[state][chem] = {
            "median_ppt": float(row["MEDIAN_PPT"]) if pd.notna(row["MEDIAN_PPT"]) else 0.0,
            "max_ppt": float(row["MAX_PPT"]) if pd.notna(row["MAX_PPT"]) else 0.0,
            "n_samples": float(row["N_SAMPLES"]) if pd.notna(row["N_SAMPLES"]) else 0.0,
            "pct_detected": float(row["PCT_DETECTED"]) if pd.notna(row["PCT_DETECTED"]) else 0.0,
            "pct_censored": float(row["PCT_CENSORED"]) if pd.notna(row["PCT_CENSORED"]) else 0.0,
        }

    # Build national stats ("US")
    nat: Dict[str, Dict[str, float]] = {}
    for chem, sub in df.groupby("CONTAMINANT"):
        med = sub["MEDIAN_PPT"].dropna()
        mx = sub["MAX_PPT"].dropna()
        n = sub["N_SAMPLES"].dropna()
        det = sub["PCT_DETECTED"].dropna()
        cen = sub["PCT_CENSORED"].dropna()

        nat[chem] = {
            "median_ppt": float(med.median()) if not med.empty else 0.0,
            "max_ppt": float(mx.max()) if not mx.empty else 0.0,
            "n_samples": float(n.sum()) if not n.empty else 0.0,
            "pct_detected": float(det.mean()) if not det.empty else 0.0,
            "pct_censored": float(cen.mean()) if not cen.empty else 0.0,
        }

    state_stats["US"] = nat

    return state_stats


# For backward compatibility with earlier code:
# load_background() = medians-only view
def load_background() -> Dict[str, Dict[str, float]]:
    return load_background_medians()


if __name__ == "__main__":
    # Simple debug/printout
    med = load_background_medians()
    stats = load_background_stats()

    print(f"Loaded medians for {len(med)} regions (including 'US').")
    for region in sorted(med.keys())[:10]:
        print(f"{region}: {len(med[region])} chemicals (medians only)")

    print("\nExample detailed stats for VA (if present):")
    va_stats: Dict[str, Any] = stats.get("VA", {})
    for chem, info in list(va_stats.items())[:10]:
        print(f"  {chem}: {info}")
