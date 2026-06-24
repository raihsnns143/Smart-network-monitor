"""
app/devices/routes.py
=====================
Device management blueprint.

Routes:
  GET  /devices/           — List / search / filter devices
  GET  /devices/<id>       — Device detail & log history
  POST /devices/<id>/update — Update notes, category, trust status
  POST /devices/<id>/trust  — Mark device as trusted
  POST /devices/<id>/block  — Block / unblock device
  POST /devices/<id>/delete — Delete device record
"""
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, jsonify)
from flask_login import login_required, current_user
from sqlalchemy import or_
from ..models import Device, DeviceLog, Alert
from .. import db

devices_bp = Blueprint("devices", __name__)

CATEGORIES = [
    "Uncategorized", "Router", "PC / Laptop", "Mobile / Tablet",
    "Printer", "Smart TV", "IoT / Smart Home", "Gaming Console",
    "Server", "IP Camera", "Other"
]

DEVICE_TYPES = ["unknown", "router", "pc", "mobile", "iot", "printer"]


@devices_bp.route("/")
@login_required
def list_devices():
    """List all devices with search and filter support."""
    q         = request.args.get("q", "").strip()
    status    = request.args.get("status", "")
    category  = request.args.get("category", "")
    trusted   = request.args.get("trusted", "")
    page      = request.args.get("page", 1, type=int)

    query = Device.query

    if q:
        query = query.filter(or_(
            Device.ip_address.ilike(f"%{q}%"),
            Device.mac_address.ilike(f"%{q}%"),
            Device.hostname.ilike(f"%{q}%"),
            Device.vendor.ilike(f"%{q}%"),
        ))
    if status in ("online", "offline"):
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)
    if trusted == "yes":
        query = query.filter_by(is_trusted=True)
    elif trusted == "no":
        query = query.filter_by(is_trusted=False)

    devices = query.order_by(Device.last_seen.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    return render_template(
        "devices/list.html",
        title      = "Device Management",
        devices    = devices,
        categories = CATEGORIES,
        q          = q,
        status     = status,
        category   = category,
        trusted    = trusted,
    )


@devices_bp.route("/<int:device_id>")
@login_required
def detail(device_id: int):
    """Device detail page — info + log history."""
    device = Device.query.get_or_404(device_id)
    logs   = (DeviceLog.query
              .filter_by(device_id=device_id)
              .order_by(DeviceLog.logged_at.desc())
              .limit(50)
              .all())
    alerts = (Alert.query
              .filter_by(device_id=device_id)
              .order_by(Alert.created_at.desc())
              .limit(20)
              .all())
    return render_template(
        "devices/detail.html",
        title      = f"Device — {device.ip_address}",
        device     = device,
        logs       = logs,
        alerts     = alerts,
        categories = CATEGORIES,
        device_types = DEVICE_TYPES,
    )


@devices_bp.route("/<int:device_id>/update", methods=["POST"])
@login_required
def update_device(device_id: int):
    """Update device notes, category, device type."""
    device = Device.query.get_or_404(device_id)

    device.notes       = request.form.get("notes", device.notes)
    device.category    = request.form.get("category", device.category)
    device.device_type = request.form.get("device_type", device.device_type)
    device.hostname    = request.form.get("hostname", device.hostname)

    db.session.add(DeviceLog(
        device_id  = device.id,
        event_type = "update",
        details    = f"Updated by {current_user.username}",
    ))
    db.session.commit()
    flash("Device updated successfully.", "success")
    return redirect(url_for("devices.detail", device_id=device_id))


@devices_bp.route("/<int:device_id>/trust", methods=["POST"])
@login_required
def toggle_trust(device_id: int):
    """Toggle the device's trusted status."""
    device = Device.query.get_or_404(device_id)
    device.is_trusted = not device.is_trusted

    # Optionally sync whitelist
    from ..models import Whitelist
    if device.is_trusted:
        if not Whitelist.query.filter_by(mac_address=device.mac_address).first():
            db.session.add(Whitelist(
                mac_address = device.mac_address,
                label       = device.hostname,
                added_by    = current_user.id,
            ))
        flash(f"{device.hostname} marked as TRUSTED.", "success")
    else:
        wl = Whitelist.query.filter_by(mac_address=device.mac_address).first()
        if wl:
            db.session.delete(wl)
        flash(f"{device.hostname} marked as UNTRUSTED.", "warning")

    db.session.commit()
    return redirect(url_for("devices.detail", device_id=device_id))


@devices_bp.route("/<int:device_id>/block", methods=["POST"])
@login_required
def toggle_block(device_id: int):
    """Block or unblock a device."""
    device = Device.query.get_or_404(device_id)
    device.is_blocked = not device.is_blocked

    if device.is_blocked:
        db.session.add(Alert(
            device_id  = device.id,
            alert_type = "blocked_device",
            severity   = "medium",
            title      = f"Device Blocked: {device.ip_address}",
            message    = f"Device {device.mac_address} was blocked by {current_user.username}.",
        ))
        flash(f"Device {device.ip_address} has been BLOCKED.", "danger")
    else:
        flash(f"Device {device.ip_address} has been UNBLOCKED.", "success")

    db.session.commit()
    return redirect(url_for("devices.detail", device_id=device_id))


@devices_bp.route("/<int:device_id>/delete", methods=["POST"])
@login_required
def delete_device(device_id: int):
    """Permanently delete a device record and all its logs."""
    device = Device.query.get_or_404(device_id)
    name   = device.ip_address
    db.session.delete(device)
    db.session.commit()
    flash(f"Device {name} and all its logs have been deleted.", "info")
    return redirect(url_for("devices.list_devices"))


@devices_bp.route("/api/list")
@login_required
def api_list():
    """Return all devices as JSON (for AJAX tables)."""
    devices = Device.query.order_by(Device.last_seen.desc()).all()
    return jsonify([d.to_dict() for d in devices])
