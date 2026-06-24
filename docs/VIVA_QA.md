# Viva Voce Preparation
## Smart Network Monitoring & Device Tracker

---

## PART A — Core Technical Questions

---

### Q1. What is the purpose of your project?
**Answer:**
The Smart Network Monitoring & Device Tracker is a web-based application that monitors all devices connected to a local network in real time. It discovers devices using ARP scanning, stores their information in a MySQL database, displays analytics on a dashboard, and alerts administrators about unknown or suspicious devices. The goal is to give network administrators complete visibility and control over their network.

---

### Q2. What technology stack did you use and why?
**Answer:**

| Layer | Technology | Reason |
|-------|-----------|--------|
| Backend | Python Flask | Lightweight, easy to extend, large ecosystem |
| Database | MySQL | Industry-standard RDBMS, strong data integrity |
| ORM | SQLAlchemy | Prevents SQL injection, simplifies queries |
| Scanning | Scapy | Python-native packet crafting, ARP scan support |
| Frontend | Bootstrap 5 | Responsive design, pre-built components |
| Charts | Chart.js | Free, highly customisable, browser-native |
| Auth | Flask-Login + Werkzeug | Proven, secure session and password management |

---

### Q3. What is ARP and how does your scanner use it?
**Answer:**
ARP stands for **Address Resolution Protocol** (RFC 826). It maps IP addresses to MAC (hardware) addresses on a local network. When a device wants to communicate with another IP on the same LAN, it broadcasts an ARP request: *"Who has IP 192.168.1.x? Tell me your MAC."* The target responds with its MAC address.

My scanner uses **Scapy** to:
1. Craft an ARP request packet (`ARP(pdst="192.168.1.0/24")`)
2. Wrap it in an Ethernet broadcast frame (`Ether(dst="ff:ff:ff:ff:ff:ff")`)
3. Send it to the network using `srp()` (send & receive at Layer 2)
4. Collect all replies and extract IP + MAC pairs

This discovers every device that responds on the subnet without requiring SNMP, agents, or credentials.

---

### Q4. What is the difference between MAC address and IP address?
**Answer:**
- **IP Address**: A logical, network-layer (Layer 3) address assigned by DHCP or configured manually. It can change over time (dynamic IP). Example: `192.168.1.100`
- **MAC Address**: A physical, data-link layer (Layer 2) address permanently assigned by the manufacturer, burned into the network card's ROM. It is globally unique (in theory) and doesn't change. Example: `AC:DE:48:AB:CD:EF`

My system uses the **MAC address as the primary unique key** for devices, because even if a device gets a new IP address from DHCP, it will be recognised as the same device by its MAC.

---

### Q5. How does your authentication system work?
**Answer:**
1. Admin submits username + password via the login form
2. Flask retrieves the User record from MySQL by username
3. **Werkzeug's `check_password_hash()`** compares the submitted password against the stored PBKDF2-SHA256 hash (600,000 iterations)
4. If valid, **Flask-Login** calls `login_user()`, which creates a signed session cookie
5. The session cookie is stored client-side but cannot be forged (signed with `SECRET_KEY`)
6. Every protected route uses the `@login_required` decorator — Flask-Login checks the session before allowing access
7. Passwords are **never stored in plain text** — only the hash is saved

---

### Q6. What is an ORM? Why use SQLAlchemy instead of raw SQL?
**Answer:**
ORM stands for **Object-Relational Mapper**. It translates Python objects to database rows and vice versa, so you write Python code instead of SQL strings.

**Benefits of SQLAlchemy over raw SQL:**
1. **SQL Injection Prevention** — Parameters are always escaped; user input never directly interpolated into queries
2. **Database Agnostic** — Switching from MySQL to PostgreSQL only requires changing the connection string
3. **Pythonic** — `Device.query.filter_by(status="online").all()` is readable and maintainable
4. **Relationship Management** — Lazy loading, cascade deletes, and join queries are handled automatically
5. **Migration Support** — Flask-Migrate creates schema change scripts automatically

