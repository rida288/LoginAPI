const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const request = async (endpoint, options = {}) => {
  const token = localStorage.getItem('token');
  const headers = {
    ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
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

  // Admin — user management
  getPendingUsers: () => request('/admin/users/pending', { method: 'GET' }),
  getAllUsers: () => request('/admin/users', { method: 'GET' }),
  approveUser: (userId) => request(`/admin/users/${userId}/approve`, { method: 'PUT' }),
  suspendUser: (userId) => request(`/admin/users/${userId}/suspend`, { method: 'PUT' }),
  adminCreateUser: (data) =>
    request('/admin/users', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  editUser: (userId, data) =>
    request(`/admin/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify({ id: userId, ...data }),
    }),
  deleteUser: (userId) => request(`/admin/users/${userId}`, { method: 'DELETE' }),

  // Projects
  getProjects: () => request('/projects', { method: 'GET' }),
  getAllProjects: () => request('/projects/all', { method: 'GET' }),
  createProject: (formData) =>
    request('/projects', {
      method: 'POST',
      body: formData,
    }),
  getProjectData: (projectId) => request(`/projects/${projectId}/data`, { method: 'GET' }),
  deleteProject: (projectId) => request(`/projects/${projectId}`, { method: 'DELETE' }),

  getProtected: () => request('/protected', { method: 'GET' }),
};
