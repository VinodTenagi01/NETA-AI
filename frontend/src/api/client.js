import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL ?? '';

// In-memory tokens — never written to localStorage (XSS cannot steal them)
let _accessToken = null;
let _refreshToken = null;

export function setAccessToken(token) { _accessToken = token; }
export function getAccessToken() { return _accessToken; }
export function setRefreshToken(token) { _refreshToken = token; }
export function getRefreshToken() { return _refreshToken; }

export function clearAccessToken() {
  _accessToken = null;
  _refreshToken = null;
  try { delete client.defaults.headers.common.Authorization; } catch (_) { /* no-op */ }
}

const client = axios.create({
  baseURL: `${API_BASE}/api`,
  timeout: 15000,
  withCredentials: true, // always send httpOnly refresh cookie
});

// ── Request interceptor: attach in-memory access token ───────────────────────
client.interceptors.request.use(config => {
  // Ensure headers object always exists before writing
  config.headers = config.headers ?? {};
  if (_accessToken) {
    config.headers.Authorization = `Bearer ${_accessToken}`;
  }
  return config;
});

// ── Response interceptor: 401 → cookie-based refresh → retry ─────────────────
let isRefreshing = false;
let failedQueue = [];

function processQueue(error, token = null) {
  failedQueue.forEach(({ resolve, reject }) =>
    error ? reject(error) : resolve(token)
  );
  failedQueue = [];
}

client.interceptors.response.use(
  res => res,
  async error => {
    const original = error.config ?? {};
    const url = original.url ?? '';

    // ── Pass-through conditions (do NOT attempt a refresh) ──────────────────
    // 1. Not a 401
    // 2. Already retried this request
    // 3. Auth credential endpoints — their 401s mean wrong password / bad token,
    //    NOT an expired session; passing them through lets callers show the error.
    const isCredentialEndpoint = /\/auth\/(login|change-password)\b/.test(url);
    if (
      error.response?.status !== 401 ||
      original._retry ||
      isCredentialEndpoint
    ) {
      return Promise.reject(error);
    }

    // ── Queue concurrent requests while a refresh is in flight ──────────────
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then(token => {
        original.headers = { ...(original.headers ?? {}), Authorization: `Bearer ${token}` };
        return client(original);
      }).catch(err => Promise.reject(err));
    }

    original._retry = true;
    isRefreshing = true;

    try {
      // Use raw axios (not `client`) to avoid infinite interceptor recursion.
      const storedRefresh = getRefreshToken();
      if (!storedRefresh) throw new Error('no refresh token');
      const res = await axios.post(`${API_BASE}/api/auth/refresh`, { refresh_token: storedRefresh }, {
        withCredentials: true,
      });
      const { access_token } = res.data;
      setAccessToken(access_token);
      processQueue(null, access_token);
      original.headers = { ...(original.headers ?? {}), Authorization: `Bearer ${access_token}` };
      return client(original);
    } catch (refreshError) {
      processQueue(refreshError);
      clearAccessToken();
      window.location.href = '/login';
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export default client;
