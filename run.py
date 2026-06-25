"""
run.py
======
Application entry point.

Usage:
    python run.py                   # development server
    python run.py --seed            # seed demo data then run
    flask run --host=0.0.0.0        # alternate start

Environment variable FLASK_ENV controls config selection:
    development (default) | production
"""
import sys
import os
from app import create_app, db

app = create_app()


def seed_demo_data() -> None:
    """
    Insert realistic demo devices and alerts so the UI looks
    populated on first launch — useful for demos / presentations.
    """
    from datetime import datetime, timedelta
    from app.models import Device, DeviceLog, Alert, Statistic

    demo_devices = [
        {"ip": "192.168.1.1",  "mac": "00:11:22:33:44:55",
         "hostname": "gateway.local",   "vendor": "Cisco Systems",
         "type": "router",  "category": "Router",  "trusted": True},
        {"ip": "192.168.1.5",  "mac": "AC:DE:48:AB:CD:EF",
         "hostname": "macbook-pro",     "vendor": "Apple",
         "type": "pc",      "category": "PC / Laptop", "trusted": True},
        {"ip": "192.168.1.10", "mac": "B8:27:EB:12:34:56",
         "hostname": "raspberrypi",     "vendor": "Raspberry Pi Foundation",
         "type": "iot",     "category": "IoT / Smart Home", "trusted": True},
        {"ip": "192.168.1.15", "mac": "50:46:5D:78:9A:BC",
         "hostname": "DESKTOP-WIN11",   "vendor": "Microsoft",
         "type": "pc",      "category": "PC / Laptop", "trusted": True},
        {"ip": "192.168.1.20", "mac": "00:23:14:DE:AD:BE",
         "hostname": "hp-printer",      "vendor": "HP",
         "type": "printer", "category": "Printer",   "trusted": True},
        {"ip": "192.168.1.25", "mac": "F0:18:98:56:78:9A",
         "hostname": "iphone-14",       "vendor": "Apple",
         "type": "mobile",  "category": "Mobile / Tablet", "trusted": False},
        {"ip": "192.168.1.30", "mac": "74:D4:35:AA:BB:CC",
         "hostname": "gaming-pc",       "vendor": "Giga-byte",
         "type": "pc",      "category": "Gaming Console", "trusted": False},
        {"ip": "192.168.1.99", "mac": "DE:AD:BE:EF:CA:FE",
         "hostname": "Unknown",         "vendor": "Unknown Vendor",
         "type": "unknown", "category": "Uncategorized", "trusted": False},
    ]

    with app.app_context():
        if Device.query.count() > 0:
            print("[SEED] Devices already exist — skipping demo seed.")
            return

        now = datetime.utcnow()
        for i, d in enumerate(demo_devices):
            device = Device(
                ip_address  = d["ip"],
                mac_address = d["mac"],
                hostname    = d["hostname"],
                vendor      = d["vendor"],
                device_type = d["type"],
                category    = d["category"],
                status      = "online" if i % 3 != 0 else "offline",
                is_trusted  = d["trusted"],
                first_seen  = now - timedelta(days=30 - i * 3),
                last_seen   = now - timedelta(minutes=i * 7),
            )
            db.session.add(device)
            db.session.commit()  # commit first so device.id is assigned

            # Seed logs
            for j in range(5):
                log = DeviceLog(
                    device_id  = device.id,
                    event_type = "online" if j % 2 == 0 else "offline",
                    ip_address = d["ip"],
                    logged_at  = now - timedelta(hours=j * 6),
                )
                db.session.add(log)
            db.session.commit()  # commit logs separately

        # Seed unknown device alert
        db.session.add(Alert(
            alert_type = "unknown_device",
            severity   = "high",
            title      = "Unknown Device Detected: 192.168.1.99",
            message    = "An unrecognised device (DE:AD:BE:EF:CA:FE) joined the network.",
        ))
        db.session.add(Alert(
            alert_type = "new_device",
            severity   = "medium",
            title      = "New Device: iphone-14",
            message    = "A new mobile device joined from IP 192.168.1.25.",
        ))

        # Seed 7 days of statistics
        for i in range(7):
            db.session.add(Statistic(
                recorded_at     = now - timedelta(days=6 - i),
                total_devices   = 8,
                online_devices  = 5 + (i % 3),
                offline_devices = 3 - (i % 3),
                new_devices     = 1 if i == 3 else 0,
                total_alerts    = 2,
                bytes_sent      = 1024 * 1024 * (50 + i * 10),
                bytes_recv      = 1024 * 1024 * (200 + i * 30),
                packets_sent    = 50000 + i * 5000,
                packets_recv    = 200000 + i * 20000,
            ))

        db.session.commit()
        print("[SEED] Demo data inserted successfully.")


if __name__ == "__main__":
    if "--seed" in sys.argv:
        seed_demo_data()

    app.run(
        host  = "0.0.0.0",
        port  = int(os.environ.get("PORT", 5000)),
        debug = app.config.get("DEBUG", True),
    )
