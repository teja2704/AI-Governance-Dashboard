// api.js — single place all backend calls go through.
// Handles: attaching JWT, base URL, JSON parsing, consistent error shape.

const TOKEN_KEY = 'gd_access_token';

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function isLoggedIn() {
  return !!getToken();
}

/**
 * Core request helper.
 * @param {string} path - e.g. '/auth/login'
 * @param {object} options - { method, body, auth }
 *   auth: true (default) attaches Authorization header if a token exists
 */
async function apiRequest(path, { method = 'GET', body, auth = true, timeoutMs = 15000 } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (auth && getToken()) {
    headers['Authorization'] = `Bearer ${getToken()}`;
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  let response;
  try {
    response = await fetch(`${window.API_BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeout);
    if (err.name === 'AbortError') {
      throw new ApiError('Request timed out. Please try again.', 0);
    }
    throw new ApiError('Could not reach the server. Check your connection.', 0);
  }
  clearTimeout(timeout);

  // Session expired / invalid token — force back to login
  if (response.status === 401 && auth) {
    clearToken();
    window.location.href = '/login.html';
    throw new ApiError('Session expired. Please log in again.', 401);
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    // No JSON body — fine for some responses
  }

  if (!response.ok) {
    const message = (data && (data.detail || data.message)) || `Request failed (${response.status})`;
    throw new ApiError(message, response.status);
  }

  return data;
}

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

const api = {
  get: (path, opts) => apiRequest(path, { ...opts, method: 'GET' }),
  post: (path, body, opts) => apiRequest(path, { ...opts, method: 'POST', body }),
};
