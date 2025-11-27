"""
pdf_exporter.py

Simple PDF generator for PFAS DC RiskScope.
Uses reportlab to generate a text-based summary and optionally embed a map image.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def _ensure_output_path(output_path: Optional[Path], prefix: str) -> Path:
    if output_path is None:
        output_dir = Path(".")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{prefix}.pdf"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def generate_pdf_report(result: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Basic PDF report without maps (keeps backward compatibility).
    """
    output = _ensure_output_path(
        Path(output_path) if output_path else None,
        prefix="pfas_risk_report",
    )

    c = canvas.Canvas(str(output), pagesize=LETTER)
    width, height = LETTER
    y = height - inch

    c.setFont("Helvetica-Bold", 14)
    c.drawString(inch, y, "PFAS DC RiskScope – Simulation Report")
    y -= 0.4 * inch

    c.setFont("Helvetica", 10)

    # Inputs
    inputs = result.get("inputs", {})
    c.drawString(inch, y, "Inputs:")
    y -= 0.25 * inch
    for k, v in inputs.items():
        c.drawString(inch * 1.2, y, f"- {k}: {v}")
        y -= 0.2 * inch

    y -= 0.2 * inch

    # Overall risk
    c.drawString(inch, y, f"Overall risk classification: {result.get('overall_risk', 'N/A')}")
    y -= 0.3 * inch

    # Uncertainty notes
    notes = result.get("uncertainty_notes", [])
    if notes:
        c.drawString(inch, y, "Uncertainty notes:")
        y -= 0.25 * inch
        for note in notes:
            c.drawString(inch * 1.2, y, f"- {note}")
            y -= 0.2 * inch

    c.showPage()
    c.save()
    return str(output)


def generate_pdf_report_with_map(
    result: Dict[str, Any],
    map_path: Path,
    output_path: Optional[str] = None,
) -> str:
    """
    PDF report that includes a static map image (e.g., from map_renderer).
    """
    output = _ensure_output_path(
        Path(output_path) if output_path else None,
        prefix="pfas_risk_report_map",
    )

    c = canvas.Canvas(str(output), pagesize=LETTER)
    width, height = LETTER
    y = height - inch

    c.setFont("Helvetica-Bold", 14)
    c.drawString(inch, y, "PFAS DC RiskScope – Location-Aware Report")
    y -= 0.4 * inch

    c.setFont("Helvetica", 10)

    # Location info
    location = result.get("location", {})
    c.drawString(inch, y, "Location:")
    y -= 0.25 * inch
    for k, v in location.items():
        c.drawString(inch * 1.2, y, f"- {k}: {v}")
        y -= 0.2 * inch

    y -= 0.2 * inch

    # Overall risk
    c.drawString(inch, y, f"Overall risk classification: {result.get('overall_risk', 'N/A')}")
    y -= 0.3 * inch

    # Uncertainty notes
    notes = result.get("uncertainty_notes", [])
    if notes:
        c.drawString(inch, y, "Uncertainty notes:")
        y -= 0.25 * inch
        for note in notes:
            c.drawString(inch * 1.2, y, f"- {note}")
            y -= 0.2 * inch

    # New page for map
    c.showPage()

    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch, height - inch, "PFAS Monitoring Context Map")

    # Draw image roughly centered
    img_w = 6 * inch
    img_h = 4 * inch
    x = (width - img_w) / 2
    y_img = height - inch * 1.5 - img_h

    c.drawImage(str(map_path), x, y_img, width=img_w, height=img_h)

    c.showPage()
    c.save()
    return str(output)
