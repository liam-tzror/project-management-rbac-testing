import pytest
from playwright.sync_api import expect


def test_user_can_add_task_to_own_project(create_project_by_user, logged_in_page_as_user):
    project_name = create_project_by_user["name"]
    page = logged_in_page_as_user
    
    project = page.locator("#project-list li").filter(has_text=project_name)
    project.get_by_role("button", name="פתח").click()
    
    page.get_by_role("textbox", name="שם משימה חדשה").fill("newtask")
    page.get_by_role("button", name="הוסף משימה").click()
    task = page.get_by_role("listitem").filter(has_text="newtask")
    expect(task.get_by_role("combobox")).to_be_visible()
    
    
def test_user_can_update_task_status(create_task_by_user, logged_in_page_as_user):
    project_name = create_task_by_user["name"]
    task_title = create_task_by_user["title"]
    page = logged_in_page_as_user
    
    project = page.locator("#project-list li").filter(has_text=project_name)
    project.get_by_role("button", name="פתח").click()
    
    task = page.get_by_role("listitem").filter(has_text=task_title)
    expect(task.get_by_role("combobox")).to_be_visible()
    task.get_by_role("combobox").select_option("done")
    expect(task.get_by_role("combobox")).to_have_value("done")
    

@pytest.mark.parametrize("task_name", [
    "",
    "       "
])
def test_create_task_empty_title(create_project_by_user ,logged_in_page_as_user, task_name):
    project_name = create_project_by_user["name"]
    page = logged_in_page_as_user
    
    project = page.locator("#project-list li").filter(has_text=project_name)
    project.get_by_role("button", name="פתח").click()
    
    page.get_by_role("textbox", name="שם משימה חדשה").fill(task_name)
    page.get_by_role("button", name="הוסף משימה").click()
    expect(page.locator("#task-error")).to_contain_text("Title is required")