# Project Management RBAC Testing

REST API and UI test automation for a role-based project management system (projects, tasks, admin/user permissions). Built with Python, pytest, and Playwright.

This is a hands-on QA automation practice project: a small Node.js/Express/SQLite backend I built specifically to test against, plus a full Python test suite covering the API and a browser UI, with a CI pipeline that runs everything automatically on every push.

---

## What's in this project

- **`server.js`** — the backend: users (with roles), projects, tasks, and a full authorization layer (admin vs regular user).
- **`index.html`** — a minimal single-page UI on top of the API: login, register, project list, and a task screen per project.
- **`tests/api/`** — pytest tests against the API directly, using `requests`.
- **`tests/ui/`** — pytest + Playwright tests that drive the actual browser UI.
- **`API_DOCUMENTATION.md`** — full reference for every endpoint, including known bugs found during testing.
- **`.github/workflows/tests.yml`** — GitHub Actions pipeline that runs the entire suite (API + UI) automatically on every push.

---

## Project structure

```
qa-project2/
├── server.js
├── package.json
├── index.html
├── setup.py
├── requirements.txt
├── .env.example
├── API_DOCUMENTATION.md
├── .github/
│   └── workflows/
│       └── tests.yml
└── tests/
    ├── api/
    │   ├── conftest.py
    │   ├── test_auth.py
    │   ├── test_projects.py
    │   ├── test_tasks.py
    │   └── test_known_issues.py
    └── ui/
        ├── conftest.py
        ├── test_login.py
        ├── test_register.py
        ├── test_projects_user.py
        ├── test_projects_admin.py
        ├── test_tasks_user.py
        └── test_tasks_admin.py
```

---

## Running this project locally

### 1. Install dependencies

```
npm install
pip install -r requirements.txt --break-system-packages
```

(If there's no `requirements.txt` yet, install directly: `pip install requests pytest pytest-playwright python-dotenv --break-system-packages`, then `playwright install`.)

### 2. Start the server

```
node server.js
```

Leave this running in its own terminal — the tests need it live at `http://localhost:3000`.

### 3. Start the UI

In a second terminal:

```
python -m http.server 8080
```

The UI is now available at `http://localhost:8080`.

### 4. Set up test users

In a third terminal:

```
python setup.py
```

This script does two things: it copies `.env.example` to `.env` (if you don't already have one), and it registers the fixed test accounts the tests rely on — an admin user and two regular user accounts (one used by the API tests, one by the UI tests). It's safe to run more than once; it skips anything that already exists.

### 5. Run the tests

All API tests:
```
python -m pytest tests/api/ -v
```

All UI tests:
```
python -m pytest tests/ui/ -v
```

Everything together:
```
python -m pytest tests/ -v
```

---

## Test coverage

### API tests (`tests/api/`)

Covers the full REST API directly, with no browser involved:

- **Authentication** — register/login validation, duplicate usernames, wrong passwords, correct role returned on login.
- **Projects** — creation, ownership, updating a project's name, deleting (including idempotent double-delete), listing (admin sees everything, a regular user sees only their own).
- **Tasks** — creation, partial updates (updating only `title` or only `status` without clearing the other field), status filtering, behavior after the parent project is deleted.
- **Authorization** — a full matrix of admin vs. regular user access: who can view, create, update, and delete each resource, and who gets blocked with a 403.
- **Mass assignment protection** — confirming a user can't set `owner_id` themselves when creating a project.
- **Known issues** — a handful of real bugs found in the server, documented below.

### UI tests (`tests/ui/`)

Drives the actual browser with Playwright, against the same server:

- **Login/register screens** — layout, successful login for both roles, invalid-field handling (parametrized across several bad inputs), the role badge's color/class.
- **Projects (user)** — viewing, creating, opening, deleting your own project, confirming another user's projects never appear in your list.
- **Projects (admin)** — seeing every user's projects, deleting a project that isn't the admin's own, and confirming the admin-only panel is visible inside a project.
- **Tasks (user & admin)** — adding a task, updating its status through the dropdown, and admin's ability to add/update tasks inside another user's project.

### Why some API tests use `requests` for setup/cleanup inside a `page`-based UI test

A few UI tests create or clean up data through direct API calls (`requests`) rather than clicking through the browser for every step. This is intentional: Playwright is used for whatever the test is actually verifying (a click, a form, what appears on screen), while API calls handle fast, reliable setup and teardown that isn't the point of the test itself — the same way a fixture prepares data without being "the test." It keeps each test focused on one thing and makes the suite much faster than doing everything through the UI.

---

## CI/CD

`.github/workflows/tests.yml` runs the entire suite automatically on every push to GitHub. The pipeline:

1. Checks out the code and installs Node and Python dependencies.
2. Starts the server in the background.
3. Runs `python setup.py` — this is what makes the pipeline self-contained. Since `.env` is never committed to the repository (it's in `.gitignore`, by design — see below), the CI environment starts with no `.env` file and no test users at all. `setup.py` creates `.env` from `.env.example` and registers the test accounts through the API, so the exact same script that sets up a fresh local machine also sets up the CI runner, with no separate CI-only logic needed.
4. Runs the full API test suite.
5. Starts the static file server for the UI.
6. Runs the full UI test suite (Playwright, headless).

---

## Environment variables and `.env`

Test credentials (the admin account and the two fixed test users) live in a `.env` file, which is **not** committed to GitHub — it's excluded via `.gitignore` so no username/password combination is ever visible in the repository's history. `.env.example` is committed instead: it shows the exact structure required, with the same values that already work against this server, so running `python setup.py` after cloning produces a working `.env` immediately, no manual editing needed.

---

## Known Issues

The server has a handful of intentional, documented bugs, found and confirmed through the test suite itself — see `API_DOCUMENTATION.md` for the full list and the exact test that proves each one. Most of them are marked in the tests with `pytest.mark.xfail(strict=True)`, which keeps the CI pipeline green while still tracking the gap: if a bug is ever fixed, the corresponding test unexpectedly starts passing, and `strict=True` turns that into a visible failure — a built-in signal to go remove the outdated marker. One issue (public registration being able to create an admin account) is deliberately *not* marked `xfail`, because that test is supposed to pass — the pass itself is what confirms the vulnerability exists.