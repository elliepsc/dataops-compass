"""
Initialize Grafana datasource and dashboard.
Run after docker-compose is up:
  python grafana/init.py
"""

import os
import json
import time
import requests

GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
GRAFANA_USER = os.getenv("GRAFANA_ADMIN_USER", "admin")
GRAFANA_PASSWORD = os.getenv("GRAFANA_ADMIN_PASSWORD", "admin")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "dataops_assistant")
POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "adminpassword")


def wait_for_grafana():
    print("Waiting for Grafana...")
    for _ in range(30):
        try:
            r = requests.get(f"{GRAFANA_URL}/api/health", timeout=3)
            if r.status_code == 200:
                print("Grafana is ready.")
                return
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError("Grafana did not start in time.")


def create_datasource():
    datasource = {
        "name": "PostgreSQL",
        "type": "postgres",
        "url": f"{POSTGRES_HOST}:5432",
        "database": POSTGRES_DB,
        "user": POSTGRES_USER,
        "secureJsonData": {"password": POSTGRES_PASSWORD},
        "jsonData": {
            "sslmode": "disable",
            "postgresVersion": 1300,
        },
        "access": "proxy",
        "isDefault": True,
    }

    r = requests.post(
        f"{GRAFANA_URL}/api/datasources",
        auth=(GRAFANA_USER, GRAFANA_PASSWORD),
        json=datasource,
    )

    if r.status_code in (200, 409):
        print(f"Datasource ready: {r.json().get('message', 'ok')}")
    else:
        print(f"Datasource error: {r.status_code} {r.text}")


def create_dashboard():
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.json")
    if not os.path.exists(dashboard_path):
        print("dashboard.json not found, skipping.")
        return

    with open(dashboard_path) as f:
        dashboard = json.load(f)

    payload = {
        "dashboard": dashboard,
        "overwrite": True,
        "folderId": 0,
    }

    r = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        auth=(GRAFANA_USER, GRAFANA_PASSWORD),
        json=payload,
    )

    if r.status_code == 200:
        print(f"Dashboard created: {r.json().get('url')}")
    else:
        print(f"Dashboard error: {r.status_code} {r.text}")


if __name__ == "__main__":
    wait_for_grafana()
    create_datasource()
    create_dashboard()
    print("Grafana initialization complete.")
