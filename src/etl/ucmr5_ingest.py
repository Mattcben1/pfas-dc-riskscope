# src/etl/ucmr5_ingest.py

"""
UCMR5 ingestion that matches your raw UCMR5_All.txt file:
- Tab-delimited
- Latin-1 encoded
- Units column shows “�g/L” meaning µg/L
- Convert µg/L → ppt (1 µg/L = 1000 ppt)
- Compute per-state *all-chemical* medians + TOTAL_PFAS
"""

from pathlib import Path
import pandas as pd
import numpy as np

RAW_FILE = Path("data/raw/UCMR5_All.txt")
PROCESSED_FILE = Path("data/processed/ucmr5_state_medians.csv")

EXPECTED_COLS = {
    "PWSID", "PWSName", "CollectionDate", "Contaminant",
    "AnalyticalResultsSign", "AnalyticalResultValue", "State", "Units"
}


def load_ucmr5_background() -> dict:
    """
    Returns dict structure:
    {
        "51": {
            "PFOA": 1.2,
            "PFOS": 0.9,
            "PFHxS": 0.4,
            ...
            "TOTAL_PFAS": 7.5
        },
        ...
    }
    Units are ppt.
    """

    # If processed version already exists, load it
    if PROCESSED_FILE.exists():
        print("Loaded cached UCMR5 medians.")
        df = pd.read_csv(PROCESSED_FILE)
        return _df_to_state_map(df)

    print("Building per-state, per-chemical medians from UCMR5…")

    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Missing raw UCMR5 file at {RAW_FILE}")

    # --- Your UCMR5 file format: tab-delimited, Latin-1 ---
    df = pd.read_csv(
        RAW_FILE,
        sep="\t",
        encoding="latin1",
        low_memory=False
    )

    # Check columns
    missing = EXPECTED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"Raw UCMR5 file missing expected columns: {missing}")

    # Keep only PFAS contaminants
    df = df[df["Contaminant"].str.contains("PF", na=False)]

    # Convert to numeric; nondetects are "<" and become NaN → 0 after replacement
    df["AnalyticalResultValue"] = pd.to_numeric(
        df["AnalyticalResultValue"], errors="coerce"
    )

    # Convert µg/L → ppt  (1 µg/L = 1000 ppt)
    df["ppt"] = df["AnalyticalResultValue"] * 1000

    # Replace nondetects with 0 ppt
    df.loc[df["AnalyticalResultsSign"] == "<", "ppt"] = 0.0

    # Normalize state FIPS code
    df["State"] = df["State"].astype(str).str.zfill(2)

    # ------------------------------
    # Compute per-state, per-chemical medians
    # ------------------------------
    grouped = (
        df.groupby(["State", "Contaminant"])["ppt"]
        .median()
        .reset_index()
    )

    # ------------------------------
    # Compute TOTAL_PFAS per state
    # ------------------------------
    totals = (
        grouped.groupby("State")["ppt"]
        .sum()
        .reset_index()
        .rename(columns={"ppt": "TOTAL_PFAS"})
    )

    # Merge total back into grouped
    totals["Contaminant"] = "TOTAL_PFAS"
    merged = pd.concat([grouped, totals], ignore_index=True)

    # Store processed file
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(PROCESSED_FILE, index=False)

    return _df_to_state_map(merged)


def _df_to_state_map(df: pd.DataFrame) -> dict:
    """
    Convert long DF into nested dict:

      {
        "51": {"PFOA": 2.1, "PFOS": 1.9, "TOTAL_PFAS": 7.5}
      }
    """

    out = {}

    for _, row in df.iterrows():
        state = str(row["State"]).zfill(2)
        chem = str(row["Contaminant"])
        val = float(row["ppt"])

        if state not in out:
            out[state] = {}

        out[state][chem] = val

    return out