---

### Q7. Explain the Flask Application Factory Pattern.
**Answer:**
Instead of creating the Flask `app` object at module level (which makes testing hard), the **factory pattern** wraps creation in a function: `create_app(config_name)`.

Benefits:
- **Testability**: Each test can create a fresh app with test config (test database)
- **Multiple configurations**: Same codebase runs in development (DEBUG=True) or production (DEBUG=False, HTTPS)
- **Circular import prevention**: Extensions (`db`, `login_manager`) are initialised without `app`, then attached via `init_app(app)` inside the factory
- **Blueprint registration**: Each module (auth, devices, monitor…) is a separate Blueprint, registered inside the factory

---

### Q8. What is a Flask Blueprint?
**Answer:**
A Blueprint is a way to organise a Flask application into modular components. Each Blueprint has its own routes, templates folder, and static files. You register blueprints with a URL prefix on the main app.

In my project:
- `auth_bp` → `/auth/login`, `/auth/logout`
- `monitor_bp` → `/monitor/scan`, `/monitor/api/status`
- `devices_bp` → `/devices/`, `/devices/<id>`
- `alerts_bp` → `/alerts/`, `/alerts/<id>/resolve`
- `dashboard_bp` → `/`
- `reports_bp` → `/reports/csv`, `/reports/pdf`

This follows **Separation of Concerns** — each feature is independently developed and tested.

---

### Q9. How does your alert system detect unknown devices?
**Answer:**
When the scanner processes results:
1. It queries the `whitelist` table for all trusted MAC addresses
2. For each newly discovered device (MAC not in `devices` table), it checks if the MAC is in the whitelist
3. If **not whitelisted**, `is_trusted = False` and an **Alert** record is created with `alert_type = 'new_device'`, `severity = 'high'`
4. The alert is immediately visible in the Alert Centre
5. The navbar badge counter updates every 30 seconds via AJAX

---

### Q10. What is Chart.js and how do you use it?
**Answer:**
Chart.js is an open-source JavaScript library that renders interactive charts in an HTML5 `<canvas>` element.

In my dashboard:
1. Python route `/api/chart-data` queries the `statistics` table and returns JSON
2. `dashboard.js` calls this API using `fetch()`
3. Four charts are created:
   - **Line chart**: online/offline device counts over 7 days
   - **Doughnut chart**: device type distribution
   - **Doughnut chart**: alert severity breakdown
   - **Bar chart**: network traffic (MB sent/received per day)
4. All charts use a custom dark colour palette matching the UI

---

## PART B — Database Questions

---

### Q11. How many tables does your database have? Describe each.
**Answer:**
7 tables:

| Table | Purpose |
|-------|---------|
| `users` | Admin accounts with hashed passwords |
| `devices` | Every unique device discovered (MAC as unique key) |
| `device_logs` | Immutable event log (online/offline transitions) |
| `alerts` | Security warnings for admin |
| `statistics` | Hourly aggregated metrics for charts |
| `whitelist` | Admin-approved trusted MAC addresses |
| `scan_sessions` | Metadata for each network scan run |

---

### Q12. What is database normalisation? Which normal form is your DB in?
**Answer:**
Normalisation is the process of organising a database to reduce data redundancy and improve integrity.

My database is in **3rd Normal Form (3NF)**:
- **1NF**: All columns have atomic values, no repeating groups
- **2NF**: No partial dependencies on composite keys (single-column PKs)
- **3NF**: No transitive dependencies — e.g., `vendor` is stored in `devices`, not derived from `mac_address` via a separate lookup table at query time

I chose NOT to normalise vendor into a separate table because vendor lookup is done at scan time (from the prefix dictionary) and stored for performance.

---

