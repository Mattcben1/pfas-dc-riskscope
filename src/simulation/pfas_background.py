"""
pfas_background.py

Loads state-level PFAS background concentrations (median, in ppt)
from the processed UCMR5 dataset.

Output shape (from load_background):

{
    "VA": {
        "PFOA": 3.2,
        "PFOS": 4.7,
        ...
    },
    "CA": { ... },
    ...
    "US": { ... }   # national medians across all states
}
"""

from pathlib import Path
from typing import Dict

import pandas as pd

PFAS_MEDIANS_PATH = Path("data/processed/ucmr5_state_medians.csv")


def load_background() -> Dict[str, Dict[str, float]]:
    """
    Load state-level PFAS medians from the processed UCMR5 file.

    Returns:
        dict: mapping STATE -> { CONTAMINANT -> MEDIAN_PPT }
    """
    if not PFAS_MEDIANS_PATH.exists():
        raise FileNotFoundError(
            f"Processed PFAS medians file not found at {PFAS_MEDIANS_PATH}"
        )

    df = pd.read_csv(PFAS_MEDIANS_PATH)

    # Normalize columns
    df["STATE"] = df["STATE"].astype(str).str.strip().str.upper()
    df["CONTAMINANT"] = df["CONTAMINANT"].astype(str).str.strip().str.upper()

    # Try to coerce medians to float
    df["MEDIAN_PPT"] = pd.to_numeric(df["MEDIAN_PPT"], errors="coerce")

    # Drop rows with missing or non-positive medians
    df = df.dropna(subset=["MEDIAN_PPT"])
    df = df[df["MEDIAN_PPT"] >= 0]

    # Build state -> chem -> value dict
    state_to_chem: Dict[str, Dict[str, float]] = {}

    for _, row in df.iterrows():
        state = row["STATE"]
        chem = row["CONTAMINANT"]
        value = float(row["MEDIAN_PPT"])

        if state not in state_to_chem:
            state_to_chem[state] = {}

        # If multiple facilities per state/chemical, this will just keep
        # the last one. If you want to aggregate, do that earlier in ETL.
        state_to_chem[state][chem] = value

    # Build a simple national median per chemical for fallback ("US")
    nat: Dict[str, float] = {}
    for chem, sub in df.groupby("CONTAMINANT"):
        vals = sub["MEDIAN_PPT"].dropna()
        if not vals.empty:
            nat[chem] = float(vals.median())

    state_to_chem["US"] = nat

    return state_to_chem


if __name__ == "__main__":
    bg = load_background()
    print(f"Loaded background for {len(bg)} regions (including 'US').")

    for key in sorted(bg.keys())[:10]:
        print(f"{key}: {len(bg[key])} chemicals")
