import pandas as pd
from pathlib import Path
from typing import Dict

DEFAULT_PATH = Path("data/processed/ucmr5_state_medians.csv")

# Map contaminants to normalized EPA names
EPA_PFAS = {
    "PFOA": ["PFOA"],
    "PFOS": ["PFOS"],
    "PFHxS": ["PFHXS"],
    "PFNA": ["PFNA"],
    "PFBS": ["PFBS"],
    "HFPO-DA": ["HFPO-DA", "GENX", "HFPO-DA"],
}


def load_background(path: Path = DEFAULT_PATH) -> Dict[str, Dict[str, float]]:
    """Load state PFAS medians into nested dict structure."""
    if not path.exists():
        raise FileNotFoundError(f"Processed medians file not found at {path}")

    df = pd.read_csv(path)

    # Build state → contaminant → median map
    result = {}

    for state in df["STATE"].unique():
        state_df = df[df["STATE"] == state]

        state_data = {}

        for epa_name, synonyms in EPA_PFAS.items():
            match = state_df[state_df["CONTAMINANT"].isin(synonyms)]
            if not match.empty:
                state_data[epa_name] = float(match["MEDIAN_PPT"].median())
            else:
                state_data[epa_name] = 0.0  # nondetects

        result[state] = state_data

    return result


if __name__ == "__main__":
    bg = load_background()
    print("Example state background for VA:")
    print(bg.get("VA", {}))

