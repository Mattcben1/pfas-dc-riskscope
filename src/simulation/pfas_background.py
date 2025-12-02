import pandas as pd
from pathlib import Path

UCMR5_PATH = Path("data/processed/ucmr5_state_medians.csv")

def load_ucmr5_background():
    if not UCMR5_PATH.exists():
        raise FileNotFoundError(f"UCMR5 file not found at: {UCMR5_PATH}")

    df = pd.read_csv(UCMR5_PATH)

    # compute median of all measured PFAS chemicals per state
    bg = df.groupby("STATE")["MEDIAN_PPT"].median().to_dict()

    # Convert any NaN to 0.0
    bg = {str(k).zfill(2): float(v) if pd.notna(v) else 0.0 for k, v in bg.items()}
    return bg
