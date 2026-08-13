import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import { jwtDecode } from 'jwt-decode';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await api.login(email, password);
      const token = data.token;

      // We don't have role in token payload right now, but wait, do we?
      // In protectRoute.py, payload has user_id. 
      // Actually, we can fetch /protected to get the user details and role.
      localStorage.setItem('token', token);

      try {
        const userDetails = await api.getProtected();
        // But /protected in main.py just returns a message right now.
        // Wait, main.py /protected returns {"message": f"Hello {user.first_name} {user.last_name}..."}
        // Actually, we should just decode it or maybe we need a /me endpoint?
        // Let's just decode the token to see if role is there. It's not.
        // If we don't know the role, we could try fetching /admin/users/pending.
        // If it returns 403, it's a User. If it succeeds, it's an Admin.

        // Quick role check hack:
        try {
          await api.getPendingUsers();
          localStorage.setItem('role', 'Admin');
        } catch (err) {
          localStorage.setItem('role', 'User');
        }

        navigate('/dashboard');
      } catch (err) {
        setError('Failed to verify user details.');
      }
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="glass-card">
        <h2>Welcome Back</h2>
        <p className="subtitle">Sign in to your account</p>

        {error && <div className="error-alert">{error}</div>}

        <form onSubmit={handleLogin} className="auth-form">
          <div className="input-group">
            <label>Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
            />
          </div>
          <div className="input-group">
            <label>Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
            />
          </div>

          <button type="submit" className="primary-btn" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="auth-footer">
          Don't have an account? <Link to="/signup">Sign up</Link>
        </p>
      </div>
    </div>
  );
}
