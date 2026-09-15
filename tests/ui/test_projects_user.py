import os
import pytest
from playwright.sync_api import expect


BASE_URL = os.environ.get("BASE_URL", "http://localhost:3000")


def test_user_can_view_projects(logged_in_page_as_user):
    page = logged_in_page_as_user
    expect(page.get_by_role("heading")).to_have_text("הפרויקטים שלי user")
    expect(page.get_by_role("textbox", name="שם פרויקט חדש")).to_be_visible()
    expect(page.get_by_role("button", name="הוסף פרויקט")).to_be_visible()
    expect(page.get_by_role("button", name="התנתק")).to_be_visible()
    

def test_user_can_create_project(logged_in_page_as_user, user_session):
    page = logged_in_page_as_user
    page.get_by_role("textbox", name="שם פרויקט חדש").click()
    page.get_by_role("textbox", name="שם פרויקט חדש").fill("userproject")
    page.get_by_role("button", name="הוסף פרויקט").click()
        
    project = page.locator("#project-list li").filter(has_text="userproject")
    expect(project).to_be_visible()
    expect(project.get_by_role("button", name="פתח")).to_be_visible()
    expect(project.get_by_role("button", name="מחק")).to_be_visible()
    
    response = user_session.get(f"{BASE_URL}/projects")
    assert response.status_code == 200
    projects = response.json()
    for p in projects:
        if p["name"] == "userproject":
            user_session.delete(f"{BASE_URL}/projects/{p['id']}")
            
    
def test_user_can_open_project(create_project_by_user ,logged_in_page_as_user):
    project_name = create_project_by_user["name"]
    page = logged_in_page_as_user
    
    project = page.locator("#project-list li").filter(has_text=project_name)
    project.get_by_role("button", name="פתח").click()
    
    expect(page.get_by_role("button", name="← חזרה לפרויקטים")).to_be_visible()
    expect(page.locator("#current-project-name")).to_have_text(project_name)
    expect(page.get_by_role("textbox", name="שם משימה חדשה")).to_be_visible()
    expect(page.get_by_role("button", name="הוסף משימה")).to_be_visible()
    
    
def test_user_can_delete_own_project(create_project_by_user, logged_in_page_as_user):
    project_name = create_project_by_user["name"]
    page = logged_in_page_as_user
    
    project = page.locator("#project-list li").filter(has_text=project_name)
    expect(project.get_by_role("button", name="מחק")).to_be_visible()
    project.get_by_role("button", name="מחק").click()
    
    expect(page.locator("#project-list li").filter(has_text=project_name)).not_to_be_visible()
    
    
def test_user_cannot_see_admin_projects_in_list(create_project_by_admin, logged_in_page_as_user):
    project_name = create_project_by_admin["name"]
    page = logged_in_page_as_user
    expect(page.locator("#project-list li").filter(has_text=project_name)).not_to_be_visible()
    

@pytest.mark.parametrize("project_name", [
    "",
    "       "
])
def test_create_project_invalid_fields(logged_in_page_as_user, project_name):
    page = logged_in_page_as_user
    page.get_by_role("textbox", name="שם פרויקט חדש").click()
    page.get_by_role("textbox", name="שם פרויקט חדש").fill(project_name)
    page.get_by_role("button", name="הוסף פרויקט").click()
    expect(page.locator("#project-error")).to_have_text("Project name is required")
    
    