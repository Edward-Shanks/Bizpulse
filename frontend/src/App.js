import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import axios from 'axios';
import '@/App.css';
import Login from '@/pages/Login';
import LoginVariations from '@/pages/LoginVariations';
import DashboardNew from '@/pages/DashboardNew';
import CustomerAnalysisNew from '@/pages/CustomerAnalysisNew';
import CustomerInsights from '@/pages/CustomerInsights';
import BrandAnalysisNew from '@/pages/BrandAnalysisNew';
import CategoryAnalysisNew from '@/pages/CategoryAnalysisNew';
import Reports from '@/pages/Reports';
import CockpitNew from '@/pages/CockpitNew';
import ProjectsNew from '@/pages/ProjectsNew';
import StrategicDeployment from '@/pages/StrategicDeployment';
import SalesAnalysis from '@/pages/SalesAnalysis';
import RootCauseAnalysis from '@/pages/RootCauseAnalysis';
import ChartInsight from '@/pages/ChartInsight';
import Kanban from '@/pages/Kanban';
import Signup from '@/pages/Signup';
import ForgotPassword from '@/pages/ForgotPassword';
import UserManagement from '@/pages/UserManagement';
import { Toaster } from '@/components/ui/sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
export const API = `${BACKEND_URL}/api`;

// Check if in development mode
// Note: NODE_ENV is set by Create React App build scripts, not from .env
// We check multiple conditions to ensure development mode is detected
// ALWAYS enable on localhost for easier development
const isDevelopment = (() => {
  // Primary check: REACT_APP_ENVIRONMENT from .env
  if (process.env.REACT_APP_ENVIRONMENT === 'development') {
    return true;
  }
  // Secondary check: NODE_ENV (set automatically by npm start)
  if (process.env.NODE_ENV === 'development') {
    return true;
  }
  // Fallback: ALWAYS enable on localhost (most reliable for development)
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname.includes('localhost')) {
      return true;
    }
  }
  return false;
})();

// Debug log - always show in console
console.log('🔧 Environment Check:');
console.log('  NODE_ENV:', process.env.NODE_ENV);
console.log('  REACT_APP_ENVIRONMENT:', process.env.REACT_APP_ENVIRONMENT);
console.log('  Hostname:', typeof window !== 'undefined' ? window.location.hostname : 'N/A');
console.log('  isDevelopment:', isDevelopment);
if (isDevelopment) {
  console.log('✅ Development mode - Signup and User Management routes ENABLED');
  console.log('   Access: /signup and /user-management');
} else {
  console.log('❌ Production mode - Signup and User Management routes DISABLED');
}

// Auth Context
export const AuthContext = React.createContext(null);

