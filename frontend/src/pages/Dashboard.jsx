import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

export default function Dashboard() {
  const [role, setRole] = useState(localStorage.getItem('role'));
  const [pendingUsers, setPendingUsers] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    if (role === 'Admin') {
      fetchAdminData();
    } else {
      setLoading(false);
    }
  }, [role, navigate]);

  const fetchAdminData = async () => {
    try {
      setLoading(true);
      const pending = await api.getPendingUsers();
      const all = await api.getAllUsers();
      setPendingUsers(pending);
      // Filter out admins from suspendable users list if desired, but for now we list all
      setAllUsers(all.filter(u => u.is_approved));
    } catch (err) {
      if (err.message.includes('403') || err.message.includes('permissions')) {
        setRole('User');
        localStorage.setItem('role', 'User');
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch (err) {
      console.error('Logout error', err);
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('role');
      navigate('/login');
    }
  };

  const handleApprove = async (userId) => {
    try {
      await api.approveUser(userId);
      fetchAdminData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleSuspend = async (userId) => {
    try {
      await api.suspendUser(userId);
      fetchAdminData();
    } catch (err) {
      alert(err.message);
    }
  };

  if (loading) return <div className="loading">Loading dashboard...</div>;

  return (
    <div className="dashboard-container">
      <nav className="navbar">
        <h2>{role === 'Admin' ? 'Admin Portal' : 'User Portal'}</h2>
        <button onClick={handleLogout} className="logout-btn">Logout</button>
      </nav>

      <main className="dashboard-content">
        {error && <div className="error-alert">{error}</div>}

        {role === 'User' ? (
          <div className="empty-state">
            <h3>Welcome to your Dashboard</h3>
            <p>You have successfully logged in. Your account is active.</p>
          </div>
        ) : (
          <div className="admin-grid">
            <section className="admin-section">
              <h3>Pending Approvals</h3>
              {pendingUsers.length === 0 ? (
                <p className="no-data">No pending requests.</p>
              ) : (
                <ul className="user-list">
                  {pendingUsers.map(user => (
                    <li key={user.id} className="user-card">
                      <div className="user-info">
                        <strong>{user.first_name} {user.last_name}</strong>
                        <span>{user.email}</span>
                      </div>
                      <button onClick={() => handleApprove(user.id)} className="approve-btn">
                        Approve
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="admin-section">
              <h3>Active Users</h3>
              {allUsers.length === 0 ? (
                <p className="no-data">No active users.</p>
              ) : (
                <ul className="user-list">
                  {allUsers.map(user => (
                    <li key={user.id} className="user-card">
                      <div className="user-info">
                        <strong>{user.first_name} {user.last_name}</strong>
                        <span>{user.email}</span>
                        <span className="role-badge">{user.role}</span>
                      </div>
                      {user.role !== 'Admin' && (
                        <button onClick={() => handleSuspend(user.id)} className="suspend-btn">
                          Suspend
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
