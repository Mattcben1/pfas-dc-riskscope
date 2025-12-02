# src/etl/ucmr5_ingest.py
import csv
from pathlib import Path

PROCESSED_FILE = Path("data/processed/ucmr5_state_medians.csv")

def load_ucmr5_background():
    """
    Loads precomputed PFAS medians (ppt) per state.
    No pandas, no ETL, no large data processing.
    Returns:
      {
         "51": {"PFOA":4.2, "PFOS":3.8},
         "24": {...}
      }
    """
    if not PROCESSED_FILE.exists():
        print("WARNING: Missing PFAS processed file.")
        return {}

    state_map = {}

    with open(PROCESSED_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            state = row["State"].zfill(2)
            chem = row["Contaminant"]
            ppt = float(row["ppt"])

            if state not in state_map:
                state_map[state] = {}

            state_map[state][chem] = ppt

    return state_map

