import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { login as apiLogin, logout as apiLogout, getMe } from '../api/auth';
import { setAccessToken, setRefreshToken, clearAccessToken } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // On mount, there is no in-memory refresh token (page just loaded).
    // Skip the refresh attempt — user will log in normally.
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const data = await apiLogin(email, password);
    setAccessToken(data.access_token);
    if (data.refresh_token) setRefreshToken(data.refresh_token);
    const me = await getMe();
    setUser(me);
    return me;
  };

  const logout = async () => {
    try {
      await apiLogout();
    } finally {
      clearAccessToken();
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
