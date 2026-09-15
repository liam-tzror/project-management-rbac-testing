import pytest
import os
from playwright.sync_api import expect

from dotenv import load_dotenv
load_dotenv()


ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

UI_USER_USERNAME = os.environ.get("UI_USER_USERNAME")
UI_USER_PASSWORD = os.environ.get("UI_USER_PASSWORD")


def test_home_login_page(page):
    page.goto("http://localhost:8080/")
    expect(page.get_by_role("heading")).to_have_text("התחברות")
    expect(page.get_by_role("textbox", name="שם משתמש")).to_be_visible()
    expect(page.get_by_role("textbox", name="סיסמה")).to_be_visible()
    expect(page.get_by_role("button", name="התחבר")).to_be_visible()
    expect(page.get_by_role("link", name="אין לך חשבון? הירשם כאן")).to_be_visible()


def test_login_as_admin(page):
    page.goto("http://localhost:8080/")
    page.get_by_role("textbox", name="שם משתמש").fill(ADMIN_USERNAME)
    page.get_by_role("textbox", name="סיסמה").fill(ADMIN_PASSWORD)
    page.get_by_role("button", name="התחבר").click()
    expect(page.locator("#role-badge")).to_contain_text("admin")
    expect(page).to_have_url("http://localhost:8080/projects")
    
    
def test_login_as_user(page):
    page.goto("http://localhost:8080/")
    page.get_by_role("textbox", name="שם משתמש").fill(UI_USER_USERNAME)
    page.get_by_role("textbox", name="סיסמה").fill(UI_USER_PASSWORD)
    page.get_by_role("button", name="התחבר").click()
    expect(page.locator("#role-badge")).to_contain_text("user")
    expect(page).to_have_url("http://localhost:8080/projects")
    
    
@pytest.mark.parametrize("username, password", [
    ("logintest", "12345"),
    ("", ""),
    ("    ", "    "),
    ("test", "    "),
    (UI_USER_USERNAME, ""),
    (ADMIN_USERNAME, ""),
    ("", "123456")
])
def test_login_invalid_fields(page, username, password):
    page.goto("http://localhost:8080/")
    page.get_by_role("textbox", name="שם משתמש").fill(username)
    page.get_by_role("textbox", name="סיסמה").fill(password)
    page.get_by_role("button", name="התחבר").click()
    expect(page.locator("#login-error")).to_contain_text("Invalid username or password")
    
    
def test_login_role_badge_shows_correct_color_admin(page):
    page.goto("http://localhost:8080/")
    page.get_by_role("textbox", name="שם משתמש").fill(ADMIN_USERNAME)
    page.get_by_role("textbox", name="סיסמה").fill(ADMIN_PASSWORD)
    page.get_by_role("button", name="התחבר").click()
    expect(page.locator("#role-badge")).to_have_class("badge admin")
    
    
def test_login_role_badge_shows_correct_color_user(page):
    page.goto("http://localhost:8080/")
    page.get_by_role("textbox", name="שם משתמש").fill(UI_USER_USERNAME)
    page.get_by_role("textbox", name="סיסמה").fill(UI_USER_PASSWORD)
    page.get_by_role("button", name="התחבר").click()
    expect(page.locator("#role-badge")).to_have_class("badge user")