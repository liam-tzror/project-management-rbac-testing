import os
from playwright.sync_api import expect


BASE_URL = os.environ.get("BASE_URL", "http://localhost:3000")


def test_admin_can_view_all_projects(create_project_by_admin, create_project_by_user, logged_in_page_as_admin):
    user_project_name = create_project_by_user["name"]
    admin_project_name = create_project_by_admin["name"]
    page = logged_in_page_as_admin
    
    expect(page.locator("#project-list li").filter(has_text=admin_project_name)).to_be_visible()
    expect(page.locator("#project-list li").filter(has_text=user_project_name)).to_be_visible()
    
    
def test_admin_can_delete_user_project(create_project_by_user, logged_in_page_as_admin):
    project_name = create_project_by_user["name"]
    page = logged_in_page_as_admin
    
    project = page.locator("#project-list li").filter(has_text=project_name)
    expect(project.get_by_role("button", name="מחק")).to_be_visible()
    project.get_by_role("button", name="מחק").click()
        
    expect(page.locator("#project-list li").filter(has_text=project_name)).not_to_be_visible()
    
    
def test_admin_panel_visible_only_to_admin(create_project_by_admin, logged_in_page_as_admin):
    project_name = create_project_by_admin["name"]
    page = logged_in_page_as_admin
        
    project = page.locator("#project-list li").filter(has_text=project_name)
    project.get_by_role("button", name="פתח").click()
        
    expect(page.get_by_role("button", name="← חזרה לפרויקטים")).to_be_visible()
    expect(page.locator("#current-project-name")).to_have_text(project_name)
    expect(page.get_by_role("textbox", name="שם משימה חדשה")).to_be_visible()
    expect(page.get_by_role("button", name="הוסף משימה")).to_be_visible()
    expect(page.locator("#admin-panel")).to_contain_text("פאנל ניהול (admin בלבד) בתור admin, אתה יכול לערוך ולמחוק גם משימות שאינן שלך.")