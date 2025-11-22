from pathlib import Path
import pandas as pd
from typing import Dict, Optional, List

# Default location of the raw file
DEFAULT_PATH = Path("data/raw/UCMR5_All.txt")

# Relevant EPA-regulated PFAS for 2024 MCL + Hazard Index
TARGET_CHEMICALS = {
    "PFOA": ["PFOA"],
    "PFOS": ["PFOS"],
    "PFHxS": ["PFHxS"],
    "PFNA": ["PFNA"],
    "PFBS": ["PFBS"],
    "HFPO-DA": ["HFPO-DA", "GENX", "HFPO-DA"],
}


def load_ucmr5(path: Optional[Path] = None) -> pd.DataFrame:
    """Load the UCMR5 dataset with encoding handling."""
    if path is None:
        path = DEFAULT_PATH

    if not path.exists():
        raise FileNotFoundError(f"Cannot find {path}")

    try:
        df = pd.read_csv(path, sep="\t", dtype=str, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(path, sep="\t", dtype=str, encoding="latin1")

    df.columns = [c.strip().upper() for c in df.columns]

    df["ANALYTICALRESULTVALUE"] = pd.to_numeric(
        df["ANALYTICALRESULTVALUE"], errors="coerce"
    )

    df = df.dropna(subset=["ANALYTICALRESULTVALUE"])
    df["CONTAMINANT"] = df["CONTAMINANT"].str.upper()
    df["UNITS"] = df["UNITS"].str.upper()

    return df


def convert_to_ppt(df: pd.DataFrame) -> pd.DataFrame:
    """Convert concentrations to ppt (ng/L)."""
    df = df.copy()

    ugr_mask = df["UNITS"].str.contains("UG/L") | df["UNITS"].str.contains("µG/L")
    df.loc[ugr_mask, "PPT"] = df.loc[ugr_mask, "ANALYTICALRESULTVALUE"] * 1000

    ppt_mask = df["UNITS"].str.contains("PPT")
    df.loc[ppt_mask, "PPT"] = df.loc[ppt_mask, "ANALYTICALRESULTVALUE"]

    return df.dropna(subset=["PPT"])


def compute_state_medians(df: pd.DataFrame) -> pd.DataFrame:
    """Group by state + chemical and compute median."""
    grouped = (
        df.groupby(["STATE", "CONTAMINANT"])["PPT"]
        .median()
        .reset_index()
        .rename(columns={"PPT": "MEDIAN_PPT"})
    )
    return grouped


def save_processed(df: pd.DataFrame, path: str = "data/processed/ucmr5_state_medians.csv"):
    """Save processed medians to data/processed."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"[OK] Saved processed file → {out_path}")


if __name__ == "__main__":
    print("Loading UCMR5...")
    df = load_ucmr5()

    print("Converting values to ppt...")
    df = convert_to_ppt(df)

    print("Computing state medians...")
    med = compute_state_medians(df)

    print("Saving processed file...")
    save_processed(med)

    print("\nExample — median PFAS for VA:")
    print(med[med["STATE"] == "VA"])
