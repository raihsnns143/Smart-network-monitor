"""
app/models.py
=============
SQLAlchemy ORM models — one class per database table.

Relationships:
  User        ─┬─< Alert (resolved_by)
               └─< Whitelist (added_by)

  Device      ─┬─< DeviceLog
               └─< Alert
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


# ──────────────────────────────────────────────────────────────────────────────
# User
# ──────────────────────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    """Admin / viewer accounts."""
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username      = db.Column(db.String(80),  nullable=False, unique=True)
    email         = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.Enum("admin", "viewer"), default="admin")
    is_active     = db.Column(db.Boolean, default=True, nullable=False)
    avatar        = db.Column(db.String(255), nullable=True)
    last_login    = db.Column(db.DateTime, nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow,
                              onupdate=datetime.utcnow)

    # relationships
    alerts_resolved = db.relationship("Alert",     backref="resolver",
                                      foreign_keys="Alert.resolved_by",
                                      lazy="dynamic")
    whitelist_added = db.relationship("Whitelist", backref="added_by_user",
                                      foreign_keys="Whitelist.added_by",
                                      lazy="dynamic")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.username}>"


# ──────────────────────────────────────────────────────────────────────────────
# Device
# ──────────────────────────────────────────────────────────────────────────────
class Device(db.Model):
    """Every unique network device ever discovered."""
    __tablename__ = "devices"

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip_address  = db.Column(db.String(45),  nullable=False, index=True)
    mac_address = db.Column(db.String(17),  nullable=False, unique=True, index=True)
    hostname    = db.Column(db.String(255), default="Unknown")
    vendor      = db.Column(db.String(255), default="Unknown")
    device_type = db.Column(
        db.Enum("router", "pc", "mobile", "iot", "printer", "unknown"),
        default="unknown"
    )
    os_guess    = db.Column(db.String(100), nullable=True)
    status      = db.Column(db.Enum("online", "offline"), default="offline", index=True)
    is_trusted  = db.Column(db.Boolean, default=False, index=True)
    is_blocked  = db.Column(db.Boolean, default=False)
    category    = db.Column(db.String(100), default="Uncategorized")
    notes       = db.Column(db.Text, nullable=True)
    open_ports  = db.Column(db.Text, nullable=True)   # stored as JSON string
    first_seen  = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen   = db.Column(db.DateTime, default=datetime.utcnow)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow,
                            onupdate=datetime.utcnow)

    # relationships
    logs   = db.relationship("DeviceLog", backref="device", lazy="dynamic",
                             cascade="all, delete-orphan")
    alerts = db.relationship("Alert",     backref="device", lazy="dynamic")

    @property
    def status_badge(self) -> str:
        return "success" if self.status == "online" else "secondary"

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "ip":          self.ip_address,
            "mac":         self.mac_address,
            "hostname":    self.hostname,
            "vendor":      self.vendor,
            "type":        self.device_type,
            "status":      self.status,
            "is_trusted":  self.is_trusted,
            "is_blocked":  self.is_blocked,
            "category":    self.category,
            "last_seen":   self.last_seen.strftime("%Y-%m-%d %H:%M:%S") if self.last_seen else None,
            "first_seen":  self.first_seen.strftime("%Y-%m-%d %H:%M:%S") if self.first_seen else None,
        }

    def __repr__(self) -> str:
        return f"<Device {self.ip_address} | {self.mac_address}>"


# ──────────────────────────────────────────────────────────────────────────────
# DeviceLog
# ──────────────────────────────────────────────────────────────────────────────
class DeviceLog(db.Model):
    """Immutable audit log of online/offline events."""
    __tablename__ = "device_logs"

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id  = db.Column(db.Integer, db.ForeignKey("devices.id", ondelete="CASCADE"),
                           nullable=False, index=True)
    event_type = db.Column(
        db.Enum("online", "offline", "scan", "update"), nullable=False
    )
    ip_address = db.Column(db.String(45), nullable=True)
    details    = db.Column(db.Text, nullable=True)
    logged_at  = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<DeviceLog device={self.device_id} event={self.event_type}>"


# ──────────────────────────────────────────────────────────────────────────────
# Alert
# ──────────────────────────────────────────────────────────────────────────────
class Alert(db.Model):
    """Admin notifications for suspicious / notable events."""
    __tablename__ = "alerts"

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id   = db.Column(db.Integer, db.ForeignKey("devices.id", ondelete="SET NULL"),
                            nullable=True)
    alert_type  = db.Column(
        db.Enum("unknown_device", "port_scan", "ip_conflict",
                "blocked_device", "high_traffic", "new_device"),
        default="unknown_device", nullable=False
    )
    severity    = db.Column(
        db.Enum("low", "medium", "high", "critical"), default="medium"
    )
    title       = db.Column(db.String(255), nullable=False)
    message     = db.Column(db.Text, nullable=False)
    is_read     = db.Column(db.Boolean, default=False, index=True)
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"),
                            nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    @property
    def severity_color(self) -> str:
        return {
            "low":      "info",
            "medium":   "warning",
            "high":     "danger",
            "critical": "dark",
        }.get(self.severity, "secondary")

    def __repr__(self) -> str:
        return f"<Alert {self.alert_type} | {self.severity}>"


# ──────────────────────────────────────────────────────────────────────────────
# Statistics
# ──────────────────────────────────────────────────────────────────────────────
class Statistic(db.Model):
    """Hourly snapshot of network metrics."""
    __tablename__ = "statistics"

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recorded_at     = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    total_devices   = db.Column(db.Integer, default=0)
    online_devices  = db.Column(db.Integer, default=0)
    offline_devices = db.Column(db.Integer, default=0)
    new_devices     = db.Column(db.Integer, default=0)
    total_alerts    = db.Column(db.Integer, default=0)
    bytes_sent      = db.Column(db.BigInteger, default=0)
    bytes_recv      = db.Column(db.BigInteger, default=0)
    packets_sent    = db.Column(db.BigInteger, default=0)
    packets_recv    = db.Column(db.BigInteger, default=0)


# ──────────────────────────────────────────────────────────────────────────────
# Whitelist
# ──────────────────────────────────────────────────────────────────────────────
class Whitelist(db.Model):
    """MAC addresses explicitly trusted by an admin."""
    __tablename__ = "whitelist"

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mac_address = db.Column(db.String(17), nullable=False, unique=True, index=True)
    label       = db.Column(db.String(255), nullable=True)
    added_by    = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"),
                            nullable=True)
    added_at    = db.Column(db.DateTime, default=datetime.utcnow)


# ──────────────────────────────────────────────────────────────────────────────
# ScanSession
# ──────────────────────────────────────────────────────────────────────────────
class ScanSession(db.Model):
    """Records metadata about each full network scan."""
    __tablename__ = "scan_sessions"

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    network_range = db.Column(db.String(50),  nullable=False)
    devices_found = db.Column(db.Integer, default=0)
    new_devices   = db.Column(db.Integer, default=0)
    scan_type     = db.Column(db.Enum("arp", "nmap", "ping"), default="arp")
    duration_sec  = db.Column(db.Float, nullable=True)
    started_at    = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    completed_at  = db.Column(db.DateTime, nullable=True)
    status        = db.Column(
        db.Enum("running", "completed", "failed"), default="running"
    )
