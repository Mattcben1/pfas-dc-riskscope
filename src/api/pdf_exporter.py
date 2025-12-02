from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas


def generate_pdf_report(result: dict) -> str:
    """
    Create a polished PDF summary of the PFAS DC RiskScope simulation.
    Fully aligned with the new PFASRiskSimulator output schema.
    """

    # -------------------------------
    # Output folder
    # -------------------------------
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

    # -------------------------------
    # Title + Timestamp
    # -------------------------------
    line("PFAS DC RiskScope – Simulation Report", font_size=18, bold=True, dy=26)
    line(f"Generated: {datetime.utcnow().isoformat()} UTC", font_size=9)
    y -= 10

    # -------------------------------
    # Location Block (if included)
    # -------------------------------
    location = result.get("location")

    if location:
        line("Location Details", bold=True, dy=20)

        if location.get("type") == "nearest_pws":
            line(f"  Nearest PWS: {location.get('name','N/A')} ({location.get('pwsid','?')})", font_size=10)
            line(f"  State: {location.get('state','?')}", font_size=10)
            line(f"  County: {location.get('county','?')}", font_size=10)
            line(f"  Distance: {location.get('distance_km','?')} km", font_size=10)
            line(f"  Coordinates: {location.get('lat')}, {location.get('lon')}", font_size=10)
        else:
            line("  No PWS found — using US-level background values.", font_size=10)
            line(f"  Coordinates: {location.get('lat')}, {location.get('lon')}", font_size=10)

        y -= 8

    # -------------------------------
    # Risk Summary
    # -------------------------------
    line("Risk Summary", bold=True, dy=20)

    line(f"  Overall Risk Score (0–100):  {result.get('overall_risk_score_0_100','N/A')}", font_size=11)
    line(f"  Risk Category:               {result.get('risk_category','N/A')}", font_size=11)
    line(f"  Dominant Pathway:            {result.get('dominant_pathway','N/A')}", font_size=11)

    mcl_flag = result.get("mcl_violation_flag", False)
    hi_value = result.get("hazard_index_value", 0)
    hi_flag = result.get("hazard_index_exceeds_1", False)

    line(f"  MCL Violation:               {'YES' if mcl_flag else 'NO'}", font_size=11)
    line(f"  Hazard Index:                {hi_value:.3f}", font_size=11)
    line(f"  HI ≥ 1.0?                    {'YES' if hi_flag else 'NO'}", font_size=11)
    y -= 8

    # -------------------------------
    # PFAS Concentration Table
    # -------------------------------
    line("Modeled Downstream PFAS Concentrations (ppt)", bold=True, dy=20)

    concs = result.get("modeled_downstream_concentrations_ppt", {})

    if concs:
        for chem, value in concs.items():
            line(f"  {chem}: {value:.3f} ppt", font_size=10, dy=14)
    else:
        line("  No PFAS concentration results available.", font_size=10)
    y -= 6

    # -------------------------------
    # Notes
    # -------------------------------
    line("Model Interpretation Notes", bold=True, dy=20)
    line("  • Intermediate PFAS risk model using simplified river mixing.", font_size=9, dy=12)
    line("  • Includes EPA MCLs + Hazard Index screening.", font_size=9, dy=12)
    line("  • Background PFAS levels derived from UCMR5 state medians.", font_size=9, dy=12)
    line("  • Not a regulatory determination — exploratory only.", font_size=9, dy=12)

    c.showPage()
    c.save()

    return str(pdf_path)
