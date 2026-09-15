import os
import requests
import pytest

from dotenv import load_dotenv
load_dotenv()

BASE_URL = os.environ.get("BASE_URL", "http://localhost:3000")

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

USER_USERNAME = os.environ.get("USER_USERNAME")
USER_PASSWORD = os.environ.get("USER_PASSWORD")


# ============================================================
# FIXTURES - Credentials (so test files don't need to re-read
# os.environ themselves - just request these as parameters)
# ============================================================

@pytest.fixture
def admin_username():
    return ADMIN_USERNAME


@pytest.fixture
def admin_password():
    return ADMIN_PASSWORD


@pytest.fixture
def user_username():
    return USER_USERNAME


@pytest.fixture
def user_password():
    return USER_PASSWORD


# ============================================================
# FIXTURES - Authentication
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
                                 "username": USER_USERNAME,
                                 "password": USER_PASSWORD})
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
# FIXTURES - Data factories (create projects/tasks on demand)
# ============================================================

@pytest.fixture
def create_project_by_admin(admin_session):
    created_projects = []

    def _create_project(name="newAdminProject1"):
        response = admin_session.post(f"{BASE_URL}/projects",
            json={"name": name})
        assert response.status_code == 201
        assert response.json()["name"] == name
        project_id = response.json()["id"]
        created_projects.append(project_id)
        return project_id

    yield _create_project

    for project_id in created_projects:
        response = admin_session.delete(f"{BASE_URL}/projects/{project_id}")
        assert response.status_code in [200, 404]


@pytest.fixture
def create_project_by_user(user_session):
    created_projects = []

    def _create_project(name="newUserProject1"):
        response = user_session.post(f"{BASE_URL}/projects",
            json={"name": name})
        assert response.status_code == 201
        assert response.json()["name"] == name
        project_id = response.json()["id"]
        created_projects.append(project_id)
        return project_id

    yield _create_project

    for project_id in created_projects:
        response = user_session.delete(f"{BASE_URL}/projects/{project_id}")
        assert response.status_code in [200, 404]


@pytest.fixture
def create_task_by_admin(admin_session, create_project_by_admin):
    created_tasks = []

    def _create_task(project_id=None, title="newAdminTask1"):
        if project_id is None:
            project_id = create_project_by_admin()
        response = admin_session.post(f"{BASE_URL}/projects/{project_id}/tasks",
            json={"title": title})
        assert response.status_code == 201
        assert response.json()["title"] == title
        task_id = response.json()["id"]
        created_tasks.append((project_id, task_id))
        return task_id

    yield _create_task

    # Note: if the parent project was already deleted by the test itself,
    # its tasks are gone too - the server cascades the delete. 200/404
    # both count as success here, since either way the task ends up gone.
    for project_id, task_id in created_tasks:
        response = admin_session.delete(f"{BASE_URL}/projects/{project_id}/tasks/{task_id}")
        assert response.status_code in [200, 404]


@pytest.fixture
def create_task_by_user(user_session, create_project_by_user):
    created_tasks = []

    def _create_task(project_id=None, title="newUserTask1"):
        if project_id is None:
            project_id = create_project_by_user()
        response = user_session.post(f"{BASE_URL}/projects/{project_id}/tasks",
            json={"title": title})
        assert response.status_code == 201
        assert response.json()["title"] == title
        task_id = response.json()["id"]
        created_tasks.append((project_id, task_id))
        return task_id

    yield _create_task

    for project_id, task_id in created_tasks:
        response = user_session.delete(f"{BASE_URL}/projects/{project_id}/tasks/{task_id}")
        assert response.status_code in [200, 404]