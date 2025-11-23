"""
ucmr5_ingest.py

ETL for EPA UCMR5 dataset placed in data/raw/UCMR5_All.txt.

Steps:
- Load raw tab-delimited file
- Filter to PFAS contaminants (using PFAS_CHEM_INFO)
- Handle censored values (AnalyticalResultsSign = '<') as 0.0 for now
- Convert from µg/L to ppt (1 µg/L = 1000 ppt)
- Aggregate to state-level medians by contaminant
- Save to data/processed/ucmr5_state_medians.csv
"""

import pandas as pd
import numpy as np

# --- Ensure project root is on PYTHONPATH ---
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulation.pfas_mapping import PFAS_CHEM_INFO, is_pfas

RAW_PATH = Path("data/raw/UCMR5_All.txt")
OUT_MEDIANS = Path("data/processed/ucmr5_state_medians.csv")

UGL_TO_PPT = 1000.0  # 1 µg/L = 1000 ppt


def detect_state_column(df: pd.DataFrame) -> str:
    """
    Try to find the correct state column name.
    UCMR5 typically uses 'State'.
    """
    for cand in ["State", "STATE", "state"]:
        if cand in df.columns:
            return cand
    raise KeyError("Could not find a State column in UCMR5 input.")


def load_ucmr5_raw() -> pd.DataFrame:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Raw UCMR5 file not found at {RAW_PATH}")

    print("Loading UCMR5 raw file...")
    df = pd.read_csv(
        RAW_PATH,
        sep="\t",
        dtype=str,
        encoding="latin-1",
    )
    print(f"Loaded {len(df):,} rows with {len(df.columns)} columns.")
    return df


def clean_and_filter(df: pd.DataFrame) -> pd.DataFrame:
    # Normalize key columns
    if "Contaminant" not in df.columns:
        raise KeyError("Expected 'Contaminant' column in UCMR5.")

    state_col = detect_state_column(df)

    df["Contaminant"] = df["Contaminant"].astype(str).str.upper().str.strip()
    df[state_col] = df[state_col].astype(str).str.upper().str.strip()

    # Filter to rows that are PFAS (based on mapping)
    mask_pfas = df["Contaminant"].apply(is_pfas)
    df_pfas = df[mask_pfas].copy()

    print(f"Filtered to {len(df_pfas):,} PFAS rows (from {len(df):,} total).")

    if df_pfas.empty:
        print("WARNING: No PFAS rows matched PFAS_CHEM_INFO. Check mapping.")
        return df_pfas

    # Handle censored values & convert units

    if "AnalyticalResultValue" not in df_pfas.columns:
        raise KeyError("Expected 'AnalyticalResultValue' column in UCMR5.")
    if "AnalyticalResultsSign" not in df_pfas.columns:
        # Some rows may not have sign; create a neutral one
        df_pfas["AnalyticalResultsSign"] = ""

    # Replace non-numeric values as NaN, but treat '<' as 0 for now.
    # You could also use half MRL here if desired.
    signs = df_pfas["AnalyticalResultsSign"].astype(str).str.strip()
    vals = pd.to_numeric(df_pfas["AnalyticalResultValue"], errors="coerce")

    # Censored values -> 0
    censored_mask = signs == "<"
    vals.loc[censored_mask] = 0.0

    df_pfas["value_ugl"] = vals

    # Drop missing numeric values
    before_drop = len(df_pfas)
    df_pfas = df_pfas.dropna(subset=["value_ugl"])
    print(f"Dropped {before_drop - len(df_pfas):,} rows with non-numeric values.")

    # Convert to ppt
    df_pfas["value_ppt"] = df_pfas["value_ugl"] * UGL_TO_PPT

    # Attach canonical PFAS name & category from mapping
    df_pfas["CONTAMINANT_STD"] = df_pfas["Contaminant"].map(
        lambda c: PFAS_CHEM_INFO[c]["canonical_name"]
    )
    df_pfas["CATEGORY"] = df_pfas["Contaminant"].map(
        lambda c: PFAS_CHEM_INFO[c]["category"]
    )
    df_pfas["STATE_STD"] = df_pfas[state_col]

    return df_pfas


def aggregate_state_medians(df_pfas: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate PFAS data to state-level stats:

    - MEDIAN_PPT: median concentration in ppt
    - MAX_PPT: max concentration in ppt
    - N_SAMPLES: number of samples
    - PCT_DETECTED: % of samples with value_ppt > 0
    - PCT_CENSORED: % of samples with value_ppt == 0
    """
    if df_pfas.empty:
        # Create an empty shell so downstream code still works
        return pd.DataFrame(
            columns=[
                "STATE",
                "CONTAMINANT",
                "MEDIAN_PPT",
                "MAX_PPT",
                "N_SAMPLES",
                "PCT_DETECTED",
                "PCT_CENSORED",
            ]
        )

    grouped = df_pfas.groupby(["STATE_STD", "CONTAMINANT_STD"])["value_ppt"]

    agg = grouped.agg(
        MEDIAN_PPT="median",
        MAX_PPT="max",
        N_SAMPLES="size",
        N_NONZERO=lambda s: (s > 0).sum(),
    ).reset_index()

    # Compute detection / censored percentages
    agg["PCT_DETECTED"] = (agg["N_NONZERO"] / agg["N_SAMPLES"]) * 100.0
    agg["PCT_CENSORED"] = 100.0 - agg["PCT_DETECTED"]

    agg = agg.rename(
        columns={
            "STATE_STD": "STATE",
            "CONTAMINANT_STD": "CONTAMINANT",
        }
    ).drop(columns=["N_NONZERO"])

    # Sort for readability
    agg = agg.sort_values(["STATE", "CONTAMINANT"]).reset_index(drop=True)

    return agg


def main():
    df_raw = load_ucmr5_raw()
    df_pfas = clean_and_filter(df_raw)
    df_medians = aggregate_state_medians(df_pfas)

    OUT_MEDIANS.parent.mkdir(parents=True, exist_ok=True)
    df_medians.to_csv(OUT_MEDIANS, index=False)

    print(f"[OK] Saved state PFAS medians → {OUT_MEDIANS}")
    print(f"Rows in medians file: {len(df_medians):,}")

    # Quick example for VA
    ex = df_medians[df_medians["STATE"] == "VA"]
    print("\nExample — median PFAS for VA:")
    print(ex.head(20))


if __name__ == "__main__":
    main()
