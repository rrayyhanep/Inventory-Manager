# database.py
import os
import json

DB_DIR = os.path.dirname(os.path.abspath(__file__))
INV_COUNTER_FILE = os.path.join(DB_DIR, ".inv_ctr")
INVENTORY_FILE = os.path.join(DB_DIR, "inventory_data.json")
COMPANY_FILE = os.path.join(DB_DIR, "company_data.json")
CLIENTS_FILE = os.path.join(DB_DIR, "clients_data.json")

# Set to empty defaults
DEFAULT_CATALOG = {}

DEFAULT_COMPANY = {
    "name": "",
    "tagline": "",
    "address": "",
    "phone": "",
    "email": "",
    "website": ""
}

def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except Exception:
            pass
    save_json(filepath, default)
    return default

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

def get_catalog():
    if os.path.exists(INVENTORY_FILE):
        try:
            with open(INVENTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    save_json(INVENTORY_FILE, DEFAULT_CATALOG)
    return DEFAULT_CATALOG

def save_catalog(catalog):
    save_json(INVENTORY_FILE, catalog)

def get_company_profile():
    if os.path.exists(COMPANY_FILE):
        try:
            with open(COMPANY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    save_json(COMPANY_FILE, DEFAULT_COMPANY)
    return DEFAULT_COMPANY

def save_company_profile(profile):
    save_json(COMPANY_FILE, profile)

def get_clients():
    if os.path.exists(CLIENTS_FILE):
        try:
            with open(CLIENTS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    save_json(CLIENTS_FILE, [])
    return []

def save_clients(clients):
    save_json(CLIENTS_FILE, clients)

def load_counter():
    try:
        with open(INV_COUNTER_FILE, "r") as f:
            return int(f.read().strip())
    except Exception:
        return 1000

def save_counter(val):
    with open(INV_COUNTER_FILE, "w") as f:
        f.write(str(val))