import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import api from '../api/auth';
import type { UserResponse, LoginRequest, UserCreate, UserRole } from '../types';

interface AuthContextType {
  user: UserResponse | null;
  loading: boolean;
  role: UserRole | null;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: UserCreate) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const role = user?.role || null;

  // Fetch current user on startup if token exists
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchCurrentUser = async () => {
    try {
      const response = await api.getMe();
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch current user:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials: LoginRequest) => {
    const response = await api.login(credentials);
    const { access_token, refresh_token } = response.data;
    
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    
    // Fetch user after login
    await fetchCurrentUser();
  };

  const register = async (data: UserCreate) => {
    await api.register(data);
    // After registration, automatically login
    await login({ email: data.email, password: data.password });
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider value={{ user, loading, role, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
