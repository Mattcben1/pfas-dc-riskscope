# src/simulation/simulator.py

"""
PFASRiskSimulator

Intermediate PFAS risk simulation for PFAS DC RiskScope.

- Uses UCMR5 state-level medians as background PFAS (ppt)
- Simple river mixing model for data-center discharge
- EPA-style MCL checks and PFAS Hazard Index
"""

from typing import Dict, Any

from src.etl.ucmr5_ingest import load_ucmr5_background
from src.simulation.model_schema import PFAS_CHEMICALS

MGD_TO_CFS = 1.547  # million gallons/day → cubic feet/second


class PFASRiskSimulator:
    def __init__(self) -> None:
        # Background PFAS medians per state (ppt)
        # keys: FIPS "51", "42", and "US" fallback
        self.background_by_state: Dict[str, Dict[str, float]] = load_ucmr5_background()

        # Very simplified MCLs (ppt)
        self.MCL = {
            "PFOA": 4.0,
            "PFOS": 4.0,
        }

        # Simplified RfDs for HI calculation (unitless scaling)
        self.HAZARD_RFD = {
            "PFHxS": 2.0,
            "PFNA": 10.0,
            "HFPO-DA": 10.0,
            "PFBS": 30.0,
        }

        # Combined MCL for PFOA + PFOS (ppt)
        self.COMBINED_MCL = 4.0

    # ------------------------------------------------------------------
    # Background by state
    # ------------------------------------------------------------------
    def get_background(self, state: str | None) -> Dict[str, float]:
        """
        Returns per-chemical background PFAS medians (ppt) for a given state.
        If state medians are all 0 or missing, falls back to 'US' (if present).
        """
        state_key = (state or "US").upper()

        chem_map = self.background_by_state.get(state_key, {})
        # if empty or all zeros, try national fallback
        if not chem_map or all(v == 0.0 for v in chem_map.values()):
            chem_map = self.background_by_state.get("US", chem_map)

        # Fill every PFAS chemical, default 0 if still missing
        return {chem: float(chem_map.get(chem, 0.0)) for chem in PFAS_CHEMICALS}

    # ------------------------------------------------------------------
    # Mixing model
    # ------------------------------------------------------------------
    def compute_mixed_concentrations(
        self,
        upstream: Dict[str, float],
        discharge: Dict[str, float],
        env: Dict[str, Any],
        dc: Dict[str, Any],
    ) -> Dict[str, float]:
        """
        Simplified mixing:

            C_down = (C_up * Q_river + C_eff * Q_eff) / (Q_river + Q_eff)

        where C_eff is discharge concentration adjusted by a cooling-type
        enrichment factor.
        """
        river_flow_cfs = float(env.get("receiving_water_flow_cfs", 100.0))
        withdrawal_mgd = float(dc.get("max_daily_water_withdrawal_mgd", 0.0))
        discharge_cfs = withdrawal_mgd * MGD_TO_CFS

        if discharge_cfs <= 0.0:
            return upstream.copy()

        cooling_type = dc.get("cooling_type", "closed_loop")
        enrichment = {
            "evaporative": 1.5,
            "hybrid": 1.3,
            "closed_loop": 1.1,
            "air_cooled": 1.0,
        }.get(cooling_type, 1.1)

        mixed: Dict[str, float] = {}

        for chem in PFAS_CHEMICALS:
            c_up = float(upstream.get(chem, 0.0))
            c_eff_base = float(discharge.get(chem, c_up))
            c_eff = c_eff_base * enrichment

            c_down = (c_up * river_flow_cfs + c_eff * discharge_cfs) / (
                river_flow_cfs + discharge_cfs
            )
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
    # Regulatory checks
    # ------------------------------------------------------------------
    def check_mcl(self, conc: Dict[str, float]) -> bool:
        return any(conc.get(chem, 0.0) > mcl for chem, mcl in self.MCL.items())

    def check_combined_mcl(self, conc: Dict[str, float]) -> bool:
        return conc.get("PFOA", 0.0) + conc.get("PFOS", 0.0) > self.COMBINED_MCL

    # ------------------------------------------------------------------
    # Main simulate()
    # ------------------------------------------------------------------
    def simulate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expected payload (from dashboard):

        {
          "state": "51",   # FIPS or "US"
          "lat": 38.8,     # optional
          "lon": -77.3,    # optional
          "chemicals": {
            "concentrations_ppt": {
              "PFOA": ...,
              "PFOS": ...,
              ...
            }
          },
          "environmental_factors": {...},
          "data_center": {...}
        }
        """
        state = payload.get("state")  # can be FIPS or "US"
        discharge_conc = payload["chemicals"]["concentrations_ppt"]
        env = payload["environmental_factors"]
        dc = payload["data_center"]

        upstream = self.get_background(state)
        downstream = self.compute_mixed_concentrations(
            upstream, discharge_conc, env, dc
        )

        hi = self.compute_hazard_index(downstream)
        hi_flag = hi > 1.0
        mcl_flag = self.check_mcl(downstream)
        combined_flag = self.check_combined_mcl(downstream)

        # Risk scoring
        risk = 0.0
        for chem, mcl_val in self.MCL.items():
            c = downstream.get(chem, 0.0)
            if mcl_val > 0:
                ratio = min(c / mcl_val, 3.0)  # cap at 3x
                risk += ratio * 12.0

        if hi_flag:
            risk += 20.0
        if combined_flag:
            risk += 15.0

        stress = env.get("water_stress_category", "low")
        stress_mult = {"low": 1.0, "moderate": 1.2, "high": 1.4}.get(stress, 1.0)
        risk *= stress_mult

        risk = max(0.0, min(risk, 100.0))

        if risk < 25:
            category = "low"
        elif risk < 50:
            category = "moderate"
        elif risk < 75:
            category = "high"
        else:
            category = "severe"

        gw_idx = float(env.get("groundwater_vulnerability_index", 0.5))
        surf_dist = float(env.get("surface_water_distance_km", 5.0))

        if gw_idx > 0.7:
            pathway = "groundwater"
        elif surf_dist < 1.0:
            pathway = "surface_water"
        else:
            pathway = "mixed"

        return {
            "state": state,
            "upstream_background_pfas_ppt": upstream,
            "modeled_downstream_concentrations_ppt": downstream,
            "hazard_index_value": hi,
            "hazard_index_exceeds_1": hi_flag,
            "mcl_violation_flag": mcl_flag,
            "combined_mcl_violation": combined_flag,
            "overall_risk_score_0_100": risk,
            "risk_category": category,
            "dominant_pathway": pathway,
        }
