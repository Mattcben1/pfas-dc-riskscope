# PFAS DC RiskScope

A geospatial PFAS risk-screening tool built for the DS 3001 Final Case Study.

This project estimates PFAS concentration changes associated with data-center development by combining environmental datasets, hydrologic mixing logic, regulatory thresholds, and an interactive map interface.

---

## Project Overview

This system models PFAS (“forever chemicals”) risk near user-selected locations by integrating:

- Real EPA UCMR5 PFAS measurements (2023 release)
- Reverse-geocoded state identification (OpenStreetMap Nominatim)
- A simplified river-mixing hydrology model
- EPA regulatory limits and hazard-index methodology
- A static web dashboard and one-click PDF reporting

Users click a location on a map, load the environmental context, run a simulation, and export a formatted PDF summary.

This project applies core Systems 1 concepts:  
FastAPI routing, Docker containerization, ETL pipelines, environment-variable management, client-side UI, and automated report generation.

---

## Architecture Summary

**End-to-end flow:**

1. User clicks a location on the Leaflet map.
2. `/simulate-location` reverse-geocodes the point and retrieves state-level PFAS medians.
3. ETL pipeline ingests the UCMR5 dataset, converts raw units, and computes per-state medians.
4. The simulation engine mixes upstream PFAS with data-center discharge under different hydrologic conditions.
5. Regulatory logic evaluates MCL exceedances and the PFAS hazard index.
6. `/export-pdf` generates a one-page simulation report.

All services run within a single containerized FastAPI application.

---

## How to Run (Docker Recommended)

```bash
docker build -t pfas:latest .
docker run --rm -p 8080:8080 pfas:latest
```
Then open: http://localhost:8080/map
Workflow:

-Click anywhere on the map
-Auto-filled values load: state, PFAS background, hydrology
-Click Go to Dashboard
-Run the simulation
-Export the final PDF risk report

# Key Design Decisions

**FastAPI** – Chosen for fast development, built-in validation, and clean routing  
**UCMR5 Dataset** – Large, real environmental dataset; provides state-level PFAS medians  
**Median PFAS per State** – Balances realism with computational simplicity  
**Mixing Model** – Simple but interpretable (river flow + discharge)  
**PDF Output** – Enables reporting-ready scientific deliverables  

---

# Security & Ethical Considerations

- No personal data collected; only map coordinates are processed.  
- Nominatim requests include a compliant User-Agent string.  
- Sensitive configs stored in `.env` (not committed) with `env.txt` / `.env.example` provided.  
- EPA PFAS data is public scientific data, used for learning—not regulatory decision-making.  
- The tool avoids claiming certainty; all results are screening-level estimates only.  

---

# Testing

A minimal but functional test suite is included:

**tests/test_api.py**  
- Verifies `/health` returns OK  
- Validates `/simulate` returns correct structure  
- Confirms `/simulate-location` returns a state + background PFAS values  

**Docker-based testing** ensures the entire app runs in a reproducible environment.

---

# Results & Validation

- ETL pipeline parses and cleans the UCMR5 raw dataset.  
- Background PFAS levels are computed as **medians per state**.  
- The simulation outputs:
  - downstream PFAS concentrations  
  - hazard index  
  - MCL exceedances  
  - overall **0–100 risk score**  

- `/simulate`, `/simulate-location`, and `/export-pdf` all function in Docker.  
- The final PDF report includes:
  - location  
  - PFAS values  
  - risk category  
  - MCL interpretation  

Screenshots included in `assets/screenshots/`.

---

# What I Learned

This project strengthened skills in:

- Dockerized API development  
- ETL workflows for large environmental datasets  
- Reverse geocoding + mapping (Leaflet + Nominatim)  
- Environmental modeling concepts (PFAS, hazard index, water mixing)  
- Environment variables and secure configuration  
- Reproducible scientific reporting via PDF generation  

It also demonstrated how environmental science and data engineering connect in real analysis.

---

# Repository Overview

**src/api/** — FastAPI routes, PDF generation, location service  
**src/etl/** — UCMR5 ingestion and cleaned background builder  
**src/simulation/** — PFAS chemical schema and mixing model  
**src/ui/** — HTML/JS interfaces (picker and dashboard)  
**data/raw/** — Raw UCMR5 dataset  
**data/processed/** — State PFAS medians  
**assets/** — Diagrams, screenshots, templates  
**Dockerfile** — Container build  
**requirements.txt** — Python dependencies  
**run.sh** — Optional runner

---

# Data Sources

## UCMR5 Dataset (EPA)
United States Environmental Protection Agency — Unregulated Contaminant Monitoring Rule 5 (UCMR 5)  
https://www.epa.gov/dwucmr/unregulated-contaminant-monitoring-rule-ucmr-5

## OpenStreetMap Nominatim API
Location lookup and reverse geocoding  
https://nominatim.openstreetmap.org/

---

# PFAS Regulatory & Scientific References

- EPA PFAS MCL Final Rule (2024/2025):  
  https://www.epa.gov/pfas/pfas-national-primary-drinking-water-regulation  
- EPA Hazard Index for PFAS Mixtures:  
  https://www.epa.gov/sdwa/hazard-index-pfas  
- USGS PFAS Occurrence Studies:  
  https://www.usgs.gov/mission-areas/water-resources/science/pfas

---

# Mapping Libraries

- Leaflet.js: https://leafletjs.com/  
- OpenStreetMap Tiles: https://www.openstreetmap.org/copyright




