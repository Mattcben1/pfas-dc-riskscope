"""
simulator.py

PFAS RiskScope – Final Simulation Engine
----------------------------------------
• Loads UCMR5 median PFAS concentrations per state (FIPS-based)
• Applies a simple hydrologic mixing model for data-center discharge
• Computes individual and combined MCL exceedances
• Computes a PFAS Hazard Index
• Produces a final 0–100 risk score + category
"""

from typing import Dict, Any

from src.etl.ucmr5_ingest import load_ucmr5_background
from src.simulation.model_schema import PFAS_CHEMICALS

# Convert million gallons/day to cubic feet/second
MGD_TO_CFS = 1.547


class PFASRiskSimulator:
    def __init__(self):
        # Load UCMR5 background dictionary:
        # { "51": {"PFOA": X, "PFOS": Y, ...}, ...}
        self.background_by_state: Dict[str, Dict[str, float]] = load_ucmr5_background()

        # EPA Draft MCL (ppt)
        self.MCL = {"PFOA": 4.0, "PFOS": 4.0}

        # EPA Hazard Index chemicals + RfD-like scaling factors
        self.HAZARD_RFD = {
            "PFHxS": 2.0,
            "PFNA": 10.0,
            "HFPO-DA": 10.0,
            "PFBS": 30.0,
        }

        # EPA combined MCL for PFOA + PFOS (ppt)
        self.COMBINED_MCL = 4.0

    # ------------------------------------------------------------------
    # Background retrieval
    # ------------------------------------------------------------------
    def get_background(self, fips: str) -> Dict[str, float]:
        """
        Returns per-chemical background PFAS medians for a given state (FIPS code).
        Missing chemicals default to 0.
        """
        fips = str(fips).zfill(2)  # ensure formatting
        chem_map = self.background_by_state.get(fips, {})

        return {chem: float(chem_map.get(chem, 0.0)) for chem in PFAS_CHEMICALS}

    # ------------------------------------------------------------------
    # Mixing model
    # ------------------------------------------------------------------
    def compute_mixed_concentrations(
        self,
        upstream: Dict[str, float],
        discharge: Dict[str, float],
        env: Dict[str, Any],
        dc: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Simple 2-source mixing:

        C_down = (C_up * Q_river + C_eff * Q_eff) / (Q_river + Q_eff)
        """
        # Convert flows
        Q_river = float(env.get("receiving_water_flow_cfs", 100.0))
        Q_eff = float(dc.get("max_daily_water_withdrawal_mgd", 0.0)) * MGD_TO_CFS

        if Q_eff <= 0:
            return upstream.copy()

        # Cooling-type enrichment factor
        enrichment = {
            "evaporative": 1.5,
            "hybrid": 1.3,
            "closed_loop": 1.1,
            "air_cooled": 1.0,
        }.get(dc.get("cooling_type", "closed_loop"), 1.1)

        mixed = {}

        for chem in PFAS_CHEMICALS:
            c_up = float(upstream.get(chem, 0.0))
            c_eff_base = float(discharge.get(chem, c_up))
            c_eff = c_eff_base * enrichment

            c_down = (c_up * Q_river + c_eff * Q_eff) / (Q_river + Q_eff)
            mixed[chem] = c_down

        return mixed

    # ------------------------------------------------------------------
    # Hazard Index
    # ------------------------------------------------------------------
    def compute_hazard_index(self, conc: Dict[str, float]) -> float:
        hi = 0.0
        for chem, rfd in self.HAZARD_RFD.items():
            hi += float(conc.get(chem, 0.0)) / (rfd + 1e-9)
        return hi

    # ------------------------------------------------------------------
    # MCL checks
    # ------------------------------------------------------------------
    def check_mcl(self, conc: Dict[str, float]) -> bool:
        return any(conc.get(chem, 0.0) > mcl for chem, mcl in self.MCL.items())

    def check_combined_mcl(self, conc: Dict[str, float]) -> bool:
        return conc.get("PFOA", 0.0) + conc.get("PFOS", 0.0) > self.COMBINED_MCL

    # ------------------------------------------------------------------
    # MAIN SIMULATE
    # ------------------------------------------------------------------
    def simulate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expected payload from UI.
        """
        fips = payload.get("state", "00")  # use FIPS
        discharge = payload["chemicals"]["concentrations_ppt"]
        env = payload["environmental_factors"]
        dc = payload["data_center"]

        # Background PFAS (per-chemical)
        upstream = self.get_background(fips)

        # Apply mixing
        downstream = self.compute_mixed_concentrations(
            upstream=upstream,
            discharge=discharge,
            env=env,
            dc=dc
        )

        # Hazard Index
        hi = self.compute_hazard_index(downstream)
        hi_flag = hi > 1.0

        # MCL checks
        mcl_flag = self.check_mcl(downstream)
        combined_flag = self.check_combined_mcl(downstream)

        # Risk scoring
        risk = 0.0
        for chem, mcl_val in self.MCL.items():
            c = downstream.get(chem, 0.0)
            ratio = min(c / mcl_val, 3.0)
            risk += ratio * 12.0  # max ~36

        if hi_flag:
            risk += 20
        if combined_flag:
            risk += 15

        # Environmental stress multiplier
        stress_level = env.get("water_stress_category", "low")
        stress_mult = {"low": 1.0, "moderate": 1.2, "high": 1.4}.get(stress_level, 1.0)
        risk *= stress_mult

        # Clamp 0–100
        risk = max(0, min(100, risk))

        # Category
        if risk < 25:
            category = "low"
        elif risk < 50:
            category = "moderate"
        elif risk < 75:
            category = "high"
        else:
            category = "severe"

        # Pathway inference
        gw = float(env.get("groundwater_vulnerability_index", 0.5))
        surf = float(env.get("surface_water_distance_km", 5.0))

        if gw > 0.7:
            pathway = "groundwater"
        elif surf < 1.0:
            pathway = "surface_water"
        else:
            pathway = "mixed"

        return {
            "state_fips": fips,
            "background_pfas_ppt": upstream,
            "modeled_downstream_pfas_ppt": downstream,
            "hazard_index": hi,
            "hazard_index_exceeds_1": hi_flag,
            "mcl_violation": mcl_flag,
            "combined_mcl_violation": combined_flag,
            "overall_risk_score": risk,
            "risk_category": category,
            "dominant_pathway": pathway,
        }
