from typing import Dict, Any
from .pfas_background import load_background
from ..config.regulatory import RegulatoryLimits

reg_limits = RegulatoryLimits()
EPA_LIMITS = reg_limits.get_mcl_limits()
UNCERTAINTY = reg_limits.get_uncertainty()


class PFASSimulator:
    def __init__(self):
        self.background = load_background()

    def simulate(self, state: str, facility_load: Dict[str, float]) -> Dict[str, Any]:
        state = state.upper()

        if state not in self.background:
            raise ValueError(f"No PFAS background data available for {state}")

        background = self.background[state]

        results = {}
        total_hazard_index = 0

        for chem, bg_value in background.items():
            facility_value = facility_load.get(chem, 0)

            total_conc = bg_value + facility_value
            mcl = EPA_LIMITS.get(chem, None)
            exceedance = max(total_conc - mcl, 0) if mcl else None

            # Hazard Index contribution
            if mcl and mcl > 0:
                hi = total_conc / mcl
            else:
                hi = 0

            total_hazard_index += hi

            results[chem] = {
                "background_ppt": bg_value,
                "facility_added_ppt": facility_value,
                "total_ppt": total_conc,
                "mcl": mcl,
                "exceedance": exceedance,
            }

        return {
            "state": state,
            "chemicals": results,
            "hazard_index": total_hazard_index,
            "risk_tier": self._risk_tier(total_hazard_index),
        }

    def _risk_tier(self, hi: float) -> str:
        if hi < 0.5:
            return "LOW"
        elif hi < 1.0:
            return "MODERATE"
        elif hi < 2.0:
            return "HIGH"
        else:
            return "SEVERE"


if __name__ == "__main__":
    sim = PFASSimulator()
    example = sim.simulate(
        "VA",
        {"PFOA": 2.0, "PFOS": 1.0}
    )
    print(example)