### Q13. Why do you use MAC address as the unique key for devices, not IP?
**Answer:**
IP addresses are **dynamic** — DHCP assigns them and they can change. The same laptop could have `192.168.1.100` today and `192.168.1.145` tomorrow. If we used IP as the primary identifier, we would create duplicate records.

MAC addresses are **burned into the hardware** and don't change (under normal circumstances). Using `mac_address` as a `UNIQUE` constraint ensures one record per physical device, regardless of how many times its IP changes.

When a scan detects a known MAC at a new IP, we **update** `ip_address` on the existing device record instead of creating a new one.

---

## PART C — Security & Networking Questions

---

### Q14. What security vulnerabilities did you address?
**Answer:**

| Vulnerability | Mitigation |
|---------------|-----------|
| SQL Injection | SQLAlchemy ORM — parameterised queries, never string interpolation |
| XSS (Cross-Site Scripting) | Jinja2 auto-escaping — `{{ user_input }}` is always HTML-escaped |
| Password theft | PBKDF2-SHA256 with 600K iterations — rainbow tables impractical |
| Session hijacking | HTTPOnly + SameSite cookies, SECRET_KEY signed sessions |
| Unauthorised access | `@login_required` decorator on every protected route |

---

### Q15. What is a DFD? Describe your system's DFD.
**Answer:**
A **Data Flow Diagram** shows how data moves through a system between processes, data stores, and external entities.

**DFD Level 0 (Context Diagram):**
```
[Network Devices] → (ARP Scan) → [Smart Network Monitor System] → [Admin Browser]
[Admin Browser] → (Login/Commands) → [Smart Network Monitor System]
[Smart Network Monitor System] ↔ [MySQL Database]
```

**DFD Level 1** decomposes into processes:
1. Authentication Process → reads/writes `users` store
2. Network Scanning Process → reads network, writes `devices`, `device_logs`, `scan_sessions`
3. Alert Generation Process → reads `whitelist`, writes `alerts`
4. Dashboard Process → reads `statistics`, `devices`, `alerts`
5. Report Generation Process → reads all stores, outputs files

---

### Q16. What is the difference between GET and POST in your application?
**Answer:**

| HTTP Method | Use in my app |
|------------|---------------|
| GET | Read data: list devices, view dashboard, download reports |
| POST | Write/modify data: login, trigger scan, update device, block device |

POST is used for all state-changing operations because:
1. POST data is in the request body, not visible in browser history/bookmarks
2. Browsers warn before re-submitting POST requests (prevents accidental double-submit)
3. Follows REST principles (safe vs unsafe methods)

---

## PART D — Project Management & Design

---

### Q17. What challenges did you face and how did you solve them?
**Answer:**

**Challenge 1: ARP scan requires root privileges**
- Solution: Implemented a 3-tier fallback strategy — Scapy (root) → ARP cache parsing (no root) → Mock data (demo mode). The application works at all privilege levels.

**Challenge 2: MAC vendor lookup without internet**
- Solution: Bundled a dictionary of the top 30 MAC OUI prefixes directly in `scanner.py`. No API call required.

**Challenge 3: Real-time updates without WebSockets**
- Solution: JavaScript `setInterval()` + AJAX `fetch()` to `/monitor/api/status` every 30 seconds, updating the DOM without page reload.

**Challenge 4: Charts with no historical data on first launch**
- Solution: The `seed_demo_data()` function in `run.py --seed` inserts 7 days of `statistics` rows, making charts look populated immediately.

---

### Q18. How would you deploy this to production?
**Answer:**

**Production deployment steps:**
1. **Server**: Ubuntu 22.04 LTS on a local server or cloud VM
2. **WSGI Server**: Replace Flask dev server with Gunicorn: `gunicorn -w 4 run:app`
3. **Reverse Proxy**: Nginx to handle HTTPS, static files, and proxy to Gunicorn
4. **SSL Certificate**: Let's Encrypt (Certbot) for HTTPS
5. **Environment**: Set `FLASK_ENV=production`, strong `SECRET_KEY`, restricted DB user
6. **Process Manager**: Systemd service to auto-restart on crash
7. **Database**: MySQL with dedicated `netmonitor` user, minimal privileges

