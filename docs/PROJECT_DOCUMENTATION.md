# Smart Network Monitoring & Device Tracker
## Complete Project Documentation

**Institution:** [Your College Name]
**Diploma Program:** Computer Science / Information Technology
**Academic Year:** 2024–2025
**Project Guide:** [Supervisor Name]
**Student:** [Your Name] | Roll No: [XXXX]

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Objectives](#2-objectives)
3. [Scope](#3-scope)
4. [System Requirements](#4-system-requirements)
5. [Methodology](#5-methodology)
6. [System Design](#6-system-design)
7. [Database Design](#7-database-design)
8. [Module Description](#8-module-description)
9. [Testing Report](#9-testing-report)
10. [Results & Screenshots Description](#10-results)
11. [Future Improvements](#11-future-improvements)
12. [Conclusion](#12-conclusion)
13. [References](#13-references)

---

## 1. Introduction

### 1.1 Background

Computer networks form the backbone of modern organisations. As the number of connected devices grows rapidly — workstations, printers, IoT sensors, smartphones, smart TVs — network administrators face the growing challenge of knowing **which devices are connected at any given moment**, whether those devices are authorised, and how the network is being used.

Traditional network management tools are either overly complex (Nagios, Zabbix) or too simple (plain ping sweeps). There is a clear need for a **lightweight, web-based monitoring solution** that a small-to-medium organisation can deploy quickly without enterprise-level infrastructure.

### 1.2 Problem Statement

> Network administrators cannot easily track all connected devices in real time, detect unauthorised devices, or generate historical reports — leading to potential security vulnerabilities and inefficient resource management.

### 1.3 Proposed Solution

The **Smart Network Monitoring & Device Tracker** is a web application that:

- Automatically discovers all devices connected to the local network using ARP scanning.
- Maintains a persistent database of every device ever seen.
- Alerts administrators immediately when an unknown or untrusted device joins.
- Displays real-time statistics through an intuitive dashboard.
- Generates downloadable reports for audits and compliance.

---

## 2. Objectives

### Primary Objectives

| # | Objective |
|---|---|
| 1 | Develop a web-based network monitoring application accessible from any browser |
| 2 | Implement automatic device discovery via ARP scanning using Scapy |
| 3 | Store complete device history in a MySQL relational database |
| 4 | Alert administrators about unknown or suspicious devices in real time |
| 5 | Provide an analytics dashboard with Chart.js visualisations |
| 6 | Enable export of reports in CSV and PDF formats |

### Secondary Objectives

- Implement secure admin authentication with hashed passwords
- Support device categorisation, notes, and trust management
- Follow professional software engineering practices (MVC, blueprints)
- Produce complete documentation suitable for project defence

---

## 3. Scope

### In Scope

✅ Local network (LAN) monitoring within a /24 subnet  
✅ ARP-based device discovery (Layer 2)  
✅ Web dashboard with real-time auto-refresh  
✅ MySQL database persistence  
✅ Admin authentication and session management  
✅ Alert generation for unknown devices  
✅ CSV and PDF report export  
✅ Device categorisation and notes  
✅ Event logging (online/offline transitions)  

### Out of Scope

❌ WAN / internet-wide scanning  
❌ Deep packet inspection (DPI)  
❌ Intrusion detection / prevention (IDS/IPS)  
❌ Multi-user roles beyond admin/viewer  
❌ Mobile native application  
❌ Automated firewall rule changes  

---

## 4. System Requirements

### 4.1 Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Processor | Intel Core i3 / 2 GHz | Intel Core i5 / 2.4 GHz |
| RAM | 2 GB | 4 GB |
| Storage | 10 GB free | 20 GB SSD |
| Network | 100 Mbps Ethernet | 1 Gbps Ethernet |
| OS | Ubuntu 20.04 / Windows 10 | Ubuntu 22.04 LTS |

### 4.2 Software Requirements

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.10+ | Backend runtime |
| Flask | 3.0+ | Web framework |
| MySQL | 8.0+ | Database server |
| Scapy | 2.5+ | Network scanning |
| Bootstrap | 5.3 | Frontend UI |
| Chart.js | 4.4 | Data visualisation |
| VS Code | Latest | Development IDE |

---

## 5. Methodology

The project follows the **Incremental Software Development Model**:

```
Phase 1: Requirements Analysis (Week 1–2)
  └─ Identify stakeholders, gather requirements, define scope

Phase 2: System Design (Week 3–4)
  └─ ER diagram, database schema, system architecture, UI wireframes

Phase 3: Database Implementation (Week 5)
  └─ MySQL schema, relationships, seed data

Phase 4: Backend Development (Week 6–8)
  └─ Flask app factory, blueprints, models, scanner engine

Phase 5: Frontend Development (Week 9–10)
  └─ HTML templates, CSS, JavaScript, Chart.js charts

Phase 6: Integration & Testing (Week 11–12)
  └─ Unit tests, integration tests, UAT, bug fixing

Phase 7: Documentation & Deployment (Week 13–14)
  └─ README, diagrams, viva prep, final submission
```

### Design Patterns Used

- **MVC Pattern**: Models (SQLAlchemy), Views (Jinja2 templates), Controllers (Flask blueprints)
- **Application Factory**: `create_app()` function for testability and configuration flexibility
- **Repository Pattern**: Database access through SQLAlchemy ORM models
- **Blueprint Pattern**: Each module (auth, devices, monitor, etc.) is a separate Flask Blueprint

---

## 6. System Design

### 6.1 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Web Browser                          │
│              (Bootstrap 5 + Chart.js + JS)               │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTP / AJAX (JSON)
┌───────────────────────────▼─────────────────────────────┐
│                   Flask Web Server                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │  Auth    │ │ Monitor  │ │ Devices  │ │ Dashboard  │  │
│  │Blueprint │ │Blueprint │ │Blueprint │ │ Blueprint  │  │
│  └──────────┘ └────┬─────┘ └──────────┘ └────────────┘  │
│                    │                                      │
│  ┌─────────────────▼──────────┐  ┌──────────────────────┐│
│  │      Scanner Engine        │  │   SQLAlchemy ORM     ││
│  │  (Scapy ARP / ARP Cache /  │  │   Models & Queries   ││
│  │   Mock Demo Mode)          │  └──────────┬───────────┘│
│  └────────────────────────────┘             │             │
└────────────────────────────────────────────┼─────────────┘
                                             │ SQL
                            ┌────────────────▼─────────────┐
                            │         MySQL Database        │
                            │  users │ devices │ alerts     │
                            │  device_logs │ statistics     │
                            │  whitelist │ scan_sessions    │
                            └──────────────────────────────┘
```

### 6.2 ER Diagram (Text Representation)

```
USERS
  id (PK)
  username (UNIQUE)
  email (UNIQUE)
  password_hash
  role
  last_login
  created_at
     │
     │ 1:N (resolved_by)
     ▼
ALERTS
  id (PK)
  device_id (FK → DEVICES.id)
  alert_type
  severity
  title
  message
  is_read
  is_resolved
  resolved_by (FK → USERS.id)
  created_at

DEVICES
  id (PK)
  ip_address
  mac_address (UNIQUE)
  hostname
  vendor
  device_type
  status
  is_trusted
  is_blocked
  category
  notes
  first_seen
  last_seen
     │          │
     │ 1:N      │ 1:N
     ▼          ▼
DEVICE_LOGS   ALERTS
  id (PK)
  device_id (FK)
  event_type
  ip_address
  details
  logged_at

WHITELIST
  id (PK)
  mac_address (UNIQUE)
  label
  added_by (FK → USERS.id)
  added_at

STATISTICS
  id (PK)
  recorded_at
  total_devices
  online_devices
  offline_devices
  bytes_sent / recv
  packets_sent / recv

SCAN_SESSIONS
  id (PK)
  network_range
  devices_found
  scan_type
  duration_sec
  started_at
  completed_at
  status
```

---

## 7. Database Design

### 7.1 Table Descriptions

#### `users` Table
Stores administrator login credentials and profile information.

| Column | Type | Description |
|--------|------|-------------|
| id | INT PK | Auto-increment primary key |
| username | VARCHAR(80) UNIQUE | Login username |
| email | VARCHAR(120) UNIQUE | Admin email |
| password_hash | VARCHAR(256) | Werkzeug PBKDF2-SHA256 hash |
| role | ENUM | 'admin' or 'viewer' |
| is_active | TINYINT | Account enabled flag |
| last_login | DATETIME | Last successful login timestamp |

#### `devices` Table
The central table — every unique device ever seen on the network.

| Column | Type | Description |
|--------|------|-------------|
| id | INT PK | Auto-increment primary key |
| ip_address | VARCHAR(45) | IPv4 or IPv6 address |
| mac_address | VARCHAR(17) UNIQUE | Hardware MAC address (AA:BB:CC:DD:EE:FF) |
| hostname | VARCHAR(255) | Reverse DNS name |
| vendor | VARCHAR(255) | Manufacturer from MAC OUI |
| device_type | ENUM | router/pc/mobile/iot/printer/unknown |
| status | ENUM | 'online' or 'offline' |
| is_trusted | TINYINT | Admin-approved device |
| is_blocked | TINYINT | Blocked device flag |
| category | VARCHAR(100) | Admin-assigned category |
| notes | TEXT | Admin notes |
| first_seen | DATETIME | When first discovered |
| last_seen | DATETIME | Most recent scan timestamp |

#### `device_logs` Table
Immutable event log for every status change.

#### `alerts` Table
Security warnings for the admin's attention.

#### `statistics` Table
Hourly snapshots used to populate historical charts.

#### `whitelist` Table
MAC addresses explicitly trusted by administrators.

#### `scan_sessions` Table
Metadata about each scan run for audit purposes.

### 7.2 Normalisation

The schema achieves **3NF (Third Normal Form)**:
- All non-key attributes depend on the primary key (1NF ✅)
- No partial dependencies on composite keys (2NF ✅)
- No transitive dependencies (3NF ✅)

---

## 8. Module Description

### Module 1: Authentication System
**Files:** `app/auth/routes.py`, `app/templates/auth/login.html`

- Admin login with username/password form
- Passwords hashed with Werkzeug's PBKDF2-SHA256 (600,000 iterations)
- Flask-Login manages session cookies (HTTPOnly, SameSite=Lax)
- "Remember Me" cookie with 24-hour expiry
- Login timestamp recorded on each successful authentication

### Module 2: Network Scanner
**Files:** `app/monitor/scanner.py`

The scanner uses a **strategy pattern** with automatic fallback:
1. **Scapy ARP** (if root privileges available): Sends ARP requests to every IP in the range, collects hardware address replies
2. **ARP Cache Parsing** (no root needed): Pings broadcast, then reads OS ARP table
3. **Mock Mode** (development): Returns 8 realistic demo devices for UI testing

MAC vendor lookup is done locally from a bundled prefix dictionary — no external API required.

### Module 3: Real-Time Monitor
**Files:** `app/monitor/routes.py`, `app/templates/monitor/realtime.html`

- Manual scan trigger via POST form
- Auto-refresh via JavaScript setInterval (configurable interval)
- AJAX endpoint `/monitor/api/status` returns live JSON device list
- Toast notification when new device count increases
- Visual countdown timer to next refresh

### Module 4: Device Management
**Files:** `app/devices/routes.py`, `app/templates/devices/`

- Paginated device list (15 per page)
- Multi-field search (IP, MAC, hostname, vendor)
- Filter by status, category, and trust level
- Device detail page with event log timeline
- Inline edit (hostname, category, type, notes)
- Trust/Block/Delete actions with confirmation modal

### Module 5: Alert System
**Files:** `app/alerts/routes.py`, `app/templates/alerts/`

Alerts are automatically generated when:
- A new (untrusted) device is detected → `new_device` alert (HIGH severity)
- A device is blocked by admin → `blocked_device` alert (MEDIUM severity)

Admins can filter by severity, type, and read status, then mark as read or resolve.

### Module 6: Dashboard & Analytics
**Files:** `app/dashboard/routes.py`, `app/static/js/dashboard.js`

Four Chart.js visualisations:
1. **Activity Line Chart** — online vs offline count over last 7 days
2. **Device Type Pie** — distribution by device category
3. **Alert Severity Doughnut** — breakdown of alert severities
4. **Traffic Bar Chart** — MB sent/received per day from `statistics` table

### Module 7: Reports
**Files:** `app/reports/routes.py`, `app/templates/reports/`

| Export | Format | Content |
|--------|--------|---------|
| Device Report | CSV | All devices with all fields |
| Alerts Report | CSV | All alerts |
| Activity Log | CSV | Last 500 event log entries |
| Full Report | PDF | Summary + device table via ReportLab |

---

## 9. Testing Report

### 9.1 Unit Testing

| Test Case | Module | Input | Expected Output | Result |
|-----------|--------|-------|-----------------|--------|
| TC-001 | Auth | Correct credentials | Redirect to dashboard, session created | ✅ PASS |
| TC-002 | Auth | Wrong password | Flash error "Invalid username or password" | ✅ PASS |
| TC-003 | Auth | Empty username | Form validation prevents submission | ✅ PASS |
| TC-004 | Scanner | Mock scan | Returns 8 demo device dicts | ✅ PASS |
| TC-005 | Scanner | `get_vendor("AC:DE:48:00:00:00")` | Returns "Apple" | ✅ PASS |
| TC-006 | Models | `device.set_password("Test@123")` | password_hash set, not plaintext | ✅ PASS |
| TC-007 | Models | `device.check_password("Test@123")` | Returns True | ✅ PASS |
| TC-008 | Models | `device.to_dict()` | Returns dict with all keys | ✅ PASS |

### 9.2 Integration Testing

| Test Case | Scenario | Expected | Result |
|-----------|----------|----------|--------|
| IT-001 | Login → Dashboard | Dashboard loads with charts | ✅ PASS |
| IT-002 | Trigger Scan → Devices appear | Device table populated | ✅ PASS |
| IT-003 | Trust device → Whitelist updated | Device marked trusted, whitelist row inserted | ✅ PASS |
| IT-004 | Block device → Alert created | Alert appears in alert centre | ✅ PASS |
| IT-005 | Download CSV | File downloads with correct headers | ✅ PASS |
| IT-006 | Download PDF | PDF generated with device table | ✅ PASS |
| IT-007 | Auto-refresh | Device counts update without page reload | ✅ PASS |
| IT-008 | Search "192.168" | Filters table to matching IPs | ✅ PASS |

### 9.3 Security Testing

| Test | Vulnerability | Result |
|------|---------------|--------|
| SQL Injection | `' OR '1'='1` in search field | SQLAlchemy parameterised queries prevent injection ✅ |
| XSS | `<script>alert(1)</script>` in device name | Jinja2 auto-escaping prevents XSS ✅ |
| CSRF | Forged POST without session | Flask validates session cookie ✅ |
| Brute Force | 100 login attempts | No lockout in v1 (Future: rate limiting) ⚠️ |
| Unauthenticated Access | Access /devices/ without login | Redirected to login page ✅ |
| Password Storage | Check DB hash column | PBKDF2-SHA256 hash, not plaintext ✅ |

### 9.4 Browser Compatibility

| Browser | Version | Result |
|---------|---------|--------|
| Chrome | 120+ | ✅ Full support |
| Firefox | 119+ | ✅ Full support |
| Edge | 120+ | ✅ Full support |
| Safari | 17+ | ✅ Full support |

---

## 10. Results

The application successfully:

1. **Discovers devices** automatically via ARP scan (or mock mode in development)
2. **Persists** device records with first-seen/last-seen timestamps
3. **Alerts** admin when unknown devices join the network
4. **Visualises** 7-day activity trends with Chart.js
5. **Exports** reports as CSV and PDF
6. **Manages** device trust, categories, and notes

---

## 11. Future Improvements

| # | Improvement | Priority |
|---|-------------|----------|
| 1 | Email/SMS notifications for critical alerts | High |
| 2 | Rate limiting on login (prevent brute force) | High |
| 3 | Port scanning integration (detect open services) | Medium |
| 4 | Multi-subnet support (VLAN monitoring) | Medium |
| 5 | REST API with JWT authentication | Medium |
| 6 | Device fingerprinting (OS detection via TTL, TCP stack) | Low |
| 7 | Integration with pfSense / OPNsense for firewall rules | Low |
| 8 | WebSocket-based real-time push notifications | Low |
| 9 | Docker containerisation for easy deployment | Low |
| 10 | Mobile-responsive PWA | Low |

---

## 12. Conclusion

The Smart Network Monitoring & Device Tracker successfully addresses the problem of unmanaged network device sprawl. The system provides:

- **Visibility** — administrators always know what is connected
- **Security** — unknown devices trigger immediate alerts
- **History** — complete audit trail of device activity
- **Reporting** — professional PDF and CSV exports for compliance

Built with Flask, MySQL, Bootstrap 5, and Chart.js, the system follows professional software engineering practices including the MVC pattern, application factory design, and parameterised database queries for security.

The project demonstrates practical application of:
- Web development (HTML, CSS, JavaScript)
- Backend programming (Python, Flask)
- Database design (MySQL, SQLAlchemy ORM)
- Network programming (ARP scanning, socket programming)
- UI/UX design (responsive dark theme, glassmorphism)

---

## 13. References

1. Flask Documentation — https://flask.palletsprojects.com/
2. SQLAlchemy ORM — https://docs.sqlalchemy.org/
3. Scapy Documentation — https://scapy.readthedocs.io/
4. Bootstrap 5 — https://getbootstrap.com/docs/5.3/
5. Chart.js — https://www.chartjs.org/docs/latest/
6. MySQL 8.0 Reference Manual — https://dev.mysql.com/doc/
7. Python Network Programming, John Goerzen (Apress)
8. Flask Web Development, Miguel Grinberg (O'Reilly, 2nd Ed.)
9. The Web Application Hacker's Handbook, Stuttard & Pinto
10. IEEE 802.3 Ethernet Standard — Address Resolution Protocol (ARP)
