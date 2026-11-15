import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

from app.models.case import InvestigationCase
from app.models.evidence import EvidenceRecord
from app.models.security_event import SecurityEvent
from app.forensics.metadata import inspect_evidence_metadata


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print 'Page X of Y' in footer."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header running line
        self.drawString(54, 755, "FORENSIGHT — DIGITAL FORENSICS INVESTIGATION TOOLKIT")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 747, 558, 747)

        # Footer running line
        self.line(54, 45, 558, 45)
        footer_text = f"CONFIDENTIAL & RESTRICTED — Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 33, footer_text)
        self.drawString(54, 33, "OFFICIAL FORENSIC INCIDENT INQUIRY REPORT")
        self.restoreState()


def format_bytes(b: int) -> str:
    if b == 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


def generate_case_pdf_report(
    case: InvestigationCase,
    evidences: List[EvidenceRecord],
    events: List[SecurityEvent],
    vault_dir: Path,
) -> bytes:
    """Generates an official, publication-quality forensic investigation PDF report.

    Includes full chain-of-custody, SHA-256 evidence verification, metadata anomalies,
    security event telemetry, chronological timeline highlights, and legal disclaimers.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom Forensics Palette
    c_primary = colors.HexColor("#0f172a")     # Deep slate
    c_accent = colors.HexColor("#0284c7")      # Forensic blue
    c_dark = colors.HexColor("#1e293b")        # Border/dark
    c_light = colors.HexColor("#f8fafc")       # Table alt
    c_danger = colors.HexColor("#b91c1c")      # Critical red
    c_success = colors.HexColor("#047857")     # Verified green
    c_muted = colors.HexColor("#64748b")       # Subtext slate

    # Typography Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=c_primary,
    )
    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=c_muted,
    )
    h1_style = ParagraphStyle(
        "H1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=c_dark,
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=c_dark,
    )
    body_bold = ParagraphStyle(
        "BodyBold",
        parent=body_style,
        fontName="Helvetica-Bold",
    )
    mono_style = ParagraphStyle(
        "Mono",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7.5,
        leading=9.5,
        textColor=c_primary,
    )
    mono_danger = ParagraphStyle(
        "MonoDanger",
        parent=mono_style,
        textColor=c_danger,
        fontName="Courier-Bold",
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10.5,
        textColor=c_muted,
    )
    cell_style = ParagraphStyle(
        "TableCell",
        parent=body_style,
        fontSize=7.5,
        leading=10,
    )
    cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=body_bold,
        fontSize=7.5,
        leading=10,
    )
    cell_mono = ParagraphStyle(
        "TableCellMono",
        parent=mono_style,
        fontSize=7,
        leading=9,
    )

    story = []

    # Title & Incident Header
    report_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    story.append(Paragraph("DIGITAL FORENSICS INVESTIGATION REPORT", title_style))
    story.append(Paragraph(f"Case File: <b>{case.case_number}</b> &bull; Generated: {report_time_utc}", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=0, spaceAfter=12))

    # SECTION 1: Case Summary Overview Table
    story.append(Paragraph("1. INVESTIGATION SUMMARY & CONTEXT", h1_style))
    case_info_data = [
        [
            Paragraph("<b>Case Number:</b>", body_style),
            Paragraph(f"<font color='#0284c7'><b>{case.case_number}</b></font>", body_style),
            Paragraph("<b>Current Status:</b>", body_style),
            Paragraph(f"<b>{case.status}</b>", body_style),
        ],
        [
            Paragraph("<b>Case Title:</b>", body_style),
            Paragraph(case.title, body_style),
            Paragraph("<b>Priority Level:</b>", body_style),
            Paragraph(f"<b>{case.priority}</b>", body_style),
        ],
        [
            Paragraph("<b>Primary Investigator:</b>", body_style),
            Paragraph(case.investigator_name, body_style),
            Paragraph("<b>Lead Analyst:</b>", body_style),
            Paragraph(case.lead_analyst or "Unassigned", body_style),
        ],
        [
            Paragraph("<b>Opened Date (UTC):</b>", body_style),
            Paragraph(case.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), body_style),
            Paragraph("<b>Last Updated (UTC):</b>", body_style),
            Paragraph(case.updated_at.strftime("%Y-%m-%d %H:%M:%S UTC"), body_style),
        ],
    ]

    t_case = Table(case_info_data, colWidths=[100, 160, 100, 144])
    t_case.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), c_light),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(t_case)
    story.append(Spacer(1, 8))

    # Incident Scope / Description
    if case.description:
        story.append(Paragraph(f"<b>Incident Background & Hypothesis:</b> {case.description}", body_style))
        story.append(Spacer(1, 10))

    # SECTION 2: Evidence Inventory & Hash Verification
    story.append(Paragraph("2. EVIDENCE INVENTORY & CRYPTOGRAPHIC INTEGRITY", h1_style))
    if not evidences:
        story.append(Paragraph("<i>No physical or digital evidence artifacts are currently secured to this case.</i>", body_style))
    else:
        ev_header = [
            Paragraph("<b>Tag</b>", body_bold),
            Paragraph("<b>Original Artifact</b>", body_bold),
            Paragraph("<b>Size / MIME</b>", body_bold),
            Paragraph("<b>Acquisition SHA-256</b>", body_bold),
            Paragraph("<b>Status</b>", body_bold),
        ]
        ev_rows = [ev_header]

        for ev in evidences:
            status_color = "#047857" if ev.integrity_status == "VERIFIED" else "#b91c1c"
            status_p = Paragraph(f"<font color='{status_color}'><b>{ev.integrity_status}</b></font>", body_style)

            ev_rows.append([
                Paragraph(f"<b>{ev.evidence_number}</b>", body_style),
                Paragraph(f"{ev.source_filename}<br/><font color='#64748b' size='6.5'>By: {ev.acquired_by}</font>", body_style),
                Paragraph(f"{format_bytes(ev.file_size_bytes)}<br/><font color='#64748b' size='6.5'>{ev.mime_type}</font>", body_style),
                Paragraph(f"<font size='6.5'>{ev.sha256_hash}</font>", mono_style),
                status_p,
            ])

        t_evidence = Table(ev_rows, colWidths=[45, 120, 85, 195, 59])
        t_evidence.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )
        story.append(t_evidence)

    story.append(Spacer(1, 10))

    # SECTION 3: File Metadata & Heuristic Indicators
    story.append(Paragraph("3. FILE METADATA & INVESTIGATIVE ANOMALIES", h1_style))
    indicators_found = False

    for ev in evidences:
        meta = inspect_evidence_metadata(
            vault_dir=vault_dir,
            stored_filename=ev.stored_filename,
            source_filename=ev.source_filename,
            acquired_at=ev.acquired_at,
            original_sha256=ev.sha256_hash,
            md5_hash=ev.md5_hash,
        )
        inds = meta.get("investigative_indicators", [])
        if inds:
            indicators_found = True
            story.append(Paragraph(f"<b>Artifact {ev.evidence_number} ({ev.source_filename}):</b>", h2_style))
            for ind in inds:
                ind_color = "#b91c1c" if ind["severity"] == "HIGH" else "#d97706"
                p_ind = Paragraph(
                    f"&bull; <font color='{ind_color}'><b>[{ind['severity']}] {ind['rule']}:</b></font> {ind['description']}",
                    body_style,
                )
                story.append(p_ind)
            story.append(Spacer(1, 4))

    if not indicators_found:
        story.append(Paragraph("<i>No suspicious compound extensions, executable disguises, or magic-byte signature mismatches were detected in secured evidence.</i>", body_style))

    story.append(Spacer(1, 10))

    # SECTION 4: Security Events & Log Findings
    story.append(Paragraph("4. SECURITY EVENT TELEMETRY & RULE CORRELATION", h1_style))
    if not events:
        story.append(Paragraph("<i>No security events or imported log records have been linked to this case.</i>", body_style))
    else:
        # Breakdown statistics
        sev_counts: Dict[str, int] = {}
        for e in events:
            sev_counts[e.severity] = sev_counts.get(e.severity, 0) + 1

        summary_parts = [f"<b>{sev}:</b> {count}" for sev, count in sorted(sev_counts.items())]
        story.append(Paragraph(f"<b>Total Events Correlated:</b> {len(events)} &nbsp;({ ' &bull; '.join(summary_parts) })", body_style))
        story.append(Spacer(1, 6))

        # Check for correlated security findings / heuristic detections (e.g. SUSPICIOUS_INDICATOR)
        findings = [e for e in events if e.event_type == "SUSPICIOUS_INDICATOR"]
        telemetry_events = [e for e in events if e.event_type != "SUSPICIOUS_INDICATOR"]

        if findings:
            story.append(Paragraph("<b>Correlated Security Findings & Rule Detections:</b>", h2_style))
            finding_header = [
                Paragraph("<b>Severity</b>", cell_bold),
                Paragraph("<b>Detection Finding & Rule Summary</b>", cell_bold),
                Paragraph("<b>Affected Entity</b>", cell_bold),
                Paragraph("<b>Detected Indicators / ATT&CK</b>", cell_bold),
            ]
            finding_rows = [finding_header]
            sev_priority = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
            sorted_findings = sorted(findings, key=lambda x: (sev_priority.get(x.severity, 99), x.timestamp))

            for f in sorted_findings:
                f_color = "#b91c1c" if f.severity in ["CRITICAL", "HIGH"] else ("#d97706" if f.severity == "MEDIUM" else "#0284c7")
                ent_parts = []
                if f.source_ip:
                    ent_parts.append(f"<b>IP:</b> {f.source_ip}")
                if f.user_account:
                    ent_parts.append(f"<b>User:</b> {f.user_account}")
                ent_text = "<br/>".join(ent_parts) if ent_parts else "—"

                tags_text = f.indicator_tags if f.indicator_tags else "—"

                finding_rows.append([
                    Paragraph(f"<font color='{f_color}'><b>{f.severity}</b></font>", cell_style),
                    Paragraph(f.description, cell_style),
                    Paragraph(ent_text, cell_style),
                    Paragraph(f"<font size='7' color='#0284c7'><b>{tags_text}</b></font>", cell_style),
                ])

            t_findings = Table(finding_rows, colWidths=[55, 215, 95, 139])
            t_findings.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fee2e2")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#fca5a5")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#fecaca")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ])
            )
            story.append(t_findings)
            story.append(Spacer(1, 8))

        # Show event telemetry stream
        story.append(Paragraph("<b>Security Telemetry & Event Audit Stream:</b>", h2_style))
        evt_header = [
            Paragraph("<b>Timestamp (UTC)</b>", cell_bold),
            Paragraph("<b>Type</b>", cell_bold),
            Paragraph("<b>Severity</b>", cell_bold),
            Paragraph("<b>Entity / Host</b>", cell_bold),
            Paragraph("<b>Event Details & Indicators</b>", cell_bold),
        ]
        evt_rows = [evt_header]

        # Use telemetry events if findings are separated, or all events if no separate findings
        display_events = telemetry_events if findings else events
        sorted_events = sorted(display_events, key=lambda x: x.timestamp, reverse=True)

        for e in sorted_events[:30]:
            sev_color = "#b91c1c" if e.severity in ["CRITICAL", "HIGH"] else ("#d97706" if e.severity == "MEDIUM" else "#0284c7")
            ent_parts = []
            if e.source_ip:
                ent_parts.append(f"<b>IP:</b> {e.source_ip}")
            if e.user_account:
                ent_parts.append(f"<b>User:</b> {e.user_account}")
            ent_text = "<br/>".join(ent_parts) if ent_parts else "—"

            desc_text = e.description
            if e.indicator_tags:
                desc_text += f"<br/><font color='#b91c1c' size='6.5'><b>Indicators:</b> {e.indicator_tags}</font>"

            evt_rows.append([
                Paragraph(e.timestamp.strftime("%Y-%m-%d<br/>%H:%M:%S"), cell_mono),
                Paragraph(e.event_type, cell_style),
                Paragraph(f"<font color='{sev_color}'><b>{e.severity}</b></font>", cell_style),
                Paragraph(ent_text, cell_style),
                Paragraph(desc_text, cell_style),
            ])

        t_events = Table(evt_rows, colWidths=[80, 85, 50, 95, 194])
        t_events.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )
        story.append(t_events)

    story.append(Spacer(1, 12))

    # SECTION 5: Investigation Timeline & Milestones
    story.append(Paragraph("5. KEY INVESTIGATION CHRONOLOGY", h1_style))
    chronology_items = []
    for ev in evidences:
        chronology_items.append((ev.acquired_at, "EVIDENCE", f"Evidence artifact secured: {ev.evidence_number} ({ev.source_filename})"))
    for e in events:
        if e.severity in ["CRITICAL", "HIGH"] or e.event_type in ["AUTHENTICATION", "PRIVILEGE_ESCALATION"]:
            chronology_items.append((e.timestamp, e.event_type, e.description))

    chronology_items.sort(key=lambda x: x[0])

    if not chronology_items:
        story.append(Paragraph("<i>No chronological milestones logged.</i>", body_style))
    else:
        for t, cat, desc in chronology_items[:25]:
            story.append(Paragraph(
                f"<font color='#0284c7'><b>[{t.strftime('%Y-%m-%d %H:%M:%S UTC')}]</b></font> &nbsp;<b>{cat}:</b> {desc[:150]}",
                body_style,
            ))
            story.append(Spacer(1, 2))

    story.append(Spacer(1, 14))

    # SECTION 6: Evidentiary Disclaimer & Methodology Notes
    disclaimer_block = [
        Paragraph("<b>EVIDENTIARY DISCLAIMER & METHODOLOGY STATEMENT:</b>", body_bold),
        Paragraph(
            "This document is an automated forensic investigation summary prepared by the ForenSight Digital Forensics Toolkit. "
            "All cryptographic hashes (SHA-256 and MD5) were generated directly from evidence byte streams stored in an isolated, read-only vault. "
            "Investigative indicators and rule-based heuristic alerts represent technical leads and correlation observations; they do not constitute legal proof of malicious intent. "
            "Chain of custody records are maintained with strict UTC timestamps.",
            disclaimer_style,
        ),
    ]
    story.append(KeepTogether(disclaimer_block))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()
