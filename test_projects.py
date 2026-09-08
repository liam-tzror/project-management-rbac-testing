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
def user_token():
    requests.post(f"{BASE_URL}/register",
                  json={"username": USER_USERNAME, "password": USER_PASSWORD})
    response_login = requests.post(f"{BASE_URL}/login",
                                 json={
                                     "username": USER_USERNAME,
                                     "password": USER_PASSWORD})
    assert response_login.status_code == 200
    user_id = response_login.json()["id"]
    yield response_login.json()["token"]
    response = requests.delete(f"{BASE_URL}/users/{user_id}")
    assert response.status_code == 200


@pytest.fixture
def admin_session(admin_user):
    s = requests.Session()
    s.headers.update({"authorization": admin_user["token"]})
    return s


@pytest.fixture
def user_session(user_token):
    s = requests.Session()
    s.headers.update({"authorization": user_token})
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


# ============================================================
# TESTS - Projects: creation, ownership, authorization
# ============================================================

def test_create_project_by_admin(admin_session, admin_user):
    response = admin_session.post(f"{BASE_URL}/projects",
                                  json={"name": "newAdminProject1"})
    assert response.status_code == 201
    assert response.json()["name"] == "newAdminProject1"
    assert response.json()["owner_id"] == admin_user["id"]


def test_user_cannot_access_admin_project(user_session, create_project_by_admin):
    project_id = create_project_by_admin()
    response = user_session.get(f"{BASE_URL}/projects/{project_id}")
    assert response.status_code == 403


