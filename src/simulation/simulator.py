"""
simulator.py

Core PFAS risk simulation engine.

This module uses:
- model_schema.py (for variable structure and expected fields)
- regulatory_loader.py (for EPA regulatory limits)

The goal: given data-center properties and environmental conditions,
return a PFAS regulatory risk assessment.
"""

from typing import Dict, Any
from .model_schema import PFAS_RISK_MODEL_SCHEMA, PFAS_CHEMICALS
from ..etl.regulatory_loader import RegulatoryLimits


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
        total = concentrations.get("PFOA", 0) + concentrations.get("PFOS", 0)
        return total > limit

    # -------------------------------------------------------------
    # 4) Main Simulation Logic
    # -------------------------------------------------------------
    def simulate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs a simplified PFAS regulatory risk simulation
        using the model schema expectations.
        """

        # -----------------------------------------------------
        # Retrieve concentrations
        # -----------------------------------------------------
        concentrations = payload["chemicals"]["concentrations_ppt"]

        # -----------------------------------------------------
        # Hazard Index
        # -----------------------------------------------------
        hi_value = self.compute_hazard_index(concentrations)
        hi_flag = hi_value > 1.0

        # -----------------------------------------------------
        # MCL checks
        # -----------------------------------------------------
        mcl_flag = self.check_mcl_violations(concentrations)
        combined_flag = self.combined_mcl_violation(concentrations)

        # -----------------------------------------------------
        # Build a simple risk score
        # -----------------------------------------------------
        # This will get more sophisticated later, but works now.
        base_risk = 0

        if mcl_flag:
            base_risk += 40
        if combined_flag:
            base_risk += 25
        if hi_flag:
            base_risk += 25

        # Environmental factors
        env = payload["environmental_factors"]
        stress = env.get("water_stress_category", "low")

        stress_multiplier = {
            "low": 1.0,
            "moderate": 1.2,
            "high": 1.4,
            "extreme": 1.6,
        }.get(stress, 1.0)

        base_risk *= stress_multiplier

        # Bound to 0–100
        risk_score = min(100, max(0, base_risk))

        # Risk category
        if risk_score < 25:
            category = "low"
        elif risk_score < 50:
            category = "moderate"
        elif risk_score < 75:
            category = "high"
        else:
            category = "severe"

        # -----------------------------------------------------
        # Dominant pathway (very simple placeholder)
        # -----------------------------------------------------
        groundwater_index = env["groundwater_vulnerability_index"]
        surface_dist = env["surface_water_distance_km"]

        if groundwater_index > 0.7:
            pathway = "groundwater"
        elif surface_dist < 1.0:
            pathway = "surface_water"
        else:
            pathway = "mixed"

        # -----------------------------------------------------
        # Final Output
        # -----------------------------------------------------
        return {
            "overall_risk_score_0_100": risk_score,
            "risk_category": category,
            "mcl_violation_flag": mcl_flag or combined_flag,
            "hazard_index_value": hi_value,
            "hazard_index_exceeds_1": hi_flag,
            "dominant_pathway": pathway,
            "notes": "This is a simplified early-stage model. Results should be interpreted with caution.",
        }


if __name__ == "__main__":
    # Manual test example (this will print output to terminal)
    example_input = {
        "chemicals": {
            "concentrations_ppt": {
                "PFOA": 3,
                "PFOS": 2,
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
        },
        "data_center": {
            "cooling_type": "evaporative",
            "max_daily_water_withdrawal_mgd": 2.5,
        },
        "regulatory": {},
        "scenario_parameters": {"time_horizon_years": 10},
    }

    sim = PFASRiskSimulator()
    print(sim.simulate(example_input))
