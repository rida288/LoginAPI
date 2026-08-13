const API_URL = 'http://localhost:8000';

const request = async (endpoint, options = {}) => {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  };

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Something went wrong');
  }
  return data;
};

export const api = {
  login: (email, password) =>
    request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  signup: (first_name, last_name, email, password) =>
    request('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ first_name, last_name, email, password }),
    }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  getPendingUsers: () => request('/admin/users/pending', { method: 'GET' }),
  getAllUsers: () => request('/admin/users', { method: 'GET' }),
  approveUser: (userId) =>
    request(`/admin/users/${userId}/approve`, { method: 'PUT' }),
  suspendUser: (userId) =>
    request(`/admin/users/${userId}/suspend`, { method: 'PUT' }),
  getProtected: () => request('/protected', { method: 'GET' }),
};
