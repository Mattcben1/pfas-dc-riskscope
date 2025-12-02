# src/api/pdf_exporter.py

from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas


def generate_pdf_report(result: dict) -> str:
    """
    Generate a 1-page PDF summarizing the PFAS DC RiskScope simulation.

    `result` is the dict returned by PFASRiskSimulator.simulate(), with
    lat/lon and state optionally attached in routes.py.
    """

    output_dir = Path("assets/report_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    pdf_path = output_dir / f"pfas_risk_report_{timestamp}.pdf"

    c = canvas.Canvas(str(pdf_path), pagesize=LETTER)
    width, height = LETTER
    y = height - 50

    def line(text: str, font_size: int = 11, bold: bool = False, dy: int = 16):
        nonlocal y
        if bold:
            c.setFont("Helvetica-Bold", font_size)
        else:
            c.setFont("Helvetica", font_size)
        c.drawString(50, y, text)
        y -= dy

    # --------------------------------------------------
    # Title
    # --------------------------------------------------
    line("PFAS DC RiskScope – Simulation Report", font_size=16, bold=True, dy=22)
    line(f"Generated: {datetime.utcnow().isoformat()} UTC", font_size=9)
    y -= 10

    # --------------------------------------------------
    # Location & State
    # --------------------------------------------------
    state = result.get("state", "N/A")
    lat = result.get("lat", "N/A")
    lon = result.get("lon", "N/A")

    line("Location & State", bold=True, dy=18)
    line(f"  State (FIPS): {state}", font_size=10)
    line(f"  Latitude: {lat}", font_size=10)
    line(f"  Longitude: {lon}", font_size=10)
    y -= 8

    # --------------------------------------------------
    # Background & downstream PFAS (ppt)
    # --------------------------------------------------
    upstream = result.get("upstream_background_pfas_ppt", {}) or {}
    downstream = result.get("modeled_downstream_concentrations_ppt", {}) or {}

    bg_pfoa = upstream.get("PFOA", 0.0)
    bg_pfos = upstream.get("PFOS", 0.0)
    dn_pfoa = downstream.get("PFOA", None)
    dn_pfos = downstream.get("PFOS", None)

    line("Background PFAS (ppt)", bold=True, dy=18)
    line(f"  PFOA: {bg_pfoa}", font_size=10)
    line(f"  PFOS: {bg_pfos}", font_size=10)
    y -= 8

    line("Downstream PFAS (ppt)", bold=True, dy=18)
    line(f"  PFOA: {dn_pfoa}", font_size=10)
    line(f"  PFOS: {dn_pfos}", font_size=10)
    y -= 8

    # --------------------------------------------------
    # Risk & regulatory summary
    # --------------------------------------------------
    hi = result.get("hazard_index_value", None)
    hi_flag = result.get("hazard_index_exceeds_1", False)
    risk_score = result.get("overall_risk_score_0_100", None)
    category = result.get("risk_category", "N/A")
    mcl_flag = result.get("mcl_violation_flag", None)
    combined_flag = result.get("combined_mcl_violation", False)

    line("Risk & Regulatory Summary", bold=True, dy=18)
    line(f"  Hazard Index: {hi}", font_size=10)
    line(f"  HI Exceeds 1.0? {hi_flag}", font_size=10)
    line(f"  Risk Score (0–100): {risk_score}", font_size=10)
    line(f"  Category: {category}", font_size=10)
    line(f"  MCL Violation: {mcl_flag}", font_size=10)
    line(f"  Combined MCL Violation: {combined_flag}", font_size=10)
    y -= 8

    # --------------------------------------------------
    # Notes
    # --------------------------------------------------
    line("Interpretation Notes", bold=True, dy=18)
    line("  • Screening-level model, not a formal regulatory determination.", font_size=9, dy=12)
    line("  • Background PFAS from UCMR5 state medians with national fallback.", font_size=9, dy=12)
    line("  • Scenario factors approximate data-center discharge and mixing.", font_size=9, dy=12)

    c.showPage()
    c.save()

    return str(pdf_path)
