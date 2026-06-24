"""
app/dashboard/routes.py
=======================
Dashboard blueprint — main analytics view.

Routes:
  GET / (index)          — Main dashboard with charts data
  GET /api/chart-data    — JSON data for Chart.js graphs
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from sqlalchemy import func
from ..models import Device, Alert, Statistic, DeviceLog

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    """Main dashboard page."""
    # ── Summary cards ─────────────────────────────────────────────────────────
    total_devices   = Device.query.count()
    online_devices  = Device.query.filter_by(status="online").count()
    offline_devices = Device.query.filter_by(status="offline").count()
    trusted_devices = Device.query.filter_by(is_trusted=True).count()
    blocked_devices = Device.query.filter_by(is_blocked=True).count()
    unread_alerts   = Alert.query.filter_by(is_read=False).count()
    critical_alerts = Alert.query.filter_by(
                        severity="critical", is_read=False).count()

    # ── Recent alerts ─────────────────────────────────────────────────────────
    recent_alerts = (Alert.query
                     .order_by(Alert.created_at.desc())
                     .limit(5)
                     .all())

    # ── Recently seen devices ─────────────────────────────────────────────────
    recent_devices = (Device.query
                      .order_by(Device.last_seen.desc())
                      .limit(8)
                      .all())

    # ── Device type breakdown ─────────────────────────────────────────────────
    type_breakdown = (Device.query
                      .with_entities(Device.device_type,
                                     func.count(Device.id).label("cnt"))
                      .group_by(Device.device_type)
                      .all())

    # ── Category breakdown ────────────────────────────────────────────────────
    cat_breakdown = (Device.query
                     .with_entities(Device.category,
                                    func.count(Device.id).label("cnt"))
                     .group_by(Device.category)
                     .all())

    return render_template(
        "dashboard/index.html",
        title           = "Dashboard",
        total_devices   = total_devices,
        online_devices  = online_devices,
        offline_devices = offline_devices,
        trusted_devices = trusted_devices,
        blocked_devices = blocked_devices,
        unread_alerts   = unread_alerts,
        critical_alerts = critical_alerts,
        recent_alerts   = recent_alerts,
        recent_devices  = recent_devices,
        type_breakdown  = type_breakdown,
        cat_breakdown   = cat_breakdown,
    )


@dashboard_bp.route("/api/chart-data")
@login_required
def chart_data():
    """
    Return chart data as JSON for Chart.js.

    Response includes:
      - daily_stats: last 7 days of online/offline counts
      - type_chart:  device type distribution
      - alert_chart: alert severity distribution
      - traffic:     bytes sent/recv from statistics table
    """
    now    = datetime.utcnow()
    labels = []
    online_series  = []
    offline_series = []

    for i in range(6, -1, -1):
        day  = now - timedelta(days=i)
        start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        end   = start + timedelta(days=1)

        stat = (Statistic.query
                .filter(Statistic.recorded_at >= start,
                        Statistic.recorded_at < end)
                .order_by(Statistic.recorded_at.desc())
                .first())

        labels.append(day.strftime("%a %d"))
        online_series.append(stat.online_devices  if stat else 0)
        offline_series.append(stat.offline_devices if stat else 0)

    # Device type pie
    type_rows = (Device.query
                 .with_entities(Device.device_type,
                                func.count(Device.id).label("cnt"))
                 .group_by(Device.device_type)
                 .all())
    type_labels  = [r[0].capitalize() for r in type_rows]
    type_data    = [r[1] for r in type_rows]

    # Alert severity doughnut
    sev_rows = (Alert.query
                .with_entities(Alert.severity,
                               func.count(Alert.id).label("cnt"))
                .group_by(Alert.severity)
                .all())
    sev_labels = [r[0].capitalize() for r in sev_rows]
    sev_data   = [r[1] for r in sev_rows]

    # Traffic — last 7 days
    traffic_labels = labels
    traffic_sent   = []
    traffic_recv   = []
    for i in range(6, -1, -1):
        day   = now - timedelta(days=i)
        start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        end   = start + timedelta(days=1)
        stat  = (Statistic.query
                 .filter(Statistic.recorded_at >= start,
                         Statistic.recorded_at < end)
                 .order_by(Statistic.recorded_at.desc())
                 .first())
        traffic_sent.append(round((stat.bytes_sent or 0) / 1024 / 1024, 2) if stat else 0)
        traffic_recv.append(round((stat.bytes_recv or 0) / 1024 / 1024, 2) if stat else 0)

    return jsonify({
        "daily": {
            "labels":  labels,
            "online":  online_series,
            "offline": offline_series,
        },
        "device_types": {
            "labels": type_labels,
            "data":   type_data,
        },
        "alerts": {
            "labels": sev_labels,
            "data":   sev_data,
        },
        "traffic": {
            "labels": traffic_labels,
            "sent":   traffic_sent,
            "recv":   traffic_recv,
        },
    })
