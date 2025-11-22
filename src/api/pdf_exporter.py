"""
pdf_exporter.py

Generates a professional PFAS regulatory risk PDF report
based on simulation output.
"""

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from datetime import datetime


def generate_pdf_report(simulation_result: dict, metadata: dict = None) -> str:
    """
    Create a PDF report summarizing the PFAS regulatory risk simulation.

    Parameters:
        simulation_result (dict): Output from PFASRiskSimulator.simulate()
        metadata (dict): Optional site or project info

    Returns:
        str: Path to the generated PDF file
    """

    if metadata is None:
        metadata = {}

    filename = f"pfas_risk_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = f"/app/{filename}"  # Compatible inside Docker

    c = canvas.Canvas(file_path, pagesize=LETTER)
    width, height = LETTER

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------
    c.setFont("Helvetica-Bold", 18)
    c.drawString(1 * inch, height - 1 * inch, "PFAS Regulatory Risk Assessment Report")

    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, height - 1.3 * inch, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Site metadata
    y = height - 1.7 * inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1 * inch, y, "Site Information:")
    y -= 0.3 * inch

    c.setFont("Helvetica", 11)
    for key, value in metadata.items():
        c.drawString(1 * inch, y, f"- {key}: {value}")
        y -= 0.25 * inch

    # --------------------------------------------------------
    # Simulation Results
    # --------------------------------------------------------
    y -= 0.4 * inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1 * inch, y, "Simulation Outputs:")
    y -= 0.3 * inch

    c.setFont("Helvetica", 11)
    for key, value in simulation_result.items():
        c.drawString(1 * inch, y, f"- {key}: {value}")
        y -= 0.25 * inch

        if y < 1 * inch:
            c.showPage()
            y = height - 1 * inch
            c.setFont("Helvetica", 11)

    # --------------------------------------------------------
    # End of report
    # --------------------------------------------------------
    c.showPage()
    c.save()

    return file_path
