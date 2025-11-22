"""
simulator.py

Core PFAS risk simulation engine.

Intermediate model (Option 2):
- Uses EPA-like MCL checks and PFAS Hazard Index
- Adds a simple surface-water mixing / dilution model
  using data-center discharge and receiving-water flow.
"""

from typing import Dict, Any
from .model_schema import PFAS_CHEMICALS
from ..etl.regulatory_loader import RegulatoryLimits

# Conversion: million gallons per day → cubic feet per second
MGD_TO_CFS = 1.547


class PFASRiskSimulator:
    """
    Main simulation class.
    """

    def __init__(self):
        self.reg_limits = RegulatoryLimits()
        self.mcl_limits = self.reg_limits.get_mcl_limits()
        self.hazard_idx_contaminants = self.reg_limits.get_hazard_index_contaminants()
        self.combined_limit = self.reg_limits.get_combined_limit()
        self.uncertainty = self.reg_limits.get_uncertainty()

    # -------------------------------------------------------------
    # 1) Hazard Index Calculation
    # -------------------------------------------------------------
    def compute_hazard_index(self, concentrations: Dict[str, float]) -> float:
        """
        HI = sum(C_i / RfD_i) across the hazard index contaminants.
        Only applies to PFHxS, PFNA, HFPO-DA, PFBS.
        """
        hi = 0.0
        for chem, meta in self.hazard_idx_contaminants.items():
            conc = concentrations.get(chem, 0.0)
            rfd = meta.get("rfd", 1.0)
            hi += conc / (rfd + 1e-9)
        return hi

    # -------------------------------------------------------------
    # 2) Individual MCL Checks (PFOA, PFOS)
    # -------------------------------------------------------------
    def check_mcl_violations(self, concentrations: Dict[str, float]) -> bool:
        for chem, mcl in self.mcl_limits.items():
            if concentrations.get(chem, 0.0) > mcl:
                return True
        return False

    # -------------------------------------------------------------
    # 3) Combined MCL Check (PFOA + PFOS)
    # -------------------------------------------------------------
    def combined_mcl_violation(self, concentrations: Dict[str, float]) -> bool:
        limit = self.combined_limit.get("PFOA_PFOS_sum_limit", None)
        if limit is None:
            return False
        total = concentrations.get("PFOA", 0.0) + concentrations.get("PFOS", 0.0)
        return total > limit

    # -------------------------------------------------------------
    # 4) Simple mixing / dilution model
    # -------------------------------------------------------------
    def compute_mixed_concentrations(
        self,
        upstream_conc: Dict[str, float],
        env: Dict[str, Any],
        dc: Dict[str, Any],
    ) -> Dict[str, float]:
        """
        Very simplified river mixing model:

        C_down = (C_up * Q_river + C_eff * Q_eff) / (Q_river + Q_eff)

        Where:
          - Q_river is receiving water flow (cfs) (from env or default)
          - Q_eff is data-center discharge (cfs), approximated from
            max_daily_water_withdrawal_mgd
          - C_eff is an 'enriched' PFAS concentration based on cooling type.

        This is not meant to be hydrodynamically precise, but gives a
        reasonable directional signal for siting and policy exploration.
        """
        # Receiving-water flow (cfs)
        river_flow_cfs = float(env.get("receiving_water_flow_cfs", 100.0))  # default

        # Data-center discharge flow (cfs), assume ≈ max withdrawal discharged
        max_withdrawal_mgd = float(dc.get("max_daily_water_withdrawal_mgd", 0.0))
        discharge_cfs = max_withdrawal_mgd * MGD_TO_CFS

        # If no discharge, concentrations stay as upstream
        if discharge_cfs <= 0.0:
            return upstream_conc.copy()

        # Cooling-type enrichment factors (how much PFAS can be concentrated)
        cooling_type = dc.get("cooling_type", "closed_loop")
        enrichment_factor = {
            "evaporative": 1.5,
            "hybrid": 1.3,
            "closed_loop": 1.1,
            "air_cooled": 1.0,
        }.get(cooling_type, 1.1)

        mixed: Dict[str, float] = {}

        for chem in PFAS_CHEMICALS:
            c_up = float(upstream_conc.get(chem, 0.0))
            c_eff = c_up * enrichment_factor  # enriched effluent

            q_r = river_flow_cfs
            q_e = discharge_cfs

            c_down = (c_up * q_r + c_eff * q_e) / (q_r + q_e)
            mixed[chem] = c_down

        return mixed

    # -------------------------------------------------------------
    # 5) Main Simulation Logic
    # -------------------------------------------------------------
    def simulate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs an intermediate PFAS regulatory risk simulation
        using a mixing model + regulatory checks.
        """
        # Extract sections
        upstream_conc = payload["chemicals"]["concentrations_ppt"]
        env = payload["environmental_factors"]
        dc = payload["data_center"]

        # 1) Compute mixed downstream concentrations
        downstream_conc = self.compute_mixed_concentrations(upstream_conc, env, dc)

        # 2) Regulatory checks based on mixed concentrations
        hi_value = self.compute_hazard_index(downstream_conc)
        hi_flag = hi_value > 1.0

        mcl_flag = self.check_mcl_violations(downstream_conc)
        combined_flag = self.combined_mcl_violation(downstream_conc)

        # 3) Build a more nuanced risk score
        base_risk = 0.0

        # MCL-related risk from ratios of concentrations to limits
        for chem, mcl in self.mcl_limits.items():
            c = downstream_conc.get(chem, 0.0)
            if mcl > 0:
                ratio = c / mcl
                # Cap at 3x to avoid runaway values
                ratio = min(ratio, 3.0)
                base_risk += ratio * 10.0  # up to ~30 pts per chem

        if combined_flag:
            base_risk += 15.0
        if hi_flag:
            base_risk += 20.0

        # Environmental multipliers
        stress = env.get("water_stress_category", "low")
        stress_multiplier = {
            "low": 1.0,
            "moderate": 1.2,
            "high": 1.4,
            "extreme": 1.6,
        }.get(stress, 1.0)

        gw_index = float(env.get("groundwater_vulnerability_index", 0.5))
        gw_multiplier = 1.0 + (gw_index - 0.5) * 0.5  # ~0.75–1.25

        base_risk *= stress_multiplier * gw_multiplier

        # Bound 0–100
        risk_score = min(100.0, max(0.0, base_risk))

        # Risk category
        if risk_score < 25:
            category = "low"
        elif risk_score < 50:
            category = "moderate"
        elif risk_score < 75:
            category = "high"
        else:
            category = "severe"

        # Dominant pathway (very simple)
        surface_dist = float(env.get("surface_water_distance_km", 5.0))

        if gw_index > 0.7:
            pathway = "groundwater"
        elif surface_dist < 1.0:
            pathway = "surface_water"
        else:
            pathway = "mixed"

        notes = (
            "Intermediate PFAS risk model using a simple river mixing equation "
            "plus EPA-like MCL and Hazard Index checks. Results are for "
            "scenario exploration and should not be used as a formal regulatory determination."
        )

        return {
            "overall_risk_score_0_100": risk_score,
            "risk_category": category,
            "mcl_violation_flag": mcl_flag or combined_flag,
            "hazard_index_value": hi_value,
            "hazard_index_exceeds_1": hi_flag,
            "dominant_pathway": pathway,
            "modeled_downstream_concentrations_ppt": downstream_conc,
            "notes": notes,
        }


if __name__ == "__main__":
    # Simple local test (not used in Docker by default)
    example_input = {
        "chemicals": {
            "concentrations_ppt": {
                "PFOA": 3.0,
                "PFOS": 2.0,
                "PFHxS": 0.5,
                "PFNA": 0.2,
                "HFPO-DA": 0.1,
                "PFBS": 0.4,
            }
        },
        "environmental_factors": {
            "groundwater_vulnerability_index": 0.8,
            "surface_water_distance_km": 0.5,
            "water_stress_category": "high",
            "ej_score": 0.4,
            "receiving_water_flow_cfs": 120.0,
        },
        "data_center": {
            "cooling_type": "evaporative",
            "max_daily_water_withdrawal_mgd": 3.0,
        },
        "scenario_parameters": {"time_horizon_years": 10},
    }

    sim = PFASRiskSimulator()
    print(sim.simulate(example_input))
