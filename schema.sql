-- ============================================================
--  Smart Network Monitoring & Device Tracker
--  MySQL Database Schema
--  Author: Smart Network Monitor Project
--  Date: 2024
-- ============================================================

CREATE DATABASE IF NOT EXISTS smart_network_monitor
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE smart_network_monitor;

-- ============================================================
-- TABLE: users
-- Stores administrator credentials and profile information
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(80)  NOT NULL UNIQUE,
    email         VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    role          ENUM('admin','viewer') NOT NULL DEFAULT 'admin',
    is_active     TINYINT(1) NOT NULL DEFAULT 1,
    avatar        VARCHAR(255) DEFAULT NULL,
    last_login    DATETIME DEFAULT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email    (email)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: devices
-- Stores every unique network device ever seen
-- ============================================================
CREATE TABLE IF NOT EXISTS devices (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    ip_address    VARCHAR(45)  NOT NULL,
    mac_address   VARCHAR(17)  NOT NULL UNIQUE,
    hostname      VARCHAR(255) DEFAULT 'Unknown',
    vendor        VARCHAR(255) DEFAULT 'Unknown',
    device_type   ENUM('router','pc','mobile','iot','printer','unknown')
                    NOT NULL DEFAULT 'unknown',
    os_guess      VARCHAR(100) DEFAULT NULL,
    status        ENUM('online','offline') NOT NULL DEFAULT 'offline',
    is_trusted    TINYINT(1) NOT NULL DEFAULT 0,
    is_blocked    TINYINT(1) NOT NULL DEFAULT 0,
    category      VARCHAR(100) DEFAULT 'Uncategorized',
    notes         TEXT DEFAULT NULL,
    open_ports    TEXT DEFAULT NULL,       -- JSON array of open ports
    first_seen    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ip     (ip_address),
    INDEX idx_mac    (mac_address),
    INDEX idx_status (status),
    INDEX idx_trusted (is_trusted)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: device_logs
-- Immutable log of every online/offline event per device
-- ============================================================
CREATE TABLE IF NOT EXISTS device_logs (
    id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    device_id     INT UNSIGNED NOT NULL,
    event_type    ENUM('online','offline','scan','update') NOT NULL,
    ip_address    VARCHAR(45)  DEFAULT NULL,   -- IP at time of event
    details       TEXT DEFAULT NULL,
    logged_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id)
        REFERENCES devices(id) ON DELETE CASCADE,
    INDEX idx_device   (device_id),
    INDEX idx_logged   (logged_at),
    INDEX idx_event    (event_type)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: alerts
-- Suspicious device warnings and admin notifications
-- ============================================================
CREATE TABLE IF NOT EXISTS alerts (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    device_id     INT UNSIGNED DEFAULT NULL,
    alert_type    ENUM('unknown_device','port_scan','ip_conflict',
                       'blocked_device','high_traffic','new_device')
                    NOT NULL DEFAULT 'unknown_device',
    severity      ENUM('low','medium','high','critical')
                    NOT NULL DEFAULT 'medium',
    title         VARCHAR(255) NOT NULL,
    message       TEXT NOT NULL,
    is_read       TINYINT(1) NOT NULL DEFAULT 0,
    is_resolved   TINYINT(1) NOT NULL DEFAULT 0,
    resolved_by   INT UNSIGNED DEFAULT NULL,
    resolved_at   DATETIME DEFAULT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id)
        REFERENCES devices(id) ON DELETE SET NULL,
    FOREIGN KEY (resolved_by)
        REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_type      (alert_type),
    INDEX idx_severity  (severity),
    INDEX idx_read      (is_read),
    INDEX idx_created   (created_at)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: statistics
-- Hourly aggregated snapshot of network state
-- ============================================================
CREATE TABLE IF NOT EXISTS statistics (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    recorded_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_devices   INT UNSIGNED NOT NULL DEFAULT 0,
    online_devices  INT UNSIGNED NOT NULL DEFAULT 0,
    offline_devices INT UNSIGNED NOT NULL DEFAULT 0,
    new_devices     INT UNSIGNED NOT NULL DEFAULT 0,
    total_alerts    INT UNSIGNED NOT NULL DEFAULT 0,
    bytes_sent      BIGINT UNSIGNED DEFAULT 0,
    bytes_recv      BIGINT UNSIGNED DEFAULT 0,
    packets_sent    BIGINT UNSIGNED DEFAULT 0,
    packets_recv    BIGINT UNSIGNED DEFAULT 0,
    INDEX idx_recorded (recorded_at)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: whitelist
-- MAC addresses explicitly trusted by admin
-- ============================================================
CREATE TABLE IF NOT EXISTS whitelist (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    mac_address VARCHAR(17)  NOT NULL UNIQUE,
    label       VARCHAR(255) DEFAULT NULL,
    added_by    INT UNSIGNED DEFAULT NULL,
    added_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (added_by)
        REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_mac (mac_address)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: scan_sessions
-- Records each full network scan run
-- ============================================================
CREATE TABLE IF NOT EXISTS scan_sessions (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    network_range VARCHAR(50)  NOT NULL,
    devices_found INT UNSIGNED DEFAULT 0,
    new_devices   INT UNSIGNED DEFAULT 0,
    scan_type     ENUM('arp','nmap','ping') NOT NULL DEFAULT 'arp',
    duration_sec  FLOAT DEFAULT NULL,
    started_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at  DATETIME DEFAULT NULL,
    status        ENUM('running','completed','failed') DEFAULT 'running',
    INDEX idx_started (started_at)
) ENGINE=InnoDB;

-- ============================================================
-- Seed Data: Default admin user
-- Password: Admin@1234  (bcrypt hash)
-- ============================================================
INSERT INTO users (username, email, password_hash, role) VALUES (
  'admin',
  'admin@networkmonitor.local',
  'pbkdf2:sha256:600000$placeholder$hashed',
  'admin'
) ON DUPLICATE KEY UPDATE username=username;

-- ============================================================
-- Seed Data: Sample trusted devices (demo)
-- ============================================================
INSERT INTO whitelist (mac_address, label) VALUES
  ('00:00:00:00:00:01', 'Gateway/Router'),
  ('00:00:00:00:00:02', 'Admin PC')
ON DUPLICATE KEY UPDATE mac_address=mac_address;
