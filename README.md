# AECC RADIUS & Network Management System

This repository contains the restructured, premium web portal and network authentication system for the **Asociación Estudiantil de Ciencias de Cómputos (AECC)** at the University of Puerto Rico, Río Piedras Campus (UPRRP).

The system integrates a modern public website, a self-service student MAC-address linking portal, and a high-fidelity administrative cockpit with standard FreeRADIUS and Pi-hole databases.

---

## Technical Stack & Architecture

- **Backend:** Python + Flask (Application Factory pattern, blueprints, session security).
- **Frontend:** HTML5 + Vanilla CSS (Custom dark-theme design system, glassmorphism, responsive flex/grid layouts, dynamic micro-animations) + Vanilla JavaScript (AJAX endpoints, Chart.js).
- **Databases:**
  - **RADIUS Database (`radius.db`):** Standard FreeRADIUS-compliant SQLite schema containing `radcheck`, `radreply`, `radusergroup`, `radpostauth`, and `radacct` tables. Direct integration ready for local FreeRADIUS servers.
  - **Pi-hole Database (`gravity.db`):** Interfaces with Pi-hole DNS group-based configurations to control routing access rules.
- **Integrations:** Google Sheets API validation for student organization registration.

---

## Directory Structure

```
AECC-2023-Radius-System/
├── run.py                          # Main launcher script
├── config.py                       # Application configuration variables
├── requirements.txt                # System Python dependencies
├── radius.db                       # Local SQLite RADIUS database (auto-generated)
├── gravity.db                      # Local SQLite Pi-hole database (auto-generated mock)
└── app/                            # Core application package
    ├── __init__.py                 # Flask factory & database initializers
    ├── models.py                   # Data Access Objects (DAO) for SQL queries
    ├── routes/                     # Blueprint routing layer
    │   ├── main.py                 # Public static web views (Home, FAQ, Store, etc.)
    │   ├── auth.py                 # Self-service MAC registration/detection wizard
    │   └── admin.py                # Administration control cockpit & REST APIs
    ├── services/                   # Business integration layer
    │   ├── google_sheets.py        # Student credentials sheets validator
    │   ├── pihole.py               # Pi-hole group access manager
    │   └── radius.py               # RADIUS logs & session simulators
    ├── static/                     # Assets & frontend styles
    │   ├── css/style.css           # Premium vanilla CSS design system
    │   ├── js/main.js              # Global dynamic behaviors
    │   ├── js/dashboard.js         # Cockpit interactive AJAX logic
    │   └── images/                 # Event photos & organization logos
    └── templates/                  # Reusable HTML5 templates
```

---

## Setup and Quick Start

### 1. Prerequisites

Make sure you have Python 3 installed. Install the required system packages:

```bash
pip install -r requirements.txt
```

### 2. Local Development / Simulation Mode

If you run the application without Google Sheets credentials or a running Pi-hole instance, the system will **automatically initialize in Local Simulation Mode**:
- Creates `radius.db` and a dummy `gravity.db` database inside the project root.
- Seeds them with initial test users, simulated RADIUS authentication logs, and session statistics.
- Validates logins with test student IDs: e.g., ID: `12345` / Phone: `555-5555` or ID: `802111222` / Phone: `7875551234`.

### 3. Launching the Portal

Start the Flask server:

```bash
python run.py
```

Open your browser and navigate to:
- **Public Portal & Registration:** [http://localhost:8080](http://localhost:8080)
- **Administrative Cockpit:** [http://localhost:8080/admin](http://localhost:8080/admin)
  - *Default Admin Credentials:* Username: `admin` | Password: `aecc2026`

---

## Production Configurations

For live deployments:
1. Place your Google Service Account credentials JSON file named `aecc-flask2023-f18201f75c25.json` in the root folder.
2. Edit `config.py` to point `PIHOLE_DB_PATH` to your live Pi-hole `gravity.db` file.
3. Configure your local FreeRADIUS `mods-enabled/sql` module to read from the generated sqlite database `radius.db`.
