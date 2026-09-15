import os
import requests
import pytest


BASE_URL = os.environ.get("BASE_URL", "http://localhost:3000")

# ============================================================
# TESTS - Known issues (intentional bugs, kept for documentation)
#
# xfail = a real bug, marked so CI stays green but the gap is tracked.
# test_public_registration_can_create_admin has no xfail because it
# passes on purpose - the pass itself is what proves the bug exists.
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
