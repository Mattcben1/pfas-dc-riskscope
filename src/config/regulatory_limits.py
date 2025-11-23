import yaml
from pathlib import Path

class RegulatoryLimits:
    def __init__(self, yaml_path: str = "src/config/regulatory_limits.yaml"):
        self.yaml_path = Path(yaml_path)
        self.limits = self._load()

    def _load(self):
        if not self.yaml_path.exists():
            raise FileNotFoundError(f"Regulatory limits file not found at {self.yaml_path}")

        with open(self.yaml_path, "r") as f:
            return yaml.safe_load(f)

    def get_mcl_limits(self):
        return self.limits.get("mcl_individual", {})

    def get_hazard_index_contaminants(self):
        return self.limits.get("hazard_index_contaminants", {})

    def get_combined_limit(self):
        return self.limits.get("combined_mcl", {})

    def get_uncertainty(self):
        return self.limits.get("uncertainty", {})

    def summary(self):
        return {
            "MCL_Individual": self.get_mcl_limits(),
            "Hazard_Index_Contaminants": self.get_hazard_index_contaminants(),
            "Combined_MCL": self.get_combined_limit(),
            "Uncertainty_Factors": self.get_uncertainty(),
        }

if __name__ == "__main__":
    loader = RegulatoryLimits()
    print(loader.summary())
