import pytest
import requests
import os

from playwright.sync_api import expect

BASE_URL = os.environ.get("BASE_URL", "http://localhost:3000")


ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

UI_USER_USERNAME = os.environ.get("UI_USER_USERNAME")
UI_USER_PASSWORD = os.environ.get("UI_USER_PASSWORD")


def test_home_register_page(register_page):
    page = register_page
    expect(page.get_by_role("heading")).to_have_text("הרשמה")
    expect(page.get_by_role("textbox", name="שם משתמש")).to_be_visible()
    expect(page.get_by_role("textbox", name="סיסמה")).to_be_visible()
    expect(page.get_by_role("button", name="הירשם")).to_be_visible()
    expect(page.get_by_role("link", name="כבר יש לך חשבון? התחבר כאן")).to_be_visible()


def test_register_success(register_page):
    page = register_page
    page.get_by_role("textbox", name="שם משתמש").click()
    page.get_by_role("textbox", name="שם משתמש").fill("usertest")
    page.get_by_role("textbox", name="סיסמה").click()
    page.get_by_role("textbox", name="סיסמה").fill("123456")
    page.get_by_role("button", name="הירשם").click()
    expect(page.locator("#login-success")).to_have_text("נרשמת בהצלחה! אפשר להתחבר עכשיו.")
    expect(page).to_have_url("http://localhost:8080/")
    expect(page.get_by_role("heading")).to_have_text("התחברות")
    
    response = requests.post(f"{BASE_URL}/login",
                             json={"username": "usertest",
                                   "password": "123456"})
    assert response.status_code == 200
    user_id = response.json()["id"]
    
    response = requests.delete(f"{BASE_URL}/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "User deleted successfully"
    
    
@pytest.mark.parametrize("username, password, message", [
    (UI_USER_USERNAME, UI_USER_PASSWORD, "Username already exists"),
    (ADMIN_USERNAME, ADMIN_PASSWORD, "Username already exists"),
    ("", "", "username and password are required"),
    ("try", "try", "username and password are required"),
    ("    ", "    ", "username and password are required"),
    ("test", "", "username and password are required"),
    ("test2", "      ", "username and password are required"),
    ("", "123456", "username and password are required")
])
def test_register_invalid_fields(register_page, username, password, message):
    page = register_page
    page.get_by_role("textbox", name="שם משתמש").click()
    page.get_by_role("textbox", name="שם משתמש").fill(username)
    page.get_by_role("textbox", name="סיסמה").click()
    page.get_by_role("textbox", name="סיסמה").fill(password)
    page.get_by_role("button", name="הירשם").click()
    expect(page.locator("#register-error")).to_have_text(message)
    expect(page).to_have_url("http://localhost:8080/register")