export const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => {
    // Check if token exists and is not expired
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      try {
        // Basic check - decode without verification to check expiration
        const payload = JSON.parse(atob(storedToken.split('.')[1]));
        const exp = payload.exp * 1000; // Convert to milliseconds
        if (exp < Date.now()) {
          // Token expired - but don't remove it, we can try to refresh it
          // Only remove if refresh fails
          return storedToken; // Keep it for refresh attempt
        }
      } catch (e) {
        // Invalid token format
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        return null;
      }
    }
    return storedToken;
  });
  const [user, setUser] = useState(localStorage.getItem('user'));
  const [isRefreshing, setIsRefreshing] = useState(false);
  const refreshPromiseRef = React.useRef(null);
  const refreshTokenRef = React.useRef(null);

  const login = React.useCallback((newToken, email) => {
    localStorage.setItem('token', newToken);
    localStorage.setItem('user', email);
    setToken(newToken);
    setUser(email);
  }, []);

  const logout = React.useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  }, []);

  const refreshToken = React.useCallback(async () => {
    // If already refreshing, return the existing promise
    if (refreshPromiseRef.current) {
      return refreshPromiseRef.current;
    }

    const currentToken = localStorage.getItem('token');
    if (!currentToken) {
      throw new Error('No token to refresh');
    }

    setIsRefreshing(true);
    const refreshPromise = axios
      .post(`${API}/auth/refresh`, { token: currentToken })
      .then((response) => {
        const newToken = response.data.token;
        const email = response.data.email;
        login(newToken, email);
        refreshPromiseRef.current = null;
        setIsRefreshing(false);
        return newToken;
      })
      .catch((error) => {
        refreshPromiseRef.current = null;
        setIsRefreshing(false);
        // If refresh fails, logout user
        logout();
        // Redirect to login if we're in the browser
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        throw error;
      });

    refreshPromiseRef.current = refreshPromise;
    return refreshPromise;
  }, [login, logout]);

  // Store refreshToken in ref so interceptors can access it
  React.useEffect(() => {
    refreshTokenRef.current = refreshToken;
  }, [refreshToken]);

  // Set up axios interceptor for automatic token refresh
  React.useEffect(() => {
    // Request interceptor - add token to all requests
    const requestInterceptor = axios.interceptors.request.use(
      (config) => {
        const currentToken = localStorage.getItem('token');
        if (currentToken && config.headers) {
          config.headers.Authorization = `Bearer ${currentToken}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - handle 401 errors and refresh token
    const responseInterceptor = axios.interceptors.response.use(
      (response) => {
        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // If error is 401 and we haven't already tried to refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            // Attempt to refresh the token using ref
            if (refreshTokenRef.current) {
              const newToken = await refreshTokenRef.current();
              
              // Retry the original request with the new token
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              return axios(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed - user will be logged out by refreshToken
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );

    // Cleanup interceptors on unmount
    return () => {
      axios.interceptors.request.eject(requestInterceptor);
      axios.interceptors.response.eject(responseInterceptor);
    };
  }, []); // Empty deps - interceptors only set up once

  // Proactively refresh token if expired on app load
  // This runs after refreshToken and interceptors are set up
  React.useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      try {
        const payload = JSON.parse(atob(storedToken.split('.')[1]));
        const exp = payload.exp * 1000;
        // If token expires in less than 5 minutes, refresh it proactively
        const fiveMinutes = 5 * 60 * 1000;
        if (exp < Date.now() + fiveMinutes) {
          refreshToken().catch(() => {
            // Refresh failed, user will be logged out
          });
        }
      } catch (e) {
        // Invalid token - will be handled by interceptor
      }
    }
  }, [refreshToken]);

  return (
    <AuthContext.Provider value={{ token, user, login, logout, refreshToken, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
};

const PrivateRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/login-variations" element={<LoginVariations />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          {isDevelopment && (
            <Route
              path="/signup"
              element={<Signup />}
            />
          )}
          {isDevelopment && (
            <Route
              path="/user-management"
              element={
                <PrivateRoute>
                  <UserManagement />
                </PrivateRoute>
              }
            />
          )}
          <Route
            path="/"
            element={
              <PrivateRoute>
                <CockpitNew />
              </PrivateRoute>
            }
          />
          <Route
            path="/kanban"
            element={
              <PrivateRoute>
                <Kanban />
              </PrivateRoute>
            }
          />
          <Route
            path="/strategic-deployment"
            element={
              <PrivateRoute>
                <StrategicDeployment />
              </PrivateRoute>
            }
          />
          <Route
            path="/compass"
            element={
              <PrivateRoute>
                <DashboardNew />
              </PrivateRoute>
            }
          />
          <Route
            path="/customers"
            element={
              <PrivateRoute>
                <CustomerAnalysisNew />
              </PrivateRoute>
            }
          />
          <Route
            path="/customer-insights"
            element={
              <PrivateRoute>
                <CustomerInsights />
              </PrivateRoute>
            }
          />
          <Route
            path="/brands"
            element={
              <PrivateRoute>
                <BrandAnalysisNew />
              </PrivateRoute>
            }
          />
          <Route
            path="/categories"
            element={
              <PrivateRoute>
                <CategoryAnalysisNew />
              </PrivateRoute>
            }
          />
          <Route
            path="/reports"
            element={
              <PrivateRoute>
                <Reports />
              </PrivateRoute>
            }
          />
          <Route
            path="/projects"
            element={
              <PrivateRoute>
                <ProjectsNew />
              </PrivateRoute>
            }
          />
          <Route
            path="/sales-analysis"
            element={
              <PrivateRoute>
                <SalesAnalysis />
              </PrivateRoute>
            }
          />
          <Route
            path="/root-cause-analysis"
            element={
              <PrivateRoute>
                <RootCauseAnalysis />
              </PrivateRoute>
            }
          />
          <Route
            path="/chart-insight"
            element={
              <PrivateRoute>
                <ChartInsight />
              </PrivateRoute>
            }
          />
        </Routes>
        <Toaster position="top-right" />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;