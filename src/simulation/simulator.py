"""
simulator.py

Core PFAS risk simulation engine.

This version uses:
- EPA-aligned PFAS background stats (from UCMR5 medians)
- EPA-style MCL and Hazard Index concepts (via RegulatoryLimits)
- A simple surface-water mixing model:
    C_total = C_background + C_discharge * (Q_discharge / (Q_discharge + Q_receiving))

Inputs to simulate():
- state: state abbreviation, e.g. "VA"
- discharge_pfas_ppt: dict of PFAS name -> concentration in discharge (ppt)
- discharge_flow_mgd: discharge flow (million gallons per day)
- receiving_flow_mgd: receiving water flow (MGD) for the river/stream

Outputs:
- per-chemical results (baseline, total, MCL ratios)
- combined PFOA+PFOS assessment
- hazard index across hazard-index PFAS
- qualitative overall_risk and uncertainty flags
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

from ..config.regulatory_limits import RegulatoryLimits
from .pfas_background import load_background_medians, load_background_stats


# EPA hazard index PFAS set
HAZARD_INDEX_CHEMS = ["PFHXS", "PFNA", "PFBS", "HFPO-DA"]


@dataclass
class SimulationConfig:
    mixing_model: str = "complete_mixing"
    hi_threshold: float = 1.0  # Hazard Index threshold
    combined_mcl_margin_low: float = 0.5  # below 50% of MCL = low concern
    combined_mcl_margin_high: float = 1.0  # above MCL = high concern


class PFASSimulator:
    def __init__(self, config: SimulationConfig | None = None) -> None:
        self.config = config or SimulationConfig()

        # Load regulatory limits from YAML
        self.reg_limits = RegulatoryLimits()

        # Individual MCLs (ppt) for PFOA, PFOS, etc.
        self.mcl_individual: Dict[str, float] = {
            k.upper(): v
            for k, v in self.reg_limits.get_mcl_limits().items()
        }

        # Combined MCL for PFOA+PFOS (ppt), if present
        combined = self.reg_limits.get_combined_limit()
        self.combined_mcl_pfoa_pfos = combined.get("PFOA_PFOS", None)

        # Hazard-index contaminants (names normalized to uppercase)
        self.hi_contaminants: List[str] = [
            c.upper() for c in self.reg_limits.get_hazard_index_contaminants().keys()
        ]

        # Background PFAS levels & stats from UCMR5
        self.bg_medians = load_background_medians()       # STATE -> chem -> median_ppt
        self.bg_stats = load_background_stats()           # STATE -> chem -> stats dict

    # -------------------------------------------------------------------------
    # Core public API
    # -------------------------------------------------------------------------
    def simulate(
        self,
        *,
        state: str,
        discharge_pfas_ppt: Dict[str, float],
        discharge_flow_mgd: float,
        receiving_flow_mgd: float,
    ) -> Dict[str, Any]:
        """
        Main entrypoint for PFAS simulation.

        Args:
            state: e.g. "VA"
            discharge_pfas_ppt: dict of PFAS -> concentration in discharge (ppt)
            discharge_flow_mgd: discharge flow (MGD)
            receiving_flow_mgd: receiving river/stream flow (MGD)

        Returns:
            A dictionary suitable for JSON / PDF export with:
            - inputs
            - per_chemical_results
            - combined_pfoa_pfos
            - hazard_index
            - overall_risk
            - uncertainty_notes
        """

        state = state.upper().strip()

        # Get background medians/stats for the state (or default to "US")
        bg_medians_state = self._get_background_medians_for_state(state)
        bg_stats_state = self._get_background_stats_for_state(state)

        # Compute mixing factor for discharge into receiving waters
        mixing_factor = self._compute_mixing_factor(
            discharge_flow_mgd, receiving_flow_mgd
        )

        # Per-chemical evaluation
        per_chem_results: Dict[str, Any] = {}
        for chem_raw, discharge_conc in discharge_pfas_ppt.items():
            chem = chem_raw.upper().strip()
            result = self._evaluate_chemical(
                chem=chem,
                discharge_conc_ppt=discharge_conc,
                bg_medians_state=bg_medians_state,
                bg_stats_state=bg_stats_state,
                mixing_factor=mixing_factor,
            )
            per_chem_results[chem] = result

        # Combined PFOA + PFOS assessment
        combined_pfoa_pfos = self._evaluate_combined_pfoa_pfos(per_chem_results)

        # Hazard index across hazard index PFAS
        hazard_index_info = self._evaluate_hazard_index(per_chem_results)

        # Overall qualitative risk & uncertainty narrative
        overall_risk, uncertainty_notes = self._derive_overall_risk(
            combined_pfoa_pfos, hazard_index_info, per_chem_results
        )

        return {
            "inputs": {
                "state": state,
                "discharge_flow_mgd": discharge_flow_mgd,
                "receiving_flow_mgd": receiving_flow_mgd,
                "mixing_factor": mixing_factor,
                "discharge_pfas_ppt": discharge_pfas_ppt,
            },
            "per_chemical_results": per_chem_results,
            "combined_pfoa_pfos": combined_pfoa_pfos,
            "hazard_index": hazard_index_info,
            "overall_risk": overall_risk,
            "uncertainty_notes": uncertainty_notes,
        }

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------
    def _compute_mixing_factor(
        self,
        discharge_flow_mgd: float,
        receiving_flow_mgd: float,
    ) -> float:
        """
        Compute fraction of discharge concentration that appears in the mixed river.

        For a simple complete-mixing model:
            factor = Q_discharge / (Q_discharge + Q_receiving)

        If receiving_flow_mgd is zero (very small stream / worst case), factor=1.
        """
        qd = max(discharge_flow_mgd, 0.0)
        qr = max(receiving_flow_mgd, 0.0)

        denom = qd + qr
        if denom <= 0:
            # No receiving water, extremely conservative assumption
            return 1.0

        return qd / denom

    def _get_background_medians_for_state(self, state: str) -> Dict[str, float]:
        """
        Return background medians for a state, falling back to "US" if missing.
        """
        if state in self.bg_medians:
            return self.bg_medians[state]
        # Fallback to national medians
        return self.bg_medians.get("US", {})

    def _get_background_stats_for_state(self, state: str) -> Dict[str, Dict[str, float]]:
        """
        Return full background stats for a state, falling back to "US" if missing.
        """
        if state in self.bg_stats:
            return self.bg_stats[state]
        return self.bg_stats.get("US", {})

    def _evaluate_chemical(
        self,
        chem: str,
        discharge_conc_ppt: float,
        bg_medians_state: Dict[str, float],
        bg_stats_state: Dict[str, Dict[str, float]],
        mixing_factor: float,
    ) -> Dict[str, Any]:
        """
        Compute:
        - baseline (background) concentration
        - incremental concentration from discharge (post-mixing)
        - total concentration
        - ratio to individual MCL (if available)
        - simple uncertainty metrics based on detection frequency & sample count
        """

        # Background median in ppt (state-level), fallback to 0.0
        bg_median = bg_medians_state.get(chem, 0.0)

        # Stats for uncertainty (if available)
        stats = bg_stats_state.get(chem, {})
        n_samples = stats.get("n_samples", 0.0)
        pct_detected = stats.get("pct_detected", 0.0)
        max_ppt = stats.get("max_ppt", 0.0)

        # Post-mixing incremental concentration from data center
        # (if no mixing factor, we default to full discharge concentration)
        incremental = discharge_conc_ppt * mixing_factor

        total_conc = bg_median + incremental

        # Relationship to EPA MCL (if any)
        mcl = self.mcl_individual.get(chem, None)
        mcl_ratio = None
        status = "no_mcl"

        if mcl is not None and mcl > 0:
            mcl_ratio = total_conc / mcl
            if mcl_ratio < self.config.combined_mcl_margin_low:
                status = "below_half_mcl"
            elif mcl_ratio <= self.config.combined_mcl_margin_high:
                status = "near_mcl"
            else:
                status = "above_mcl"

        # Uncertainty classification (very simple, based on detection rate + sample count)
        if n_samples < 5:
            uncertainty = "low_data_volume"
        elif pct_detected < 1.0:  # <1% detections
            uncertainty = "rarely_detected"
        elif pct_detected < 20.0:
            uncertainty = "sometimes_detected"
        else:
            uncertainty = "frequently_detected"

        return {
            "chemical": chem,
            "background_median_ppt": bg_median,
            "background_max_ppt": max_ppt,
            "n_samples": n_samples,
            "pct_detected": pct_detected,
            "discharge_conc_ppt": discharge_conc_ppt,
            "incremental_conc_ppt": incremental,
            "total_conc_ppt": total_conc,
            "mcl_ppt": mcl,
            "mcl_ratio": mcl_ratio,
            "mcl_status": status,
            "uncertainty_class": uncertainty,
        }

    def _evaluate_combined_pfoa_pfos(
        self,
        per_chem_results: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evaluate combined risk for PFOA + PFOS, if a combined MCL is defined.
        """

        pfoa = per_chem_results.get("PFOA")
        pfos = per_chem_results.get("PFOS")

        if not pfoa and not pfos:
            return {
                "combined_mcl_ppt": self.combined_mcl_pfoa_pfos,
                "total_pfoa_pfos_ppt": None,
                "ratio_to_combined_mcl": None,
                "status": "no_pfoa_pfos_provided",
            }

        total_pfoa = pfoa["total_conc_ppt"] if pfoa else 0.0
        total_pfos = pfos["total_conc_ppt"] if pfos else 0.0
        combined_total = total_pfoa + total_pfos

        if self.combined_mcl_pfoa_pfos is None or self.combined_mcl_pfoa_pfos <= 0:
            return {
                "combined_mcl_ppt": None,
                "total_pfoa_pfos_ppt": combined_total,
                "ratio_to_combined_mcl": None,
                "status": "no_combined_mcl_defined",
            }

        ratio = combined_total / self.combined_mcl_pfoa_pfos
        if ratio < self.config.combined_mcl_margin_low:
            status = "below_half_combined_mcl"
        elif ratio <= self.config.combined_mcl_margin_high:
            status = "near_combined_mcl"
        else:
            status = "above_combined_mcl"

        return {
            "combined_mcl_ppt": self.combined_mcl_pfoa_pfos,
            "total_pfoa_pfos_ppt": combined_total,
            "ratio_to_combined_mcl": ratio,
            "status": status,
        }

    def _evaluate_hazard_index(
        self,
        per_chem_results: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Compute a simple Hazard Index (HI) across hazard-index PFAS.

        We approximate by treating each hazard-index PFAS as having
        a "benchmark" equal to its MCL equivalent if present, otherwise
        we skip or assume a nominal benchmark.
        """

        # Use whichever list is more authoritative:
        hi_chems: List[str] = (
            self.hi_contaminants if self.hi_contaminants else HAZARD_INDEX_CHEMS
        )

        components: List[Tuple[str, float]] = []
        hi_value = 0.0

        for chem in hi_chems:
            res = per_chem_results.get(chem)
            if not res:
                continue

            total_conc = res["total_conc_ppt"]
            benchmark = res.get("mcl_ppt") or self.mcl_individual.get(chem)

            if not benchmark or benchmark <= 0:
                # If no benchmark, skip contribution
                continue

            hq = total_conc / benchmark  # hazard quotient
            hi_value += hq
            components.append((chem, hq))

        if not components:
            return {
                "hi_value": None,
                "hi_threshold": self.config.hi_threshold,
                "status": "no_hi_chemicals_found",
                "components": [],
            }

        if hi_value < 0.5 * self.config.hi_threshold:
            status = "hi_well_below_threshold"
        elif hi_value <= self.config.hi_threshold:
            status = "hi_near_threshold"
        else:
            status = "hi_above_threshold"

        return {
            "hi_value": hi_value,
            "hi_threshold": self.config.hi_threshold,
            "status": status,
            "components": [
                {"chemical": c, "hazard_quotient": hq} for c, hq in components
            ],
        }

    def _derive_overall_risk(
        self,
        combined_pfoa_pfos: Dict[str, Any],
        hazard_index_info: Dict[str, Any],
        per_chem_results: Dict[str, Dict[str, Any]],
    ) -> Tuple[str, List[str]]:
        """
        Combine MCL, combined MCL, and HI information into an overall
        qualitative risk classification + short uncertainty narrative.
        """

        notes: List[str] = []

        # Check for obvious high-risk signals
        high_mcl_exceedances = [
            chem
            for chem, res in per_chem_results.items()
            if res.get("mcl_status") == "above_mcl"
        ]

        hi_status = hazard_index_info.get("status")
        hi_value = hazard_index_info.get("hi_value")

        combined_status = combined_pfoa_pfos.get("status")
        combined_ratio = combined_pfoa_pfos.get("ratio_to_combined_mcl")

        # Overall risk classification
        if high_mcl_exceedances or hi_status == "hi_above_threshold" or (
            isinstance(combined_ratio, (int, float))
            and combined_ratio > self.config.combined_mcl_margin_high
        ):
            overall = "HIGH"
        elif (
            hi_status == "hi_near_threshold"
            or combined_status == "near_combined_mcl"
            or any(
                res.get("mcl_status") == "near_mcl"
                for res in per_chem_results.values()
            )
        ):
            overall = "MODERATE"
        else:
            overall = "LOW"

        # Uncertainty narrative based on background detection patterns
        low_data_chems = [
            chem
            for chem, res in per_chem_results.items()
            if res.get("uncertainty_class") in ("low_data_volume", "rarely_detected")
        ]
        if low_data_chems:
            notes.append(
                "Several PFAS have limited or low-frequency detections in UCMR5 "
                f"background data: {', '.join(sorted(low_data_chems))}."
            )

        if overall == "HIGH" and hi_value:
            notes.append(
                f"Hazard Index is above the reference threshold (HI={hi_value:.2f})."
            )

        if (
            isinstance(combined_ratio, (int, float))
            and combined_ratio > self.config.combined_mcl_margin_high
        ):
            notes.append(
                f"Combined PFOA+PFOS concentration exceeds the proposed combined MCL "
                f"(ratio={combined_ratio:.2f})."
            )

        if high_mcl_exceedances:
            notes.append(
                "One or more PFAS individually exceed their proposed MCLs: "
                + ", ".join(sorted(high_mcl_exceedances))
                + "."
            )

        if not notes:
            notes.append(
                "No PFAS in this scenario exceed proposed EPA MCLs or the hazard index threshold, "
                "given the assumed background and mixing conditions."
            )

        return overall, notes


if __name__ == "__main__":
    # Simple manual test harness (used with `python -m src.simulation.simulator` style
    # if package structure allows). Typically called via API.
    sim = PFASSimulator()

    example = sim.simulate(
        state="VA",
        discharge_pfas_ppt={
            "PFOA": 10.0,
            "PFOS": 8.0,
            "HFPO-DA": 5.0,
        },
        discharge_flow_mgd=1.0,
        receiving_flow_mgd=10.0,
    )

    from pprint import pprint

    pprint(example)
