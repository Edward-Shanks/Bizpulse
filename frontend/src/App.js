import React, { useState, useEffect } from 'react';
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
import { Toaster } from '@/components/ui/sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
export const API = `${BACKEND_URL}/api`;

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
          // Token expired
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          return null;
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

  const login = (newToken, email) => {
    localStorage.setItem('token', newToken);
    localStorage.setItem('user', email);
    setToken(newToken);
    setUser(email);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isAuthenticated: !!token }}>
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
          <Route
            path="/signup"
            element={
              <PrivateRoute>
                <Signup />
              </PrivateRoute>
            }
          />
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