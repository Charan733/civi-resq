"""
CIVI-RESQ PDF Report Generator
---------------------------------
Generates a downloadable PDF summarizing a zone's risk assessment and recommended
interventions -- for engineers/planners to print, share, or attach to a proposal.
"""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

RISK_COLORS = {
    "low": colors.HexColor("#4C9A6B"),
    "moderate": colors.HexColor("#D9A441"),
    "high": colors.HexColor("#D97D34"),
    "critical": colors.HexColor("#C1443A"),
}


def generate_zone_report(zone: dict, assessment: dict, interventions: list) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleX", parent=styles["Title"], fontSize=18, spaceAfter=2)
    sub_style = ParagraphStyle("SubX", parent=styles["Normal"], textColor=colors.HexColor("#5C7B87"), fontSize=10)
    h2_style = ParagraphStyle("H2X", parent=styles["Heading2"], fontSize=13, spaceBefore=14, spaceAfter=6,
                               textColor=colors.HexColor("#10202B"))
    body_style = ParagraphStyle("BodyX", parent=styles["Normal"], fontSize=9.5, leading=13)
    disclaimer_style = ParagraphStyle("DiscX", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#8CA5B0"))

    elements = []
    elements.append(Paragraph("CIVI-RESQ Risk Assessment Report", title_style))
    elements.append(Paragraph(f"{zone['zone_name']} ({zone['zone_code']}) — {zone['city']}, {zone['state']}", sub_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", color=colors.HexColor("#DCE4E7")))

    # --- Risk Summary Table ---
    elements.append(Paragraph("Risk Assessment Summary", h2_style))
    risk_rows = [
        ["Risk Type", "Score (0-100)", "Category"],
        ["Flood / Waterlogging", f"{assessment['flood_risk_score']:.1f}", assessment["flood_risk_category"].upper()],
        ["Urban Heat", f"{assessment['heat_risk_score']:.1f}", assessment["heat_risk_category"].upper()],
        ["Accessibility / Infrastructure", f"{assessment['accessibility_risk_score']:.1f}", assessment["accessibility_risk_category"].upper()],
        ["Overall Vulnerability", f"{assessment['overall_vulnerability_score']:.1f}", assessment["overall_risk_category"].upper()],
    ]
    t = Table(risk_rows, colWidths=[80 * mm, 40 * mm, 40 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#10202B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DCE4E7")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F5F1")]),
    ]))
    elements.append(t)

    # --- Input Parameters ---
    elements.append(Paragraph("Input Parameters", h2_style))
    param_rows = [
        ["Rainfall", f"{zone['avg_annual_rainfall_mm']} mm/yr", "Elevation", f"{zone['elevation_m']} m"],
        ["Drainage Capacity", f"{zone['drainage_capacity_index']}/100", "Impervious Surface", f"{zone['impervious_surface_pct']}%"],
        ["Population Density", f"{zone['population_density_per_km2']}/km²", "Road Accessibility", f"{zone['road_accessibility_index']}/100"],
        ["Green Cover", f"{zone['green_cover_pct']}%", "Land Surface Temp", f"{zone['avg_land_surface_temp_c']}°C"],
        ["Building Density", f"{zone['building_density_pct']}%", "Flood Events (5yr)", f"{zone['historical_flood_events_5yr']}"],
    ]
    t2 = Table(param_rows, colWidths=[40 * mm, 40 * mm, 40 * mm, 40 * mm])
    t2.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#5C7B87")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#5C7B87")),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTNAME", (3, 0), (3, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#EAEDE7")),
    ]))
    elements.append(t2)

    # --- Explainability ---
    elements.append(Paragraph("Why This Score (Key Factors)", h2_style))
    for risk_key, risk_label in [("flood", "Flood Risk"), ("heat", "Heat Risk"), ("accessibility", "Accessibility Risk")]:
        factors = assessment["explanation"].get(risk_key, [])[:3]
        factor_text = "; ".join(
            f"{f['feature'].replace('_', ' ')} ({'+' if f['impact']>0 else ''}{f['impact']:.1f} pts)" for f in factors
        )
        elements.append(Paragraph(f"<b>{risk_label}:</b> {factor_text}", body_style))
        elements.append(Spacer(1, 3))

    # --- Interventions ---
    elements.append(Paragraph("Recommended Interventions", h2_style))
    if not interventions:
        elements.append(Paragraph("No interventions triggered for this zone's current risk levels.", body_style))
    else:
        iv_rows = [["Intervention", "Priority", "Cost", "Risk Reduction", "Affected Pop."]]
        for iv in interventions:
            iv_rows.append([
                iv["intervention_type"].replace("_", " ").title(),
                iv["priority_level"].upper(),
                iv["estimated_cost_category"].replace("_", " ").title(),
                f"~{iv['expected_risk_reduction_pct']}%",
                f"{iv['affected_population']:,}",
            ])
        t3 = Table(iv_rows, colWidths=[45 * mm, 22 * mm, 25 * mm, 28 * mm, 30 * mm])
        t3.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F6F63")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DCE4E7")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F5F1")]),
        ]))
        elements.append(t3)
        elements.append(Spacer(1, 6))
        for iv in interventions:
            elements.append(Paragraph(
                f"<b>{iv['intervention_type'].replace('_', ' ').title()}:</b> {iv['reason']}", body_style
            ))
            elements.append(Spacer(1, 3))

    elements.append(Spacer(1, 16))
    elements.append(HRFlowable(width="100%", color=colors.HexColor("#DCE4E7")))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "This report is generated by CIVI-RESQ, an AI-assisted preliminary urban risk assessment and "
        "decision-support system. It does not constitute certified structural safety engineering or a "
        "substitute for on-site professional assessment. Risk scores combine ML-model predictions with "
        "transparent rule-based calculations, as detailed above.",
        disclaimer_style,
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
