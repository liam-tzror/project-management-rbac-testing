import os
import requests
import pytest


BASE_URL = os.environ.get("BASE_URL", "http://localhost:3000")

# ============================================================
# TESTS - Projects: creation, ownership, authorization
# ============================================================

def test_create_project_by_admin(admin_session, admin_user):
    response = admin_session.post(f"{BASE_URL}/projects",
                                  json={"name": "newAdminProject1"})
    assert response.status_code == 201
    assert response.json()["name"] == "newAdminProject1"
    assert response.json()["owner_id"] == admin_user["id"]
    
    # ניקוי
    project_id = response.json()["id"]
    response = admin_session.delete(f"{BASE_URL}/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Project deleted successfully"


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


def test_admin_delete_user_project_also_deletes_tasks(admin_session, create_project_by_user, create_task_by_user):
    project_id = create_project_by_user()
    create_task_by_user(project_id)

    response = admin_session.delete(f"{BASE_URL}/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Project deleted successfully"

    response = admin_session.get(f"{BASE_URL}/projects/{project_id}/tasks?status=X")
    assert response.status_code == 404


def test_user_cannot_set_owner_id_on_create(user_session, admin_user, user_user):
    # Mass assignment check: user tries to claim admin's id as the
    # owner of a project they're creating. The server must ignore
    # whatever owner_id is sent and use the actual logged-in user's id.
    user_id = user_user["id"]

    response = user_session.post(f"{BASE_URL}/projects",
                                 json={"name": "newproject",
                                       "owner_id": admin_user["id"]})
    assert response.status_code == 201
    assert response.json()["owner_id"] == user_id
    
    # ניקוי
    project_id = response.json()["id"]
    response = user_session.delete(f"{BASE_URL}/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Project deleted successfully"


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


def test_create_project_empty_name(user_session):
    response = user_session.post(f"{BASE_URL}/projects",
                                 json={"name": " "})
    assert response.status_code == 400
    assert response.json()["error"] == "Project name is required"


def test_get_nonexistent_project(user_session):
    response = user_session.get(f"{BASE_URL}/projects/841284")
    assert response.status_code == 404
    assert response.json()["error"] == "Project not found"


def test_delete_nonexistent_project(user_session):
    response = user_session.delete(f"{BASE_URL}/projects/323813")
    assert response.status_code == 404
    assert response.json()["error"] == "Project not found"


def test_no_token_on_projects():
    response = requests.get(f"{BASE_URL}/projects")
    assert response.status_code == 401
    assert response.json()["error"] == "Token required"
    
    
def test_update_project_name(admin_session, create_project_by_admin, admin_user):
    project_id = create_project_by_admin("newprojectadmin")
    response = admin_session.put(f"{BASE_URL}/projects/{project_id}",
                                 json={"name": "updateadmin"})
    assert response.status_code == 200
    assert response.json()["name"] == "updateadmin"
    assert response.json()["owner_id"] == admin_user["id"]
    
    
def test_user_cannot_update_admin_project_name(user_session, create_project_by_admin, admin_session):
    project_id = create_project_by_admin("newprojectadmin")
    response = user_session.put(f"{BASE_URL}/projects/{project_id}",
                                     json={"name": "newnamebyuser"})
    assert response.status_code == 403
    assert response.json()["error"] == "Access denied"
    
    response = admin_session.get(f"{BASE_URL}/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "newprojectadmin"
    
    
def test_admin_can_update_user_project_name(admin_session, create_project_by_user):
    project_id = create_project_by_user("newprojectuser")
    response = admin_session.put(f"{BASE_URL}/projects/{project_id}",
                                 json={"name": "updatenamebyadmin"})
    assert response.status_code == 200
    assert response.json()["name"] == "updatenamebyadmin"
    


def test_update_project_empty_name(user_session, create_project_by_user):
    project_id = create_project_by_user("newuserproject")
    response = user_session.put(f"{BASE_URL}/projects/{project_id}",
                                json={"name": "     "})
    assert response.status_code == 400
    assert response.json()["error"] == "Project name is required"
    
    
def test_update_nonexistent_project(user_session):
    response = user_session.put(f"{BASE_URL}/projects/321342",
                                json={"name": "updateprojectname"})
    assert response.status_code == 404
    assert response.json()["error"] == "Project not found"