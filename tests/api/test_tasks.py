import os
import requests


BASE_URL = os.environ.get("BASE_URL", "http://localhost:3000")

# ============================================================
# TESTS - Tasks: creation, filtering, updates, authorization
# ============================================================

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


def test_create_task_empty_title(user_session, create_project_by_user):
    project_id = create_project_by_user()
    response = user_session.post(f"{BASE_URL}/projects/{project_id}/tasks",
                                 json={"title": "       "})
    assert response.status_code == 400
    assert response.json()["error"] == "Title is required"


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


def test_no_token_on_create_task(create_project_by_user):
    project_id = create_project_by_user()
    response = requests.post(f"{BASE_URL}/projects/{project_id}/tasks",
                             json={"title": "newtask"})
    assert response.status_code == 401
    assert response.json()["error"] == "Token required"
