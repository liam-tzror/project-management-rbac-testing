import pytest
import os
import requests
from playwright.sync_api import expect

from dotenv import load_dotenv
load_dotenv()

BASE_URL = os.environ.get("BASE_URL", "http://localhost:3000")

UI_BASE_URL = os.environ.get("UI_BASE_URL", "http://localhost:8080")


ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

UI_USER_USERNAME = os.environ.get("UI_USER_USERNAME")
UI_USER_PASSWORD = os.environ.get("UI_USER_PASSWORD")


# ============================================================
# FIXTURES - Authentication (API login, session objects)
# ============================================================

@pytest.fixture
def admin_user():
    response_login = requests.post(f"{BASE_URL}/login",
                             json={
                                 "username": ADMIN_USERNAME,
                                 "password": ADMIN_PASSWORD})
    assert response_login.status_code == 200
    return {"token": response_login.json()["token"], "id": response_login.json()["id"]}


@pytest.fixture
def user_user():
    response_login = requests.post(f"{BASE_URL}/login",
                             json={
                                 "username": UI_USER_USERNAME,
                                 "password": UI_USER_PASSWORD})
    assert response_login.status_code == 200
    return {"token": response_login.json()["token"], "id": response_login.json()["id"]}


@pytest.fixture
def admin_session(admin_user):
    s = requests.Session()
    s.headers.update({"authorization": admin_user["token"]})
    return s


@pytest.fixture
def user_session(user_user):
    s = requests.Session()
    s.headers.update({"authorization": user_user["token"]})
    return s


# ============================================================
# FIXTURES - Browser navigation (login/register through the UI)
# ============================================================

@pytest.fixture
def logged_in_page_as_admin(page):
    page.goto(f"{UI_BASE_URL}")
    page.get_by_role("textbox", name="שם משתמש").fill(ADMIN_USERNAME)
    page.get_by_role("textbox", name="סיסמה").fill(ADMIN_PASSWORD)
    page.get_by_role("button", name="התחבר").click()
    expect(page).to_have_url(f"{UI_BASE_URL}/projects")
    return page


@pytest.fixture
def logged_in_page_as_user(page):
    page.goto(f"{UI_BASE_URL}")
    page.get_by_role("textbox", name="שם משתמש").fill(UI_USER_USERNAME)
    page.get_by_role("textbox", name="סיסמה").fill(UI_USER_PASSWORD)
    page.get_by_role("button", name="התחבר").click()
    expect(page).to_have_url(f"{UI_BASE_URL}/projects")
    return page


@pytest.fixture
def register_page(page):
    page.goto(f"{UI_BASE_URL}/")
    page.get_by_role("link", name="אין לך חשבון? הירשם כאן").click()
    expect(page).to_have_url(f"{UI_BASE_URL}/register")
    return page


# ============================================================
# FIXTURES - Data factories (create projects/tasks via API)
# ============================================================

@pytest.fixture
def create_project_by_admin(admin_session):
    response = admin_session.post(f"{BASE_URL}/projects",
                                 json={"name": "adminproject"})
    assert response.status_code == 201
    project_id = response.json()["id"]
    yield {"id": project_id, "name": response.json()["name"]}
    admin_session.delete(f"{BASE_URL}/projects/{project_id}")
    
    
@pytest.fixture
def create_project_by_user(user_session):
    response = user_session.post(f"{BASE_URL}/projects",
                                 json={"name": "userproject"})
    assert response.status_code == 201
    project_id = response.json()["id"]
    yield {"id": project_id, "name": response.json()["name"]}
    user_session.delete(f"{BASE_URL}/projects/{project_id}")
    
    
# Created via API only, on purpose - tests combine this with
# logged_in_page_as_user and open the project themselves.
# No cleanup needed - the project's teardown cascades and deletes this too.
@pytest.fixture
def create_task_by_user(user_session, create_project_by_user):
    project_id = create_project_by_user["id"]
    response = user_session.post(f"{BASE_URL}/projects/{project_id}/tasks",
                                 json={"title": "newtask1"})
    assert response.status_code == 201
    return {"id": response.json()["id"], "title": response.json()["title"], "name": create_project_by_user["name"]}