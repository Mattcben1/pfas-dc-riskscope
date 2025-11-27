"""
map_renderer.py

Simple static map rendering for PFAS siting results.

- Plots PWS locations from data/metadata/pws_locations.csv
- Highlights the selected PWS / location
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd


PWS_CSV = Path("data/metadata/pws_locations.csv")


def render_hotspot_map(
    *,
    selected_lat: float,
    selected_lon: float,
    selected_label: str,
    output_path: Path,
    state_filter: Optional[str] = None,
) -> Path:
    """
    Render a simple scatter map of PWS locations and highlight the selected point.

    Args:
        selected_lat, selected_lon: coordinates of the simulated site
        selected_label: text label to show near the selected point
        output_path: path to save PNG
        state_filter: if provided, only show PWS in this state
    """
    if not PWS_CSV.exists():
        raise FileNotFoundError(f"PWS metadata not found at {PWS_CSV}")

    df = pd.read_csv(PWS_CSV)
    df.columns = [c.lower() for c in df.columns]

    if state_filter:
        df = df[df["state"].str.upper() == state_filter.upper()]

    if df.empty:
        # Fallback: just plot the selected point
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.scatter(selected_lon, selected_lat, marker="*", s=150)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title("PFAS DC RiskScope – Selected Location")
        ax.text(selected_lon, selected_lat, f"  {selected_label}", fontsize=8)
    else:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.scatter(df["lon"], df["lat"], alpha=0.4, label="PWS locations")
        ax.scatter(
            [selected_lon],
            [selected_lat],
            marker="*",
            s=150,
            label="Selected site",
        )

        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title("PFAS Monitoring Context and Selected Site")
        ax.legend(loc="lower left", fontsize=8)
        ax.text(selected_lon, selected_lat, f"  {selected_label}", fontsize=8)

    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return output_path
