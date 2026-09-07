# API Documentation - Projects & Tasks System

Base URL: http://localhost:3000

## Authentication

### POST /register
Creates a new user.

Body (JSON):
```
{
  "username": "string (required)",
  "password": "string (required)",
  "role": "admin" | "user" (optional, defaults to "user")
}
```

Responses:
- 201: `{ "message": "User created successfully" }`
- 400: `{ "error": "username and password are required" }` — missing fields
- 400: `{ "error": "Username already exists" }` — duplicate username

---

### POST /login
Authenticates a user and returns a token.

Body (JSON):
```
{
  "username": "string",
  "password": "string"
}
```

Responses:
- 200: `{ "id": number, "token": "string", "role": "admin" | "user" }`
- 401: `{ "error": "Invalid username or password" }`

Note: the token format is `token-<userId>-<username>`.

---

## Authorization

All endpoints below (except register/login) require an `authorization` header containing the token.

Rules:
- A regular `user` can only access/modify projects and tasks that belong to them (owner_id matches their own id).
- An `admin` can access/modify any project or task, regardless of owner.
- Missing or invalid token → 401.
- Valid token but no permission for this specific resource → 403.
- Fields like `owner_id` sent in a request body are ignored on creation — ownership is always derived from the authenticated user, never from client input.

---

## Projects

### POST /projects
Creates a new project, owned by the requesting user.

Headers: `authorization: <token>`

Body (JSON):
```
{ "name": "string (required)" }
```

Responses:
- 201: `{ "id": number, "name": "string", "owner_id": number }`
- 400: `{ "error": "Project name is required" }`

---

### GET /projects
Returns projects. Admin sees all projects; regular user sees only their own.

Headers: `authorization: <token>`

Responses:
- 200: array of project objects

---

### GET /projects/:id
Returns a single project by id.

Headers: `authorization: <token>`

Responses:
- 200: project object
- 403: `{ "error": "Access denied" }` — not owner and not admin
- 404: `{ "error": "Project not found" }`

---

### DELETE /projects/:id
Deletes a project and all its tasks. Only the owner or an admin can do this. Idempotent: deleting an already-deleted project returns 404, not an error.

Headers: `authorization: <token>`

Responses:
- 200: `{ "message": "Project deleted successfully" }`
- 403: `{ "error": "Access denied" }`
- 404: `{ "error": "Project not found" }`

---

## Tasks

### POST /projects/:id/tasks
Adds a new task to a specific project. Only the project owner or an admin can do this.

Headers: `authorization: <token>`

Body (JSON):
```
{ "title": "string (required)" }
```

Responses:
- 201: `{ "id": number, "project_id": number, "title": "string", "status": "pending" }`
- 400: `{ "error": "Title is required" }`
- 403: `{ "error": "Access denied" }`
- 404: `{ "error": "Project not found" }`

---

### GET /projects/:id/tasks
Returns all tasks belonging to a specific project.

Headers: `authorization: <token>`

Responses:
- 200: array of task objects
- 403: `{ "error": "Access denied" }`
- 404: `{ "error": "Project not found" }`

---

### GET /tasks
Returns all tasks across all of the user's own projects (or all projects, if admin). Supports optional filtering by status.

Headers: `authorization: <token>`

Query parameters (optional):
- `status`: filters tasks to only this status value (e.g. `?status=done`)

Example: `GET /tasks?status=done`

Responses:
- 200: array of task objects (filtered by status if provided)

---

### PUT /tasks/:id
Updates a task's title and/or status. Only the owner of the parent project or an admin can do this. Supports partial updates — sending only `title` leaves `status` unchanged, and vice versa. If the task's parent project was already deleted, the task is gone too.

Note: this endpoint does NOT require the project id in the URL — the task's own id is enough, since the server looks up the parent project internally.

Headers: `authorization: <token>`

Body (JSON, both fields optional):
```
{
  "title": "string",
  "status": "string"
}
```

Responses:
- 200: `{ "id": number, "title": "string", "status": "string" }`
- 403: `{ "error": "Access denied" }`
- 404: `{ "error": "Task not found" }`

---

## Cleanup helper (testing only)

### DELETE /users/:id
Deletes a user along with all of their projects and tasks. This endpoint has no auth check — it exists only to clean up test data, and should never exist in a real production system.

Responses:
- 200: `{ "message": "User deleted successfully" }`

---

## Known Issues

1. **Public registration can create admin accounts.** `POST /register` accepts a `role` field with no restriction — anyone can self-register as `admin`, with no approval process.

2. **No validation on task status values.** `PUT /tasks/:id` accepts any string as `status`, with no whitelist of allowed values (e.g. pending/in-progress/done).

3. **Missing request body causes a server crash, not a clean error.** `POST /projects` with no request body at all returns `500 Internal Server Error` instead of the expected `400 Bad Request`.

4. **Wrong Content-Type causes the same crash.** Sending a request with `Content-Type: text/plain` (so the body is never parsed as JSON) triggers the same `500` crash as a missing body.
