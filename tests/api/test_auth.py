import pytest
import os
import requests


BASE_URL = os.environ.get("BASE_URL", "http://localhost:3000")

# ============================================================
# TESTS - Authentication: register, login, validation, roles
# ============================================================

def test_register_missing_username():
    response = requests.post(f"{BASE_URL}/register",
                             json={"password": 12345})
    assert response.status_code == 400
    assert response.json()["error"] == "username and password are required"


def test_register_missing_password():
    response = requests.post(f"{BASE_URL}/register",
                             json={"username": "liam123"})
    assert response.status_code == 400
    assert response.json()["error"] == "username and password are required"


def test_register_duplicate_username(admin_username, admin_password):
    response = requests.post(f"{BASE_URL}/register",
                             json={"username": admin_username,
                                   "password": admin_password})
    assert response.status_code == 400
    assert response.json()["error"] == "Username already exists"


@pytest.mark.parametrize("username, password", [
    ("liam32", "12652313"),
    ("liam441", "16734"),
])
def test_login_invalid_credentials(username, password):
    response = requests.post(f"{BASE_URL}/login",
                             json={"username": username, "password": password})
    assert response.status_code == 401
    assert response.json()["error"] == "Invalid username or password"


def test_admin_login_returns_correct_role(admin_username, admin_password):
    response = requests.post(f"{BASE_URL}/login",
                             json={"username": admin_username,
                                   "password": admin_password})
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_user_login_returns_correct_role(user_username, user_password):
    response = requests.post(f"{BASE_URL}/login",
                             json={"username": user_username,
                                   "password": user_password})
    assert response.status_code == 200
    assert response.json()["role"] == "user"
