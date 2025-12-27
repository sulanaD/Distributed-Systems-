import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (data) => api.post('/api/auth/register', data),
  login: (data) => api.post('/api/auth/login', data),
  logout: () => api.post('/api/auth/logout'),
};

export const accountsAPI = {
  getAccounts: () => api.get('/api/accounts/'),
  createAccount: (data) => api.post('/api/accounts/', data),
  getAccount: (accountNumber) => api.get(`/api/accounts/${accountNumber}`),
  getBalance: (accountNumber) => api.get(`/api/accounts/${accountNumber}/balance`),
  deleteAccount: (accountNumber) => api.delete(`/api/accounts/${accountNumber}`),
};

export const transfersAPI = {
  createTransfer: (data) => api.post('/api/transfers/', data),
  getHistory: (limit = 50) => api.get(`/api/transfers/history?limit=${limit}`),
};

export const taxAPI = {
  calculate: (data) => api.post('/api/tax/calculate', data),
  getHistory: (limit = 10) => api.get(`/api/tax/history?limit=${limit}`),
  getBrackets: () => api.get('/api/tax/brackets'),
};

export default api;