---

### Q19. What design pattern does your project follow?
**Answer:**
The project follows the **MVC (Model-View-Controller)** architectural pattern:

- **Model** (`app/models.py`): SQLAlchemy ORM classes (User, Device, Alert, etc.) — represent data and business logic
- **View** (`app/templates/`): Jinja2 HTML templates — present data to the user
- **Controller** (`app/*/routes.py`): Flask Blueprint routes — handle requests, call models, render views

Additionally, the project uses:
- **Application Factory** pattern (`create_app()`)
- **Blueprint** pattern for module separation
- **Strategy** pattern in the scanner (3 scanning strategies with automatic fallback)

---

### Q20. What improvements would you make if you had more time?
**Answer:**

1. **Email Alerts**: Send email notifications via SMTP when critical alerts are triggered (unknown device detected)
2. **Login Rate Limiting**: Use Flask-Limiter to prevent brute force attacks (e.g., max 5 attempts per minute)
3. **WebSockets**: Replace polling with Flask-SocketIO for true real-time push notifications
4. **OS Detection**: Use Scapy TTL analysis or nmap to guess device operating systems
5. **Port Scanning**: Integrate python-nmap to detect open services on discovered devices
6. **Docker**: Package the entire application as a docker-compose stack (Flask + MySQL + Nginx)
7. **REST API**: Add JWT-authenticated REST endpoints for integration with other tools
8. **Network Topology Map**: Visual graph showing device connections using D3.js or vis.js

---

## PART E — Quick-Fire Round

| Question | Answer |
|----------|--------|
| What port does Flask run on by default? | **5000** |
| What does ORM stand for? | **Object-Relational Mapper** |
| What hashing algorithm stores passwords? | **PBKDF2-SHA256** (Werkzeug) |
| What does ARP stand for? | **Address Resolution Protocol** |
| What layer is ARP at in OSI model? | **Layer 2 (Data Link)** |
| What does MAC stand for? | **Media Access Control** |
| What is a /24 network? | **256 addresses (x.x.x.0 to x.x.x.255)** |
| What HTTP method is used for login? | **POST** |
| What does CSRF stand for? | **Cross-Site Request Forgery** |
| What does XSS stand for? | **Cross-Site Scripting** |
| What is a Flask Blueprint? | **A modular component for organising routes** |
| What does `@login_required` do? | **Redirects to login if user not authenticated** |
| What is SQLAlchemy? | **Python ORM for database interaction** |
| What is Jinja2? | **Flask's HTML templating engine** |
| What tool exports PDF reports? | **ReportLab** |
| What does PBKDF2 stand for? | **Password-Based Key Derivation Function 2** |
| What is Bootstrap 5 used for? | **Responsive CSS/HTML frontend framework** |
| What is Scapy? | **Python packet manipulation library** |

---

## Presentation Slides Outline (10 slides)

1. **Title Slide** — Project name, student name, institution, date
2. **Problem Statement** — Network visibility gap, unknown devices, no audit trail
3. **Project Overview** — What it is, one-paragraph description, key features
4. **System Architecture** — Block diagram (browser → Flask → MySQL → network)
5. **Database Design** — ER diagram with 7 tables
6. **Key Features** — Bullet list with icons: scan, monitor, alert, report
7. **Dashboard Screenshot** — Charts, stat cards (annotated)
8. **Device Management Screenshot** — Table, search, detail view
9. **Technology Stack** — Logos/table: Python, Flask, MySQL, Bootstrap, Chart.js
10. **Conclusion & Future Work** — What was achieved, what can be improved

---

*Good luck with your Viva! Remember: speak confidently, refer to your own code, and admit if you don't know something — then explain what you would do to find out.*
