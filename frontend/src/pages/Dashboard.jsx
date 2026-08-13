import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import SpreadsheetViewer from '../components/SpreadsheetViewer';

const VIEWS = {
  ALL_USERS: 'all',
  PENDING: 'pending',
  MY_PROJECTS: 'my-projects',
  ALL_PROJECTS: 'all-projects'
};

// --- Reusable Modal ---
function Modal({ title, onClose, children }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

// --- Create / Edit User Form ---
function UserForm({ initial = {}, isAdmin = false, onSubmit, loading }) {
  const [form, setForm] = useState({
    first_name: initial.first_name || '',
    last_name: initial.last_name || '',
    email: initial.email || '',
    password: '',
    role: initial.role || 'User',
  });

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  return (
    <form
      className="modal-form"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(form);
      }}
    >
      <div className="input-group-row">
        <div className="input-group">
          <label>First Name</label>
          <input name="first_name" required value={form.first_name} onChange={handleChange} placeholder="First Name" />
        </div>
        <div className="input-group">
          <label>Last Name</label>
          <input name="last_name" required value={form.last_name} onChange={handleChange} placeholder="Last Name" />
        </div>
      </div>
      <div className="input-group">
        <label>Email</label>
        <input name="email" type="email" required value={form.email} onChange={handleChange} placeholder="Email" />
      </div>
      {isAdmin && (
        <>
          <div className="input-group">
            <label>Password</label>
            <input name="password" type="password" required value={form.password} onChange={handleChange} placeholder="Password" />
          </div>
          <div className="input-group">
            <label>Role</label>
            <select name="role" value={form.role} onChange={handleChange} className="select-input">
              <option value="User">User</option>
              <option value="Admin">Admin</option>
            </select>
          </div>
        </>
      )}
      <button type="submit" className="primary-btn" disabled={loading}>
        {loading ? 'Saving...' : 'Save'}
      </button>
    </form>
  );
}

// --- Create Project Form ---
function ProjectForm({ onSubmit, loading }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!file) {
      alert('Please select a CSV or XLSX file');
      return;
    }
    onSubmit({ name, description, file });
  };

  return (
    <form className="modal-form" onSubmit={handleSubmit}>
      <div className="input-group">
        <label>Project Name</label>
        <input required value={name} onChange={(e) => setName(e.target.value)} placeholder="Project Name" />
      </div>
      <div className="input-group">
        <label>Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Short description of the project"
          className="textarea-input"
        />
      </div>
      <div className="input-group">
        <label>Upload File (.csv, .xlsx)</label>
        <input
          type="file"
          accept=".csv, .xlsx"
          required
          onChange={(e) => setFile(e.target.files[0])}
          className="file-input"
        />
      </div>
      <button type="submit" className="primary-btn" disabled={loading}>
        {loading ? 'Creating...' : 'Create Project'}
      </button>
    </form>
  );
}

