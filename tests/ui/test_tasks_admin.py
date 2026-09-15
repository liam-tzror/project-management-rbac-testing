from playwright.sync_api import expect


def test_admin_can_add_task_to_user_project(create_project_by_user, logged_in_page_as_admin):
    project_name = create_project_by_user["name"]
    page = logged_in_page_as_admin
    
    project = page.locator("#project-list li").filter(has_text=project_name)
    project.get_by_role("button", name="פתח").click()
    
    page.get_by_role("textbox", name="שם משימה חדשה").fill("taskbyadmin")
    page.get_by_role("button", name="הוסף משימה").click()
    task = page.get_by_role("listitem").filter(has_text="taskbyadmin")
    expect(task.get_by_role("combobox")).to_be_visible()
    
    
def test_admin_can_update_task_status_in_user_project(create_task_by_user, logged_in_page_as_admin):
    project_name = create_task_by_user["name"]
    task_title = create_task_by_user["title"]
    page = logged_in_page_as_admin
    
    project = page.locator("#project-list li").filter(has_text=project_name)
    project.get_by_role("button", name="פתח").click()
    
    task = page.get_by_role("listitem").filter(has_text=task_title)
    expect(task.get_by_role("combobox")).to_be_visible()
    task.get_by_role("combobox").select_option("done")
    expect(task.get_by_role("combobox")).to_have_value("done")