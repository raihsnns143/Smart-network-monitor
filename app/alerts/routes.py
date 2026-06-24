"""
app/alerts/routes.py
====================
Alert management blueprint.

Routes:
  GET  /alerts/               — List all alerts
  POST /alerts/<id>/read      — Mark alert as read
  POST /alerts/<id>/resolve   — Resolve an alert
  POST /alerts/read-all       — Mark all alerts as read
  GET  /alerts/api/unread     — JSON count of unread alerts
"""
from datetime import datetime
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, jsonify)
from flask_login import login_required, current_user
from ..models import Alert
from .. import db

alerts_bp = Blueprint("alerts", __name__)

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


@alerts_bp.route("/")
@login_required
def index():
    """List all alerts — newest first, with filter options."""
    severity  = request.args.get("severity", "")
    atype     = request.args.get("type", "")
    is_read   = request.args.get("read", "")
    page      = request.args.get("page", 1, type=int)

    query = Alert.query

    if severity in ("low", "medium", "high", "critical"):
        query = query.filter_by(severity=severity)
    if atype:
        query = query.filter_by(alert_type=atype)
    if is_read == "unread":
        query = query.filter_by(is_read=False)
    elif is_read == "read":
        query = query.filter_by(is_read=True)

    alerts = query.order_by(Alert.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    unread_count = Alert.query.filter_by(is_read=False).count()

    return render_template(
        "alerts/index.html",
        title        = "Alert Centre",
        alerts       = alerts,
        unread_count = unread_count,
        severity     = severity,
        atype        = atype,
        is_read      = is_read,
    )


@alerts_bp.route("/<int:alert_id>/read", methods=["POST"])
@login_required
def mark_read(alert_id: int):
    """Mark a single alert as read."""
    alert = Alert.query.get_or_404(alert_id)
    alert.is_read = True
    db.session.commit()
    return redirect(url_for("alerts.index"))


@alerts_bp.route("/<int:alert_id>/resolve", methods=["POST"])
@login_required
def resolve(alert_id: int):
    """Mark an alert as resolved."""
    alert = Alert.query.get_or_404(alert_id)
    alert.is_resolved  = True
    alert.is_read      = True
    alert.resolved_by  = current_user.id
    alert.resolved_at  = datetime.utcnow()
    db.session.commit()
    flash("Alert resolved.", "success")
    return redirect(url_for("alerts.index"))


@alerts_bp.route("/read-all", methods=["POST"])
@login_required
def read_all():
    """Mark all unread alerts as read."""
    Alert.query.filter_by(is_read=False).update({"is_read": True})
    db.session.commit()
    flash("All alerts marked as read.", "info")
    return redirect(url_for("alerts.index"))


@alerts_bp.route("/api/unread")
@login_required
def api_unread():
    """JSON endpoint for badge count in navbar."""
    count = Alert.query.filter_by(is_read=False).count()
    return jsonify({"unread": count})
