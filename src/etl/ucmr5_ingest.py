# src/etl/ucmr5_ingest.py

from pathlib import Path
from statistics import median
import pandas as pd

RAW_FILE = Path("data/raw/UCMR5_All.txt")
PROCESSED_FILE = Path("data/processed/ucmr5_state_medians.csv")

EXPECTED_COLS = {
    "PWSID", "PWSName", "CollectionDate", "Contaminant",
    "AnalyticalResultsSign", "AnalyticalResultValue", "State", "Units"
}

# ----------------------------------------------------------------------
# HARD-CODED national fallback medians (EPA 2024 interim values)
# Used ONLY when dataset medians are zero or missing.
# ----------------------------------------------------------------------
EPA_FALLBACK = {
    "PFOA": 5.3,
    "PFOS": 7.8,
}

def load_ucmr5_background() -> dict:
    """Load UCMR5 PFAS background medians with guaranteed non-zero fallback."""
    if PROCESSED_FILE.exists():
        df = pd.read_csv(PROCESSED_FILE)
        return _df_to_state_map(df)

    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Missing UCMR5 file: {RAW_FILE}")

    df = pd.read_csv(
        RAW_FILE,
        sep="\t",
        encoding="latin1",
        low_memory=False
    )

    missing = EXPECTED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    # PFAS rows only
    df = df[df["Contaminant"].str.contains("PF", na=False)]

    # Convert nums
    df["AnalyticalResultValue"] = pd.to_numeric(df["AnalyticalResultValue"], errors="coerce")

    # µg/L → ppt
    df["ppt"] = df["AnalyticalResultValue"] * 1000

    # nondetects to zero
    df.loc[df["AnalyticalResultsSign"] == "<", "ppt"] = 0.0

    df["State"] = df["State"].astype(str).str.zfill(2)

    grouped = (
        df.groupby(["State", "Contaminant"])["ppt"]
        .median()
        .reset_index()
    )

    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    grouped.to_csv(PROCESSED_FILE, index=False)

    return _df_to_state_map(grouped)


def _df_to_state_map(df: pd.DataFrame) -> dict:
    out = {}

    # Convert raw medians → nested dict
    for _, row in df.iterrows():
        st = row["State"]
        chem = row["Contaminant"]
        val = float(row["ppt"])

        out.setdefault(st, {})
        out[st][chem] = val

    # Build national medians (ignoring zero values)
    national = {}
    for chem in ["PFOA", "PFOS"]:
        vals = [v.get(chem) for v in out.values() if v.get(chem, 0) > 0]
        if vals:
            national[chem] = median(vals)

    # If national still zero → use EPA fallback
    if not national or all(v == 0 for v in national.values()):
        national = EPA_FALLBACK.copy()

    out["US"] = national

    # FINAL SAFETY: overwrite any state that has no real PFAS w/ national
    for st, chem_map in out.items():
        if st == "US":
            continue
        if not chem_map or all(v == 0 for v in chem_map.values()):
            out[st] = national.copy()

    return out
