import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';

export default function Signup() {
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      await api.signup(
        formData.first_name,
        formData.last_name,
        formData.email,
        formData.password
      );

      setSuccess('Registration successful! Please wait for admin approval.');
      setTimeout(() => {
        navigate('/login');
      }, 3000);

    } catch (err) {
      setError(err.message || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="glass-card">
        <h2>Create an Account</h2>
        <p className="subtitle">Join our platform today</p>

        {error && <div className="error-alert">{error}</div>}
        {success && <div className="success-alert">{success}</div>}

        <form onSubmit={handleSignup} className="auth-form">
          <div className="input-group-row">
            <div className="input-group">
              <label>First Name</label>
              <input
                type="text"
                name="first_name"
                required
                value={formData.first_name}
                onChange={handleChange}
                placeholder="John"
              />
            </div>
            <div className="input-group">
              <label>Last Name</label>
              <input
                type="text"
                name="last_name"
                required
                value={formData.last_name}
                onChange={handleChange}
                placeholder="Doe"
              />
            </div>
          </div>

          <div className="input-group">
            <label>Email</label>
            <input
              type="email"
              name="email"
              required
              value={formData.email}
              onChange={handleChange}
              placeholder="john@example.com"
            />
          </div>
          <div className="input-group">
            <label>Password</label>
            <input
              type="password"
              name="password"
              required
              value={formData.password}
              onChange={handleChange}
              placeholder="Create a strong password"
            />
          </div>

          {loading ? (
            <div className="auth-loader-container">
              <div className="circle-loader"></div>
            </div>
          ) : (
            <button type="submit" className="primary-btn" disabled={success}>
              Sign Up
            </button>
          )}
        </form>

        <p className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
