#!/usr/bin/env python3
"""
PDF compliance report generator using ReportLab.

Generates professional PDF reports suitable for auditors and compliance teams.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_pdf_report(
    framework_name: str,
    results: Dict[str, Any],
    output_path: str,
) -> str:
    """
    Generate a professional PDF compliance report.

    Args:
        framework_name: Name of compliance framework (e.g., "SOC-2", "ISO 27001")
        results: Compliance check results dictionary containing:
                 - framework: Framework metadata
                 - controls: List of control check results
                 - summary: Overall summary statistics
        output_path: Path where PDF will be saved

    Returns:
        str: Path to generated PDF file
    """
    # Create document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    # Build story (document content)
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold',
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        leading=14,
    )

    # Title page
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph(f"{framework_name} Compliance Report", title_style))
    story.append(Spacer(1, 0.3 * inch))

    # Metadata
    metadata = [
        ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')],
        ['Framework:', results.get('framework', {}).get('name', framework_name)],
        ['Version:', results.get('framework', {}).get('version', 'N/A')],
        ['Vault Instance:', 'Lockr Secrets Manager'],
    ]

    metadata_table = Table(metadata, colWidths=[2 * inch, 4 * inch])
    metadata_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7f8c8d')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(metadata_table)
    story.append(Spacer(1, 0.5 * inch))

    # Summary section
    summary = results.get('summary', {})
    score = summary.get('compliance_score', 0)
    total = summary.get('total_controls', 0)
    passed = summary.get('controls_passed', 0)
    failed = summary.get('controls_failed', 0)

    # Status indicator
    status_color = colors.HexColor('#27ae60') if score >= 90 else \
                   colors.HexColor('#f39c12') if score >= 70 else \
                   colors.HexColor('#e74c3c')

    status_text = "COMPLIANT" if score >= 90 else \
                  "PARTIALLY COMPLIANT" if score >= 70 else \
                  "NON-COMPLIANT"

    summary_data = [
        ['Compliance Score', f'{score}%'],
        ['Status', status_text],
        ['Controls Checked', str(total)],
        ['Passed', str(passed)],
        ['Failed', str(failed)],
    ]

    summary_table = Table(summary_data, colWidths=[3 * inch, 3 * inch])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (1, 0), (1, 0), status_color),
        ('TEXTCOLOR', (1, 1), (1, 1), status_color),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ecf0f1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(summary_table)
    story.append(PageBreak())

    # Controls details
    story.append(Paragraph("Control Assessment Details", heading_style))
    story.append(Spacer(1, 0.2 * inch))

    controls = results.get('controls', [])

    for control in controls:
        control_id = control.get('id', 'Unknown')
        control_name = control.get('name', 'Unknown Control')
        status = control.get('status', 'unknown')
        evidence = control.get('evidence', 'No evidence provided')
        checked_at = control.get('checked_at', 'N/A')

        # Control header
        status_icon = "✓" if status == "pass" else "✗" if status == "fail" else "⚠"
        status_color_text = colors.HexColor('#27ae60') if status == "pass" else \
                           colors.HexColor('#e74c3c') if status == "fail" else \
                           colors.HexColor('#f39c12')

        control_header = f'<b>{control_id}</b> - {control_name}'
        story.append(Paragraph(control_header, body_style))

        # Control details table
        control_data = [
            ['Status', f'{status_icon} {status.upper()}'],
            ['Evidence', str(evidence)[:200] + '...' if len(str(evidence)) > 200 else str(evidence)],
            ['Checked', checked_at],
        ]

        control_table = Table(control_data, colWidths=[1.5 * inch, 4.5 * inch])
        control_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (1, 0), (1, 0), status_color_text),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(control_table)
        story.append(Spacer(1, 0.3 * inch))

    # Gap analysis (if any failures)
    if failed > 0:
        story.append(PageBreak())
        story.append(Paragraph("Gap Analysis & Remediation", heading_style))
        story.append(Spacer(1, 0.2 * inch))

        failed_controls = [c for c in controls if c.get('status') == 'fail']

        story.append(Paragraph(
            f"The following {len(failed_controls)} control(s) require remediation:",
            body_style
        ))
        story.append(Spacer(1, 0.1 * inch))

        for control in failed_controls:
            gap_text = f"<b>{control.get('id')}</b> - {control.get('name')}"
            story.append(Paragraph(gap_text, body_style))
            story.append(Paragraph(
                f"<i>Evidence:</i> {control.get('evidence', 'Not available')}",
                body_style
            ))
            story.append(Spacer(1, 0.15 * inch))

    # Footer page
    story.append(PageBreak())
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("About This Report", heading_style))
    story.append(Paragraph(
        """This compliance report was generated automatically by Lockr Secrets Manager.
        The assessment is based on technical controls implemented in the vault and
        audit log analysis. This report should be reviewed with qualified compliance
        professionals before submission to auditors.""",
        body_style
    ))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(
        """For questions about this report or Lockr's compliance automation features,
        please contact hello@lockr.dev or visit https://lockr.dev""",
        body_style
    ))
    story.append(Spacer(1, 0.3 * inch))

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_CENTER,
    )
    story.append(Paragraph(
        "Generated by Lockr Secrets Manager — https://lockr.dev",
        footer_style
    ))

    # Build PDF
    doc.build(story)

    return output_path


def generate_summary_pdf(
    framework_name: str,
    score: float,
    total: int,
    passed: int,
    output_path: str,
) -> str:
    """
    Generate a simple one-page summary PDF (for quick sharing).

    Args:
        framework_name: Name of compliance framework
        score: Compliance score percentage (0-100)
        total: Total number of controls
        passed: Number of passed controls
        output_path: Path where PDF will be saved

    Returns:
        str: Path to generated PDF file
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=28,
        alignment=TA_CENTER,
        spaceAfter=40,
    )

    # Title
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph(f"{framework_name} Compliance", title_style))

    # Score
    score_style = ParagraphStyle(
        'Score',
        parent=styles['Normal'],
        fontSize=72,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#27ae60') if score >= 90 else colors.HexColor('#f39c12'),
    )
    story.append(Paragraph(f"<b>{score}%</b>", score_style))

    # Status
    status_text = "COMPLIANT" if score >= 90 else "IN PROGRESS"
    status_style = ParagraphStyle(
        'Status',
        parent=styles['Normal'],
        fontSize=18,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#7f8c8d'),
    )
    story.append(Paragraph(status_text, status_style))
    story.append(Spacer(1, 1 * inch))

    # Details
    details = f"{passed} of {total} controls passing"
    story.append(Paragraph(details, status_style))

    doc.build(story)
    return output_path
