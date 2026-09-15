"""
Setup script - creates a .env file from .env.example if one doesn't
already exist, and registers the fixed test users (admin, a regular
API test user, and a UI test user) needed for both test suites.

Usage: python setup.py

Note: the server (node server.js) must already be running before
you run this script, since it registers users through the API.
"""
import shutil
import os
import requests

BASE_URL = "http://localhost:3000"

if os.path.exists(".env"):
    print(".env already exists - skipping.")
else:
    shutil.copy(".env.example", ".env")
    print(".env created from .env.example.")

from dotenv import load_dotenv
load_dotenv()

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
USER_USERNAME = os.environ.get("USER_USERNAME")
USER_PASSWORD = os.environ.get("USER_PASSWORD")
UI_USER_USERNAME = os.environ.get("UI_USER_USERNAME")
UI_USER_PASSWORD = os.environ.get("UI_USER_PASSWORD")


def register_if_needed(username, password, role="user"):
    payload = {"username": username, "password": password}
    if role == "admin":
        payload["role"] = "admin"
    response = requests.post(f"{BASE_URL}/register", json=payload)
    if response.status_code == 201:
        print(f"Created user: {username} ({role})")
    elif response.status_code == 400:
        print(f"User already exists: {username} - skipping.")
    else:
        print(f"Unexpected response creating {username}: {response.status_code}")


try:
    register_if_needed(ADMIN_USERNAME, ADMIN_PASSWORD, role="admin")
    register_if_needed(USER_USERNAME, USER_PASSWORD, role="user")
    register_if_needed(UI_USER_USERNAME, UI_USER_PASSWORD, role="user")
    print("Setup complete. You're ready to run the tests.")
except requests.exceptions.ConnectionError:
    print("Could not connect to the server. Make sure 'node server.js' is running first.")