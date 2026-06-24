"""
app/monitor/routes.py
=====================
Real-time monitor blueprint.

Routes:
  GET  /monitor/           — Real-time monitor page
  POST /monitor/scan       — Trigger a network scan
  GET  /monitor/api/status — JSON status for auto-refresh (AJAX)
  GET  /monitor/api/stats  — JSON network I/O stats
"""
import json
from datetime import datetime
from flask import (Blueprint, render_template, jsonify,
                   request, current_app, flash, redirect, url_for)
from flask_login import login_required, current_user
from ..models import Device, DeviceLog, Alert, ScanSession, Statistic, Whitelist
from .. import db
from .scanner import scan_network, get_network_stats

monitor_bp = Blueprint("monitor", __name__)


def _process_scan_results(scan_result: dict) -> dict:
    """
    Persist scan results to the database.

    - Creates new Device records for first-time MACs.
    - Updates ip, hostname, vendor, status, last_seen for known devices.
    - Marks devices NOT in this scan as offline.
    - Creates DeviceLog entries for online/offline transitions.
    - Generates Alert for unknown (untrusted) devices.

    Returns summary dict.
    """
    devices_data  = scan_result["devices"]
    scanned_macs  = {d["mac_address"] for d in devices_data}
    new_count     = 0
    online_count  = 0

    # ── Get whitelisted MACs ──────────────────────────────────────────────────
    from ..models import Whitelist
    trusted_macs = {w.mac_address for w in Whitelist.query.all()}

    # ── Upsert every discovered device ───────────────────────────────────────
    for d in devices_data:
        existing = Device.query.filter_by(mac_address=d["mac_address"]).first()

        if existing is None:
            # Brand-new device
            device = Device(
                ip_address  = d["ip_address"],
                mac_address = d["mac_address"],
                hostname    = d.get("hostname", "Unknown"),
                vendor      = d.get("vendor",   "Unknown"),
                status      = "online",
                is_trusted  = d["mac_address"] in trusted_macs,
                first_seen  = datetime.utcnow(),
                last_seen   = datetime.utcnow(),
            )
            db.session.add(device)
            db.session.flush()   # get device.id

            # Log first appearance
            db.session.add(DeviceLog(
                device_id  = device.id,
                event_type = "online",
                ip_address = d["ip_address"],
                details    = f"First detected via {d.get('scan_method','scan')}",
            ))
            new_count += 1

            # Alert for unknown device
            if not device.is_trusted:
                db.session.add(Alert(
                    device_id  = device.id,
                    alert_type = "new_device",
                    severity   = "high",
                    title      = f"New Unknown Device: {d['ip_address']}",
                    message    = (
                        f"A previously unseen device joined the network.\n"
                        f"IP: {d['ip_address']}  MAC: {d['mac_address']}\n"
                        f"Vendor: {d.get('vendor','Unknown')}"
                    ),
                ))
        else:
            prev_status = existing.status
            existing.ip_address = d["ip_address"]
            existing.hostname   = d.get("hostname", existing.hostname)
            existing.vendor     = d.get("vendor",   existing.vendor)
            existing.status     = "online"
            existing.last_seen  = datetime.utcnow()

            if prev_status == "offline":
                db.session.add(DeviceLog(
                    device_id  = existing.id,
                    event_type = "online",
                    ip_address = d["ip_address"],
                    details    = "Device came back online",
                ))

        online_count += 1

    # ── Mark missing devices as offline ──────────────────────────────────────
    all_devices = Device.query.all()
    for device in all_devices:
        if device.mac_address not in scanned_macs and device.status == "online":
            device.status = "offline"
            db.session.add(DeviceLog(
                device_id  = device.id,
                event_type = "offline",
                ip_address = device.ip_address,
                details    = "Device not found in scan",
            ))

    db.session.commit()

    return {
        "online":  online_count,
        "new":     new_count,
        "total":   Device.query.count(),
        "offline": Device.query.filter_by(status="offline").count(),
    }


@monitor_bp.route("/")
@login_required
def realtime():
    """Real-time monitor page."""
    total   = Device.query.count()
    online  = Device.query.filter_by(status="online").count()
    offline = Device.query.filter_by(status="offline").count()
    recent  = Device.query.order_by(Device.last_seen.desc()).limit(20).all()
    scan_interval = current_app.config.get("SCAN_INTERVAL", 30)
    return render_template(
        "monitor/realtime.html",
        title        = "Real-Time Monitor",
        total        = total,
        online       = online,
        offline      = offline,
        recent       = recent,
        scan_interval= scan_interval,
    )


@monitor_bp.route("/scan", methods=["POST"])
@login_required
def trigger_scan():
    """Manually trigger a network scan."""
    network = current_app.config.get("NETWORK_RANGE")

    # Create scan session record
    session_rec = ScanSession(
        network_range = network,
        scan_type     = "arp",
        status        = "running",
        started_at    = datetime.utcnow(),
    )
    db.session.add(session_rec)
    db.session.commit()

    try:
        result  = scan_network(network)
        summary = _process_scan_results(result)

        session_rec.status        = "completed"
        session_rec.completed_at  = datetime.utcnow()
        session_rec.devices_found = summary["online"]
        session_rec.new_devices   = summary["new"]
        session_rec.duration_sec  = result["duration"]

        # Save hourly statistic snapshot
        stats = get_network_stats()
        db.session.add(Statistic(
            total_devices   = summary["total"],
            online_devices  = summary["online"],
            offline_devices = summary["offline"],
            new_devices     = summary["new"],
            total_alerts    = Alert.query.filter_by(is_read=False).count(),
            **stats,
        ))
        db.session.commit()

        flash(
            f"Scan complete — {summary['online']} online, "
            f"{summary['new']} new device(s) found.",
            "success"
        )
    except Exception as e:
        session_rec.status = "failed"
        db.session.commit()
        flash(f"Scan failed: {str(e)}", "danger")

    return redirect(url_for("monitor.realtime"))


@monitor_bp.route("/api/status")
@login_required
def api_status():
    """AJAX endpoint — returns current device counts as JSON."""
    total   = Device.query.count()
    online  = Device.query.filter_by(status="online").count()
    offline = Device.query.filter_by(status="offline").count()
    unread  = Alert.query.filter_by(is_read=False).count()
    devices = [d.to_dict() for d in
               Device.query.order_by(Device.last_seen.desc()).limit(20).all()]
    return jsonify({
        "total":    total,
        "online":   online,
        "offline":  offline,
        "unread_alerts": unread,
        "devices":  devices,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    })


@monitor_bp.route("/api/stats")
@login_required
def api_stats():
    """Return network I/O statistics as JSON."""
    stats = get_network_stats()
    return jsonify(stats)
