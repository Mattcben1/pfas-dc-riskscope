PFAS DC RiskScope

A geospatial PFAS risk simulator built for the DS 3001 Final Case Study.

1. Project Overview

This project models PFAS (“forever chemicals”) risk around data-center hubs by combining:

Real EPA UCMR5 water-quality data

Reverse-geocoded user locations

A river-mixing hydrology model

EPA health thresholds & hazard index calculations

Users click a location on a map → the system loads PFAS background levels → runs a simulation → and exports a PDF risk report.

This project applies multiple Systems 1 concepts:
✔ FastAPI microservice
✔ Docker containerization
✔ ETL pipeline for raw UCMR5 data
✔ Input validation middleware
✔ Static UI served from backend
✔ Automated PDF report generation

2. Architecture Summary

Flow:

Leaflet Map UI → User clicks a location

FastAPI /simulate-location → Reverse geocodes state + loads UCMR5 medians

ETL Module → Cleans UCMR5 raw data, converts µg/L → ppt, builds state-level PFAS medians

Simulation Engine → Mixes upstream PFAS with data-center discharge

Regulatory Logic → MCL, hazard index, and overall risk category

PDF Exporter → Generates a one-page simulation summary

All parts run inside a single Dockerized app.

3. How to Run
Using Docker (recommended)
docker build -t pfas:latest .
docker run --rm -p 8080:8080 pfas:latest


Then open:
http://localhost:8080/location-picker

From there:
→ Click a map point
→ Go to Dashboard
→ Run simulation
→ Export the PDF report

4. Key Design Decisions

FastAPI chosen for speed, type hints, and clean routing

UCMR5 dataset chosen for real-world environmental relevance

Median PFAS per state balances accuracy and project scope

Simple mixing model provides interpretable results

PDF output adds professionalism and helps shareability


Security & Ethical Considerations

The application does not collect any personal information; map clicks are processed entirely client-side.

All external requests to Nominatim include a safe User-Agent string to follow API usage policies.

Sensitive configuration values are stored in .env (NOT committed), with .env.example provided for reproducibility.

EPA PFAS data is non-sensitive, public, and scientific, used only for educational modeling—not regulatory decision-making.


Testing

The project contains a minimal automated test suite:

✔ tests/test_api.py

Verifies the /health endpoint

Ensures /simulate returns well-structured output for valid payloads

Checks /simulate-location returns a state + background PFAS results


5. Results & Validation

ETL successfully parses all PFAS contaminants from UCMR5

Simulation outputs:

downstream PFAS concentrations

hazard index

MCL exceedances

overall risk score (0–100)

Verified /health, /simulate, /simulate-location, and /export-pdf all function inside Docker

PDF exports cleanly with correct values

Screenshots included in /assets/screenshots.


6. What I Learned

This project helped me practice real microservice patterns, Dockerized development, API validation, environment-variable management, and handling large datasets. It also connected technical modeling with environmental science concepts like PFAS risk and hydrology.

Repo Contents:
src/api/            → API routes, location lookup, PDF exporter
src/etl/            → UCMR5 ingestion + background builder
src/simulation/     → PFAS model + mixing logic
src/ui/             → HTML/JS user interface
data/raw/           → Raw UCMR5 dataset
data/processed/     → Processed state medians
assets/             → screenshots + diagrams
Dockerfile          → container build
requirements.txt    → dependencies
run.sh              → optional starter


Data Sources:

EPA UCMR5 Dataset (2023 Release)
United States Environmental Protection Agency. Unregulated Contaminant Monitoring Rule 5 (UCMR 5) Data.
https://www.epa.gov/dwucmr/unregulated-contaminant-monitoring-rule-ucmr-5

OpenStreetMap Nominatim API (Reverse Geocoding)
OpenStreetMap Foundation.
https://nominatim.openstreetmap.org/

Scientific + Regulatory References

EPA PFAS MCL Final Rule (2024/2025 Updates)
https://www.epa.gov/pfas/pfas-national-primary-drinking-water-regulation

EPA PFAS Mixture/Hazard Index Framework (2022–2023)
https://www.epa.gov/sdwa/hazard-index-pfas

USGS PFAS Occurrence Studies
https://www.usgs.gov/mission-areas/water-resources/science/pfas

Maps & GIS
Leaflet.js Open Map Library
https://leafletjs.com/

OpenStreetMap Tile Service
https://www.openstreetmap.org/copyright



Links: 
Github: Mattcben1/pfas-dc-riskscope


