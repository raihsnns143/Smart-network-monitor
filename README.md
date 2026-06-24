# Smart Network Monitoring & Device Tracker

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/flask-3.0-green)
![MySQL](https://img.shields.io/badge/mysql-8.0-orange)

A complete, production-ready final-year diploma project: a web-based application that monitors devices on a local network, tracks status, stores data in MySQL, displays analytics via a dashboard, and alerts admins about suspicious devices.

## Features
- **Real-Time Device Discovery:** Scans the network using Scapy (ARP) with fallbacks.
- **Device Management:** View, search, filter, edit, trust, block, and categorize devices.
- **Alert System:** Automated alerts when unknown devices join or a device is blocked.
- **Dashboard Analytics:** Visualizations using Chart.js for device status, types, alerts, and network traffic.
- **Reporting:** Export devices, alerts, and logs in CSV format, or download a full PDF summary.
- **Authentication:** Secure admin login with hashed passwords.

## Setup Instructions

### 1. Prerequisites
- Python 3.10+
- MySQL Server 8.0+

### 2. Database Setup
1. Log in to your MySQL server as root:
   ```bash
   mysql -u root -p
   ```
2. Execute the schema file to create the database, tables, and default admin user:
   ```sql
   source schema.sql;
   ```
   *Note: The default admin user is created with username `admin` and password `Admin@1234`.*

### 3. Application Setup
1. Clone the repository and navigate to the project directory:
   ```bash
   cd smart_network_monitor
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the environment variables template and configure it:
   ```bash
   cp .env.example .env
   ```
   *Edit `.env` to match your MySQL credentials and network configuration.*

### 4. Running the Application

For a full demonstration with dummy data (useful if you don't have network scanning privileges):
```bash
python run.py --seed
```

For standard operation:
```bash
python run.py
```

The application will be available at `http://localhost:5000`.

**Default Login:**
- **Username:** admin
- **Password:** Admin@1234

## Folder Structure Explanation

- **`app/`**: Core application folder following the Flask Application Factory and Blueprint patterns.
  - **`__init__.py`**: Flask app factory, initializes extensions and registers blueprints.
  - **`config.py`**: Configuration settings loaded from the environment.
  - **`models.py`**: SQLAlchemy ORM classes mapping to the MySQL database tables.
  - **`auth/`, `devices/`, `monitor/`, `alerts/`, `dashboard/`, `reports/`**: Flask Blueprints for different modules, each containing a `routes.py`.
  - **`monitor/scanner.py`**: The network scanning engine with Scapy, ARP-cache fallback, and a mock mode.
  - **`static/`**: Static assets including custom CSS (`css/style.css`), JavaScript (`js/dashboard.js`), and images.
  - **`templates/`**: Jinja2 HTML templates, organized by blueprint, with a master `base.html`.
- **`docs/`**: Project documentation, including the main report (`PROJECT_DOCUMENTATION.md`) and Viva Q&A (`VIVA_QA.md`).
- **`schema.sql`**: The complete MySQL database schema for setting up the database.
- **`requirements.txt`**: Python dependencies.
- **`run.py`**: The application entry point and demo data seeder.

## Deployment

For production deployment, it is recommended to use:
- **Gunicorn** as the WSGI server.
- **Nginx** as a reverse proxy.
- **Systemd** to manage the Gunicorn service.
- Let's Encrypt for SSL certificates.

Example Gunicorn command:
```bash
gunicorn -w 4 run:app
```

## License
This project is licensed under the MIT License.
# Smart-network-monitor
# Smart-network-monitor
# Smart-network-monitor
# Smart-network-monitor
# Smart-network-monitor
