"""
app/reports/routes.py
=====================
Reports blueprint — CSV export and PDF summary.

Routes:
  GET /reports/         — Report index page
  GET /reports/csv      — Export all devices as CSV
  GET /reports/alerts   — Export all alerts as CSV
  GET /reports/logs     — Export device logs as CSV
  GET /reports/pdf      — Export full PDF report (ReportLab)
"""
import csv
import io
from datetime import datetime
from flask import (Blueprint, render_template, make_response,
                   request, current_app)
from flask_login import login_required
from ..models import Device, Alert, DeviceLog, Statistic

reports_bp = Blueprint("reports", __name__)


def _csv_response(filename: str, headers: list, rows: list):
    """Build a Flask CSV file response."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)

    resp = make_response(output.getvalue())
    resp.headers["Content-Type"]        = "text/csv"
    resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return resp


@reports_bp.route("/")
@login_required
def index():
    """Report download hub."""
    total     = Device.query.count()
    online    = Device.query.filter_by(status="online").count()
    total_al  = Alert.query.count()
    unresolved= Alert.query.filter_by(is_resolved=False).count()
    return render_template(
        "reports/index.html",
        title      = "Reports",
        total      = total,
        online     = online,
        total_al   = total_al,
        unresolved = unresolved,
        generated  = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    )


@reports_bp.route("/csv")
@login_required
def export_devices_csv():
    """Download all devices as CSV."""
    devices = Device.query.order_by(Device.last_seen.desc()).all()
    headers = ["ID", "IP Address", "MAC Address", "Hostname", "Vendor",
               "Type", "Status", "Category", "Trusted", "Blocked",
               "First Seen", "Last Seen"]
    rows = [
        [d.id, d.ip_address, d.mac_address, d.hostname, d.vendor,
         d.device_type, d.status, d.category,
         "Yes" if d.is_trusted else "No",
         "Yes" if d.is_blocked else "No",
         d.first_seen, d.last_seen]
        for d in devices
    ]
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return _csv_response(f"devices_{ts}.csv", headers, rows)


@reports_bp.route("/alerts")
@login_required
def export_alerts_csv():
    """Download all alerts as CSV."""
    alerts  = Alert.query.order_by(Alert.created_at.desc()).all()
    headers = ["ID", "Type", "Severity", "Title", "Message",
               "Read", "Resolved", "Created At"]
    rows = [
        [a.id, a.alert_type, a.severity, a.title,
         a.message[:120],
         "Yes" if a.is_read else "No",
         "Yes" if a.is_resolved else "No",
         a.created_at]
        for a in alerts
    ]
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return _csv_response(f"alerts_{ts}.csv", headers, rows)


@reports_bp.route("/logs")
@login_required
def export_logs_csv():
    """Download device event logs as CSV."""
    limit  = request.args.get("limit", 500, type=int)
    logs   = (DeviceLog.query
              .order_by(DeviceLog.logged_at.desc())
              .limit(limit)
              .all())
    headers = ["Log ID", "Device ID", "Event", "IP at Event",
               "Details", "Logged At"]
    rows = [
        [l.id, l.device_id, l.event_type, l.ip_address,
         (l.details or "")[:120], l.logged_at]
        for l in logs
    ]
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return _csv_response(f"device_logs_{ts}.csv", headers, rows)


@reports_bp.route("/pdf")
@login_required
def export_pdf():
    """
    Generate a PDF summary report using ReportLab.
    Falls back to a plain-text error if ReportLab is unavailable.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, HRFlowable)
        from reportlab.lib.units import cm

        buffer  = io.BytesIO()
        doc     = SimpleDocTemplate(buffer, pagesize=A4,
                                    rightMargin=2*cm, leftMargin=2*cm,
                                    topMargin=2*cm, bottomMargin=2*cm)
        styles  = getSampleStyleSheet()
        story   = []

        # Title
        title_style = ParagraphStyle("Title2", parent=styles["Title"],
                                      fontSize=20, spaceAfter=6)
        story.append(Paragraph("Smart Network Monitoring Report", title_style))
        story.append(Paragraph(
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            styles["Normal"]
        ))
        story.append(HRFlowable(width="100%", thickness=1,
                                color=colors.HexColor("#4361ee")))
        story.append(Spacer(1, 0.4*cm))

        # Summary
        story.append(Paragraph("Network Summary", styles["Heading2"]))
        total   = Device.query.count()
        online  = Device.query.filter_by(status="online").count()
        offline = Device.query.filter_by(status="offline").count()
        trusted = Device.query.filter_by(is_trusted=True).count()
        blocked = Device.query.filter_by(is_blocked=True).count()
        alerts  = Alert.query.count()
        unread  = Alert.query.filter_by(is_read=False).count()

        summary_data = [
            ["Metric", "Value"],
            ["Total Devices", total],
            ["Online Devices", online],
            ["Offline Devices", offline],
            ["Trusted Devices", trusted],
            ["Blocked Devices", blocked],
            ["Total Alerts", alerts],
            ["Unread Alerts", unread],
        ]
        t = Table(summary_data, colWidths=[8*cm, 4*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4361ee")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f8f9fa")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.4*cm))

        # Device table
        story.append(Paragraph("Device List", styles["Heading2"]))
        devices = Device.query.order_by(Device.last_seen.desc()).limit(30).all()
        dev_data = [["IP", "MAC", "Hostname", "Vendor", "Status", "Trusted"]]
        for d in devices:
            dev_data.append([
                d.ip_address, d.mac_address, d.hostname[:20],
                d.vendor[:18], d.status,
                "✓" if d.is_trusted else "✗"
            ])
        dt = Table(dev_data, colWidths=[3*cm, 4.2*cm, 3.5*cm, 3*cm, 2*cm, 1.5*cm])
        dt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4361ee")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 7.5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f8f9fa")]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dee2e6")),
        ]))
        story.append(dt)

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        resp = make_response(pdf_bytes)
        resp.headers["Content-Type"]        = "application/pdf"
        ts  = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        resp.headers["Content-Disposition"] = f"attachment; filename=network_report_{ts}.pdf"
        return resp

    except ImportError:
        resp = make_response("ReportLab not installed. Run: pip install reportlab")
        resp.headers["Content-Type"] = "text/plain"
        return resp, 500