def test_admin_can_delete_any_project(admin_session, create_project_by_user):
    project_id = create_project_by_user()
    response = admin_session.delete(f"{BASE_URL}/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Project deleted successfully"

    response = admin_session.get(f"{BASE_URL}/projects/{project_id}")
    assert response.status_code == 404


def test_user_cannot_delete_admin_project(user_session, create_project_by_admin):
    project_id = create_project_by_admin()
    response = user_session.delete(f"{BASE_URL}/projects/{project_id}")
    assert response.status_code == 403
    assert response.json()["error"] == "Access denied"


def test_user_cannot_add_task_to_admin_project(user_session, create_project_by_admin):
    project_id = create_project_by_admin()
    response = user_session.post(f"{BASE_URL}/projects/{project_id}/tasks",
                                json={"title": "newtask"})
    assert response.status_code == 403
    assert response.json()["error"] == "Access denied"


def test_user_cannot_update_task_in_admin_project(user_session, create_task_by_admin):
    task_id = create_task_by_admin()
    response = user_session.put(f"{BASE_URL}/tasks/{task_id}",
                                    json={"title": "newtask"})
    assert response.status_code == 403
    assert response.json()["error"] == "Access denied"


def test_admin_can_view_all_projects(admin_session, create_project_by_admin, create_project_by_user):
    create_project_by_admin("newAdminProject1")
    create_project_by_user("newUserProject1")

    response = admin_session.get(f"{BASE_URL}/projects")
    assert response.status_code == 200
    project_names = [p["name"] for p in response.json()]
    assert "newAdminProject1" in project_names
    assert "newUserProject1" in project_names


def test_user_only_sees_own_projects(user_session, create_project_by_user, create_project_by_admin):
    create_project_by_admin("newAdminProject1")
    create_project_by_user("newUserProject1")

    response = user_session.get(f"{BASE_URL}/projects")
    assert response.status_code == 200
    project_names = [p["name"] for p in response.json()]
    assert "newUserProject1" in project_names
    assert "newAdminProject1" not in project_names


def test_admin_can_add_task_to_user_project(admin_session, create_project_by_user):
    project_id = create_project_by_user()
    response = admin_session.post(f"{BASE_URL}/projects/{project_id}/tasks",
                                  json={"title": "newtaskbyadmin"})
    assert response.status_code == 201
    assert response.json()["title"] == "newtaskbyadmin"


def test_admin_can_update_user_task(admin_session, create_task_by_user):
    task_id = create_task_by_user()
    response = admin_session.put(f"{BASE_URL}/tasks/{task_id}",
                                 json={"title": "taskupdatebyadmin"})
    assert response.status_code == 200
    assert response.json()["title"] == "taskupdatebyadmin"


def test_admin_delete_user_project_also_deletes_tasks(admin_session, create_project_by_user, create_task_by_user):
    project_id = create_project_by_user()
    create_task_by_user(project_id)

    response = admin_session.delete(f"{BASE_URL}/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Project deleted successfully"

    response = admin_session.get(f"{BASE_URL}/projects/{project_id}/tasks?status=X")
    assert response.status_code == 404


def test_user_cannot_set_owner_id_on_create(user_session, admin_user):
    # Mass assignment check: user tries to claim admin's id as the
    # owner of a project they're creating. The server must ignore
    # whatever owner_id is sent and use the actual logged-in user's id.
    response_login = requests.post(f"{BASE_URL}/login",
                                   json={"username": USER_USERNAME,
                                         "password": USER_PASSWORD})
    user_id = response_login.json()["id"]

    response = user_session.post(f"{BASE_URL}/projects",
                                 json={"name": "newproject",
                                       "owner_id": admin_user["id"]})
    assert response.status_code == 201
    assert response.json()["owner_id"] == user_id


# ============================================================
# TESTS - Tasks: creation, filtering, updates
# ============================================================

def test_filter_tasks_by_status(user_session, create_task_by_user):
    task_id = create_task_by_user()
    response = user_session.put(f"{BASE_URL}/tasks/{task_id}",
                                json={"status": "done"})
    assert response.status_code == 200
    assert response.json()["status"] == "done"

    response = user_session.get(f"{BASE_URL}/tasks?status=done")
    assert response.status_code == 200
    assert response.json()[0]["status"] == "done"


def test_update_task_title_only(user_session, create_task_by_user):
    task_id = create_task_by_user()
    response = user_session.put(f"{BASE_URL}/tasks/{task_id}",
                                json={"title": "taskupdate"})
    assert response.status_code == 200
    assert response.json()["title"] == "taskupdate"


def test_update_task_partial_update(user_session, create_task_by_user):
    # Sending only title should not clear/reset the existing status
    task_id = create_task_by_user()
    response = user_session.put(f"{BASE_URL}/tasks/{task_id}",
                                    json={"title": "taskupdate"})
    assert response.status_code == 200
    assert response.json()["title"] == "taskupdate"
    assert response.json()["status"] == "pending"


def test_update_task_status_only_keeps_title(user_session, create_task_by_user):
    # The reverse of the above: sending only status should not clear/reset the existing title
    task_name = "newtaskbyuser"
    task_id = create_task_by_user(title=task_name)
    response = user_session.put(f"{BASE_URL}/tasks/{task_id}",
                                json={"status": "done"})
    assert response.status_code == 200
    assert response.json()["status"] == "done"
    assert response.json()["title"] == task_name


def test_delete_project_twice_is_idempotent(user_session, create_project_by_user):
    project_id = create_project_by_user("newprojectbyuser")
    response = user_session.delete(f"{BASE_URL}/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Project deleted successfully"

    # deleting the same project again should fail cleanly, not crash
    response = user_session.delete(f"{BASE_URL}/projects/{project_id}")
    assert response.status_code == 404
    assert response.json()["error"] == "Project not found"

    response = user_session.get(f"{BASE_URL}/projects/{project_id}")
    assert response.status_code == 404


def test_update_task_in_deleted_project(user_session, create_project_by_user, create_task_by_user):
    project_id = create_project_by_user()
    task_id = create_task_by_user(project_id, "newtask")

    response = user_session.delete(f"{BASE_URL}/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Project deleted successfully"

    # the task was deleted along with its parent project
    response = user_session.put(f"{BASE_URL}/tasks/{task_id}",
                                json={"title": "newtasktitle"})
    assert response.status_code == 404
    assert response.json()["error"] == "Task not found"


def test_multiple_projects_per_user(user_session, create_project_by_user):
    project_ids = [
        create_project_by_user("Project 1"),
        create_project_by_user("Project 2"),
        create_project_by_user("Project 3")
    ]

    response = user_session.get(f"{BASE_URL}/projects/")
    assert response.status_code == 200

    projects = response.json()
    project_ids_response = [project["id"] for project in projects]

    for p in project_ids:
        assert p in project_ids_response


# ============================================================
# TESTS - Validation
# ============================================================

def test_create_project_empty_name(user_session):
    response = user_session.post(f"{BASE_URL}/projects",
                                 json={"name": " "})
    assert response.status_code == 400
    assert response.json()["error"] == "Project name is required"


def test_create_task_empty_title(user_session, create_project_by_user):
    project_id = create_project_by_user()
    response = user_session.post(f"{BASE_URL}/projects/{project_id}/tasks",
                                 json={"title": "       "})
    assert response.status_code == 400
    assert response.json()["error"] == "Title is required"


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


def test_register_duplicate_username():
    response = requests.post(f"{BASE_URL}/register",
                             json={"username": ADMIN_USERNAME,
                                   "password": ADMIN_PASSWORD})
    assert response.status_code == 400
    assert response.json()["error"] == "Username already exists"


def test_login_wrong_password():
    response = requests.post(f"{BASE_URL}/login",
                             json={"username": "liam32",
                                   "password": "12652313"})
    assert response.status_code == 401
    assert response.json()["error"] == "Invalid username or password"


def test_login_nonexistent_user():
    response = requests.post(f"{BASE_URL}/login",
                                 json={"username": "liam441",
                                       "password": "16734"})
    assert response.status_code == 401
    assert response.json()["error"] == "Invalid username or password"


def test_admin_login_returns_correct_role():
    response = requests.post(f"{BASE_URL}/login",
                             json={"username": ADMIN_USERNAME,
                                   "password": ADMIN_PASSWORD})
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_user_login_returns_correct_role(user_session):
    response = requests.post(f"{BASE_URL}/login",
                             json={"username": USER_USERNAME,
                                   "password": USER_PASSWORD})
    assert response.status_code == 200
    assert response.json()["role"] == "user"


# ============================================================
# TESTS - Not found (404)
# ============================================================

def test_get_nonexistent_project(user_session):
    response = user_session.get(f"{BASE_URL}/projects/841284")
    assert response.status_code == 404
    assert response.json()["error"] == "Project not found"


def test_delete_nonexistent_project(user_session):
    response = user_session.delete(f"{BASE_URL}/projects/323813")
    assert response.status_code == 404
    assert response.json()["error"] == "Project not found"


def test_update_nonexistent_task(user_session):
    response = user_session.put(f"{BASE_URL}/tasks/1241295",
                                json={"title": "newtask"})
    assert response.status_code == 404
    assert response.json()["error"] == "Task not found"


def test_add_task_to_nonexistent_project(user_session):
    response = user_session.post(f"{BASE_URL}/projects/4127721/tasks",
                                 json={"title": "newtask"})
    assert response.status_code == 404
    assert response.json()["error"] == "Project not found"


# ============================================================
# TESTS - No token (401)
# ============================================================

def test_no_token_on_projects():
    response = requests.get(f"{BASE_URL}/projects")
    assert response.status_code == 401
    assert response.json()["error"] == "Token required"


def test_no_token_on_create_task(create_project_by_user):
    project_id = create_project_by_user()
    response = requests.post(f"{BASE_URL}/projects/{project_id}/tasks",
                             json={"title": "newtask"})
    assert response.status_code == 401
    assert response.json()["error"] == "Token required"


# ============================================================
# TESTS - Known issues (intentional bugs, kept for documentation)
#
# xfail = a real bug, marked so CI stays green but the gap is tracked.
# test_public_registration_can_create_admin has no xfail because it passes on purpose - the pass itself is what proves the bug exists.
# ============================================================

def test_public_registration_can_create_admin():
    # BUG: /register accepts a role field with no restriction, so anyone
    # can self-register as admin. This test documents that the bug
    # exists (it's expected to pass, but "passing" here means the
    # security hole is confirmed, not that the system is safe)
    response = requests.post(f"{BASE_URL}/register",
                             json={"username": "createadmin",
                                   "password": "123456",
                                   "role": "admin"})
    assert response.status_code == 201

    response = requests.post(f"{BASE_URL}/login",
                             json={
                                 "username": "createadmin",
                                 "password": "123456"})
    assert response.status_code == 200
    user_id = response.json()["id"]

    response = requests.delete(f"{BASE_URL}/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "User deleted successfully"


@pytest.mark.xfail(reason="Server crashes with 500 instead of returning 400 when request body is missing entirely", strict=True)
def test_create_project_no_body(user_session):
    response = user_session.post(f"{BASE_URL}/projects")
    assert response.status_code == 400
    assert response.json()["error"] == "Project name is required"


@pytest.mark.xfail(reason="Server accepts any status value without validation - no whitelist of allowed statuses", strict=True)
@pytest.mark.parametrize("bad_status", [
    21345,
    "<script>alert('hacked')</script>",
    "      ",
    "a" * 500
])
def test_task_status_accepts_any_string(user_session, create_task_by_user, bad_status):
    task_id = create_task_by_user()
    response = user_session.put(f"{BASE_URL}/tasks/{task_id}",
                                json={"status": bad_status})
    assert response.status_code == 400


@pytest.mark.xfail(reason="Server crashes with 500 instead of 400 when Content-Type is wrong and body can't be parsed", strict=True)
def test_wrong_content_type_on_create_project(user_session):
    response = user_session.post(f"{BASE_URL}/projects",
                                 data='{"name": "newproject"}',
                                 headers={"Content-Type": "text/plain"})
    assert response.status_code == 400
    assert response.json()["error"] == "Project name is required"