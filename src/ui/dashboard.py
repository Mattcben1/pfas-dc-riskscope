import streamlit as st
import requests
import geopandas as gpd
from shapely.geometry import Point

API_URL = "http://localhost:8080/simulate"  # Your FastAPI container endpoint


st.set_page_config(page_title="PFAS-DC RiskScope Dashboard", layout="wide")
st.title("🧭 PFAS-DC RiskScope — Environmental & Regulatory Dashboard")

st.subheader("Select Data Center Location")


# --- 1. Map Input ---
# Create blank map center or use a real dataset later
default_lat, default_lon = 38.9, -77.4  # Northern VA center point


clicked_point = st.map(
    data=gpd.GeoDataFrame(
        geometry=[Point(default_lon, default_lat)],
        crs="EPSG:4326"
    )
)

st.markdown("Click on the map to select a potential data center site.")


# --- 2. User Input for Environmental Parameters ---
st.sidebar.header("Environmental Factors")

gw_vulnerability = st.sidebar.slider(
    "Groundwater Vulnerability (0=Low, 1=High)",
    0.0, 1.0, 0.3
)

surface_water_distance = st.sidebar.slider(
    "Distance to Nearest Surface Water (km)",
    0.1, 20.0, 3.0
)

water_stress = st.sidebar.selectbox(
    "Water Stress Category",
    ["low", "moderate", "high"]
)

ej_score = st.sidebar.slider(
    "Environmental Justice Index (0–1)",
    0.0, 1.0, 0.2
)


# --- 3. Trigger Simulation ---
if st.button("Run PFAS Risk Simulation"):

    # Placeholder values until map clicks are wired
    payload = {
        "chemicals": {
            "concentrations_ppt": {
                "PFOA": 2,
                "PFOS": 3,
                "PFHxS": 0.1,
                "PFNA": 0.05,
                "HFPO-DA": 0.01,
                "PFBS": 0.2
            }
        },
        "environmental_factors": {
            "groundwater_vulnerability_index": gw_vulnerability,
            "surface_water_distance_km": surface_water_distance,
            "water_stress_category": water_stress,
            "ej_score": ej_score,
        },
        "data_center": {
            "cooling_type": "closed_loop",
            "max_daily_water_withdrawal_mgd": 1.5,
        },
        "scenario_parameters": {
            "time_horizon_years": 10
        }
    }

    response = requests.post(API_URL, json=payload)

    if response.status_code == 200:
        result = response.json()
        st.success("Simulation Complete")

        st.json(result)

    else:
        st.error("Simulation API Error")
