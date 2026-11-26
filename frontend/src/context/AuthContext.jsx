import { createContext, useContext, useState } from 'react';
import api from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('cognis_user');
    return saved ? JSON.parse(saved) : null;
  });

  const applySession = (data) => {
    localStorage.setItem('cognis_token', data.access_token);
    const profile = { user_id: data.user_id, full_name: data.full_name, role: data.role };
    localStorage.setItem('cognis_user', JSON.stringify(profile));
    setUser(profile);
    return profile;
  };

  const login = async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password });
    return applySession(data);
  };

  const loginWithOtp = async (email, otp_code) => {
    const { data } = await api.post('/auth/login-otp', { email, otp_code });
    return applySession(data);
  };

  const verifyEmailOtp = async (email, otp_code) => {
    const { data } = await api.post('/auth/verify-email', { email, otp_code });
    return applySession(data);
  };

  const logout = () => {
    localStorage.removeItem('cognis_token');
    localStorage.removeItem('cognis_user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, loginWithOtp, verifyEmailOtp, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