// --- Projects List Grid ---
function ProjectsView({ projects, onView, onDelete }) {
  if (projects.length === 0) return <p className="no-data">No projects found.</p>;

  return (
    <div className="projects-grid">
      {projects.map((project) => (
        <div key={project.id} className="project-card">
          <div className="project-card-header">
            <span className="project-icon">📁</span>
            <h4>{project.name}</h4>
          </div>
          <p className="project-desc">{project.description || 'No description provided'}</p>
          <div className="project-meta">
            <span className="file-badge">📄 {project.file_name}</span>
            <span className="date-badge">🕒 {new Date(project.created_at).toLocaleDateString()}</span>
          </div>
          <div className="project-card-actions">
            <button className="view-project-btn" onClick={() => onView(project)}>
              Open Spreadsheet
            </button>
            <button className="delete-project-btn" onClick={() => onDelete(project.id)}>
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

// --- All Users Table ---
function AllUsersView({ users, onEdit, onSuspend, onDelete, onApprove }) {
  if (users.length === 0) return <p className="no-data">No users found.</p>;

  return (
    <div className="table-wrapper">
      <table className="user-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.first_name} {user.last_name}</td>
              <td className="muted">{user.email}</td>
              <td><span className="role-badge">{user.role}</span></td>
              <td>
                <span className={`status-badge ${user.is_approved ? 'status-active' : 'status-suspended'}`}>
                  {user.is_approved ? 'Active' : 'Suspended'}
                </span>
              </td>
              <td>
                <div className="action-group">
                  <button className="btn-icon btn-edit" title="Edit" onClick={() => onEdit(user)}>✏️</button>
                  {user.role !== 'Admin' && (
                    <>
                      <button
                        className="btn-icon btn-suspend"
                        title={user.is_approved ? 'Suspend' : 'Approve'}
                        onClick={() => user.is_approved ? onSuspend(user.id) : onApprove(user.id)}
                      >
                        {user.is_approved ? '🔴' : '✅'}
                      </button>
                      <button className="btn-icon btn-delete" title="Delete" onClick={() => onDelete(user.id)}>🗑️</button>
                    </>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// --- Pending Approvals List ---
function PendingView({ users, onApprove }) {
  if (users.length === 0) return <p className="no-data">No pending approval requests.</p>;

  return (
    <ul className="user-list">
      {users.map((user) => (
        <li key={user.id} className="user-card">
          <div className="user-info">
            <strong>{user.first_name} {user.last_name}</strong>
            <span>{user.email}</span>
          </div>
          <button className="approve-btn" onClick={() => onApprove(user.id)}>Approve</button>
        </li>
      ))}
    </ul>
  );
}

// --- Main Dashboard ---
export default function Dashboard() {
  const [role] = useState(localStorage.getItem('role'));
  const [activeView, setActiveView] = useState(role === 'Admin' ? VIEWS.ALL_USERS : VIEWS.MY_PROJECTS);
  const [allUsers, setAllUsers] = useState([]);
  const [pendingUsers, setPendingUsers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [allProjects, setAllProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');

  // Modals / Overlays
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showCreateProjectModal, setShowCreateProjectModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [activeProject, setActiveProject] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    if (!localStorage.getItem('token')) { navigate('/login'); return; }
    if (role === 'Admin') fetchAdminData();
    else fetchUserData();
  }, [role, navigate]);

  const fetchUserData = async () => {
    try {
      setLoading(true);
      const myProjects = await api.getProjects();
      setProjects(myProjects);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchAdminData = async () => {
    try {
      setLoading(true);
      const [all, pending, myProjects, allProjs] = await Promise.all([
        api.getAllUsers(),
        api.getPendingUsers(),
        api.getProjects(),
        api.getAllProjects()
      ]);
      setAllUsers(all);
      setPendingUsers(pending);
      setProjects(myProjects);
      setAllProjects(allProjs);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try { await api.logout(); } catch (e) { console.error(e); }
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    navigate('/login');
  };

  // User Actions
  const handleApprove = async (userId) => {
    try { await api.approveUser(userId); fetchAdminData(); } catch (e) { alert(e.message); }
  };

  const handleSuspend = async (userId) => {
    try { await api.suspendUser(userId); fetchAdminData(); } catch (e) { alert(e.message); }
  };

  const handleDelete = async (userId) => {
    if (!window.confirm('Are you sure you want to permanently delete this user?')) return;
    try { await api.deleteUser(userId); fetchAdminData(); } catch (e) { alert(e.message); }
  };

  const handleCreate = async (form) => {
    setActionLoading(true);
    try {
      await api.adminCreateUser(form);
      setShowCreateModal(false);
      fetchAdminData();
    } catch (e) { alert(e.message); }
    finally { setActionLoading(false); }
  };

  const handleEdit = async (form) => {
    setActionLoading(true);
    try {
      await api.editUser(editingUser.id, form);
      setEditingUser(null);
      fetchAdminData();
    } catch (e) { alert(e.message); }
    finally { setActionLoading(false); }
  };

  // Project Actions
  const handleCreateProject = async ({ name, description, file }) => {
    setActionLoading(true);
    try {
      const formData = new FormData();
      formData.append('name', name);
      if (description) formData.append('description', description);
      formData.append('file', file);

      await api.createProject(formData);
      setShowCreateProjectModal(false);
      if (role === 'Admin') fetchAdminData();
      else fetchUserData();
    } catch (e) {
      alert(e.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteProject = async (projectId) => {
    if (!window.confirm('Are you sure you want to delete this project and its file?')) return;
    try {
      await api.deleteProject(projectId);
      if (role === 'Admin') fetchAdminData();
      else fetchUserData();
    } catch (e) {
      alert(e.message);
    }
  };

  if (loading) return <div className="loading">Loading dashboard...</div>;

  // ---- USER VIEW ----
  if (role !== 'Admin') {
    return (
      <div className="admin-layout">
        <nav className="navbar">
          <h2>User Portal</h2>
          <div className="navbar-actions">
            <button className="create-btn" onClick={() => setShowCreateProjectModal(true)}>+ Create Project</button>
            <button onClick={handleLogout} className="logout-btn">Logout</button>
          </div>
        </nav>

        <div className="admin-body">
          <aside className="sidebar">
            <nav className="sidebar-nav">
              <button
                className={`sidebar-item ${activeView === VIEWS.MY_PROJECTS ? 'active' : ''}`}
                onClick={() => setActiveView(VIEWS.MY_PROJECTS)}
              >
                <span className="sidebar-icon">📁</span> My Projects
                <span className="sidebar-count">{projects.length}</span>
              </button>
            </nav>
          </aside>

          <main className="admin-content">
            {error && <div className="error-alert">{error}</div>}

            <div className="content-header">
              <h3>My Projects</h3>
            </div>

            <ProjectsView
              projects={projects}
              onView={setActiveProject}
              onDelete={handleDeleteProject}
            />
          </main>
        </div>

        {/* Create Project Modal */}
        {showCreateProjectModal && (
          <Modal title="Create New Project" onClose={() => setShowCreateProjectModal(false)}>
            <ProjectForm onSubmit={handleCreateProject} loading={actionLoading} />
          </Modal>
        )}

        {/* Excel spreadsheet overlay */}
        {activeProject && (
          <SpreadsheetViewer project={activeProject} onClose={() => setActiveProject(null)} />
        )}
      </div>
    );
  }

  // ---- ADMIN VIEW ----
  return (
    <div className="admin-layout">
      {/* Top Navbar */}
      <nav className="navbar">
        <h2>Admin Portal</h2>
        <div className="navbar-actions">
          <button className="create-project-nav-btn" onClick={() => setShowCreateProjectModal(true)}>+ Create Project</button>
          <button className="create-btn" onClick={() => setShowCreateModal(true)}>+ Create User</button>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </nav>

      <div className="admin-body">
        {/* Sidebar */}
        <aside className="sidebar">
          <nav className="sidebar-nav">
            <button
              className={`sidebar-item ${activeView === VIEWS.ALL_USERS ? 'active' : ''}`}
              onClick={() => setActiveView(VIEWS.ALL_USERS)}
            >
              <span className="sidebar-icon">👥</span> All Users
              <span className="sidebar-count">{allUsers.length}</span>
            </button>
            <button
              className={`sidebar-item ${activeView === VIEWS.PENDING ? 'active' : ''}`}
              onClick={() => setActiveView(VIEWS.PENDING)}
            >
              <span className="sidebar-icon">🕐</span> Pending
              {pendingUsers.length > 0 && (
                <span className="sidebar-badge">{pendingUsers.length}</span>
              )}
            </button>
            <button
              className={`sidebar-item ${activeView === VIEWS.MY_PROJECTS ? 'active' : ''}`}
              onClick={() => setActiveView(VIEWS.MY_PROJECTS)}
            >
              <span className="sidebar-icon">📁</span> My Projects
              <span className="sidebar-count">{projects.length}</span>
            </button>
            <button
              className={`sidebar-item ${activeView === VIEWS.ALL_PROJECTS ? 'active' : ''}`}
              onClick={() => setActiveView(VIEWS.ALL_PROJECTS)}
            >
              <span className="sidebar-icon">🌎</span> All Projects
              <span className="sidebar-count">{allProjects.length}</span>
            </button>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="admin-content">
          {error && <div className="error-alert">{error}</div>}

          <div className="content-header">
            <h3>
              {activeView === VIEWS.ALL_USERS && 'All Users'}
              {activeView === VIEWS.PENDING && 'Pending Approvals'}
              {activeView === VIEWS.MY_PROJECTS && 'My Projects'}
              {activeView === VIEWS.ALL_PROJECTS && 'All Projects'}
            </h3>
          </div>

          {activeView === VIEWS.ALL_USERS && (
            <AllUsersView
              users={allUsers}
              onEdit={setEditingUser}
              onSuspend={handleSuspend}
              onDelete={handleDelete}
              onApprove={handleApprove}
            />
          )}
          {activeView === VIEWS.PENDING && (
            <PendingView users={pendingUsers} onApprove={handleApprove} />
          )}
          {activeView === VIEWS.MY_PROJECTS && (
            <ProjectsView
              projects={projects}
              onView={setActiveProject}
              onDelete={handleDeleteProject}
            />
          )}
          {activeView === VIEWS.ALL_PROJECTS && (
            <ProjectsView
              projects={allProjects}
              onView={setActiveProject}
              onDelete={handleDeleteProject}
            />
          )}
        </main>
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <Modal title="Create New User" onClose={() => setShowCreateModal(false)}>
          <UserForm isAdmin={true} onSubmit={handleCreate} loading={actionLoading} />
        </Modal>
      )}

      {/* Create Project Modal */}
      {showCreateProjectModal && (
        <Modal title="Create New Project" onClose={() => setShowCreateProjectModal(false)}>
          <ProjectForm onSubmit={handleCreateProject} loading={actionLoading} />
        </Modal>
      )}

      {/* Edit User Modal */}
      {editingUser && (
        <Modal title="Edit User" onClose={() => setEditingUser(null)}>
          <UserForm initial={editingUser} onSubmit={handleEdit} loading={actionLoading} />
        </Modal>
      )}

      {/* Excel spreadsheet overlay */}
      {activeProject && (
        <SpreadsheetViewer project={activeProject} onClose={() => setActiveProject(null)} />
      )}
    </div>
  );
}
