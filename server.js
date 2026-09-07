const express = require('express');
const Database = require('better-sqlite3');

const app = express();
app.use(express.json());

app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', '*');
  res.header('Access-Control-Allow-Methods', '*');
  next();
});

const db = new Database('projects.db');

db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user'
  )
`);

db.exec(`
  CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    owner_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id)
  )
`);

db.exec(`
  CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
  )
`);

// הרשמה - role ברירת מחדל הוא 'user', אלא אם מציינים אחרת
app.post('/register', (req, res) => {
  const { username, password, role } = req.body;
  if (!username || !password) {
    return res.status(400).json({ error: 'username and password are required' });
  }
  const userRole = role === 'admin' ? 'admin' : 'user';
  try {
    db.prepare('INSERT INTO users (username, password, role) VALUES (?, ?, ?)').run(username, password, userRole);
    res.status(201).json({ message: 'User created successfully' });
  } catch (e) {
    res.status(400).json({ error: 'Username already exists' });
  }
});

// התחברות
app.post('/login', (req, res) => {
  const { username, password } = req.body;
  const user = db.prepare('SELECT * FROM users WHERE username = ? AND password = ?').get(username, password);
  if (!user) {
    return res.status(401).json({ error: 'Invalid username or password' });
  }
  res.json({ id: user.id, token: `token-${user.id}-${username}`, role: user.role });
});

// middleware לבדיקת token, ומזהה את המשתמש
function auth(req, res, next) {
  const token = req.headers['authorization'];
  if (!token) {
    return res.status(401).json({ error: 'Token required' });
  }
  // הטוקן בפורמט: token-<id>-<username>
  const parts = token.split('-');
  const userId = parseInt(parts[1]);
  const user = db.prepare('SELECT * FROM users WHERE id = ?').get(userId);
  if (!user) {
    return res.status(401).json({ error: 'Invalid token' });
  }
  req.user = user;
  next();
}

// POST - יצירת פרויקט חדש
app.post('/projects', auth, (req, res) => {
  const { name } = req.body;
  if (!name || !name.trim()) {
    return res.status(400).json({ error: 'Project name is required' });
  }
  const result = db.prepare('INSERT INTO projects (name, owner_id) VALUES (?, ?)').run(name, req.user.id);
  res.status(201).json({ id: result.lastInsertRowid, name, owner_id: req.user.id });
});

// GET - כל הפרויקטים: admin רואה הכל, user רואה רק את שלו
app.get('/projects', auth, (req, res) => {
  let projects;
  if (req.user.role === 'admin') {
    projects = db.prepare('SELECT * FROM projects').all();
  } else {
    projects = db.prepare('SELECT * FROM projects WHERE owner_id = ?').all(req.user.id);
  }
  res.json(projects);
});

// GET - פרויקט ספציפי לפי id
app.get('/projects/:id', auth, (req, res) => {
  const { id } = req.params;
  const project = db.prepare('SELECT * FROM projects WHERE id = ?').get(id);
  if (!project) {
    return res.status(404).json({ error: 'Project not found' });
  }
  if (req.user.role !== 'admin' && project.owner_id !== req.user.id) {
    return res.status(403).json({ error: 'Access denied' });
  }
  res.json(project);
});

// DELETE - מחיקת פרויקט: רק הבעלים או admin
app.delete('/projects/:id', auth, (req, res) => {
  const { id } = req.params;
  const project = db.prepare('SELECT * FROM projects WHERE id = ?').get(id);
  if (!project) {
    return res.status(404).json({ error: 'Project not found' });
  }
  if (req.user.role !== 'admin' && project.owner_id !== req.user.id) {
    return res.status(403).json({ error: 'Access denied' });
  }
  db.prepare('DELETE FROM tasks WHERE project_id = ?').run(id);
  db.prepare('DELETE FROM projects WHERE id = ?').run(id);
  res.json({ message: 'Project deleted successfully' });
});

// POST - הוספת משימה לפרויקט ספציפי
app.post('/projects/:id/tasks', auth, (req, res) => {
  const { id } = req.params;
  const { title } = req.body;
  const project = db.prepare('SELECT * FROM projects WHERE id = ?').get(id);
  if (!project) {
    return res.status(404).json({ error: 'Project not found' });
  }
  if (req.user.role !== 'admin' && project.owner_id !== req.user.id) {
    return res.status(403).json({ error: 'Access denied' });
  }
  if (!title || !title.trim()) {
    return res.status(400).json({ error: 'Title is required' });
  }
  const result = db.prepare('INSERT INTO tasks (project_id, title) VALUES (?, ?)').run(id, title);
  res.status(201).json({ id: result.lastInsertRowid, project_id: parseInt(id), title, status: 'pending' });
});

// GET - כל המשימות בפרויקט ספציפי
app.get('/projects/:id/tasks', auth, (req, res) => {
  const { id } = req.params;
  const project = db.prepare('SELECT * FROM projects WHERE id = ?').get(id);
  if (!project) {
    return res.status(404).json({ error: 'Project not found' });
  }
  if (req.user.role !== 'admin' && project.owner_id !== req.user.id) {
    return res.status(403).json({ error: 'Access denied' });
  }
  const tasks = db.prepare('SELECT * FROM tasks WHERE project_id = ?').all(id);
  res.json(tasks);
});

// GET - כל המשימות שלי (בכל הפרויקטים שלי), עם סינון אופציונלי לפי status
app.get('/tasks', auth, (req, res) => {
  const { status } = req.query;
  let myProjectIds;
  if (req.user.role === 'admin') {
    myProjectIds = db.prepare('SELECT id FROM projects').all().map(p => p.id);
  } else {
    myProjectIds = db.prepare('SELECT id FROM projects WHERE owner_id = ?').all(req.user.id).map(p => p.id);
  }
  if (myProjectIds.length === 0) {
    return res.json([]);
  }
  const placeholders = myProjectIds.map(() => '?').join(',');
  let query = `SELECT * FROM tasks WHERE project_id IN (${placeholders})`;
  const params = [...myProjectIds];
  if (status) {
    query += ' AND status = ?';
    params.push(status);
  }
  const tasks = db.prepare(query).all(...params);
  res.json(tasks);
});

// PUT - עדכון משימה
app.put('/tasks/:id', auth, (req, res) => {
  const { id } = req.params;
  const { title, status } = req.body;
  const task = db.prepare('SELECT * FROM tasks WHERE id = ?').get(id);
  if (!task) {
    return res.status(404).json({ error: 'Task not found' });
  }
  const project = db.prepare('SELECT * FROM projects WHERE id = ?').get(task.project_id);
  if (req.user.role !== 'admin' && project.owner_id !== req.user.id) {
    return res.status(403).json({ error: 'Access denied' });
  }
  db.prepare('UPDATE tasks SET title = ?, status = ? WHERE id = ?')
    .run(title || task.title, status || task.status, id);
  res.json({ id, title: title || task.title, status: status || task.status });
});

app.delete('/users/:id', (req, res) => {
  const { id } = req.params;
  const userProjects = db.prepare('SELECT id FROM projects WHERE owner_id = ?').all(id);
  userProjects.forEach(project => {
    db.prepare('DELETE FROM tasks WHERE project_id = ?').run(project.id);
  });
  db.prepare('DELETE FROM projects WHERE owner_id = ?').run(id);
  db.prepare('DELETE FROM users WHERE id = ?').run(id);
  res.json({ message: 'User deleted successfully' });
});

app.listen(3000, () => {
  console.log('Server is running on http://localhost:3000');
});