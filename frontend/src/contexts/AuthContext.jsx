// frontend/src/contexts/AuthContext.js
import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Check if user is already logged in
    const checkAuthStatus = async () => {
      try {
        const token = localStorage.getItem('token');
        if (token) {
          // Configure axios to send the token with requests
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          
          const response = await axios.get('/api/check-auth');
          if (response.data.authenticated) {
            setUser(response.data.user);
          } else {
            // Token is invalid or expired
            localStorage.removeItem('token');
            delete axios.defaults.headers.common['Authorization'];
          }
        }
      } catch (err) {
        console.error('Auth check error:', err);
        localStorage.removeItem('token');
      } finally {
        setLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  const login = async (email, password) => {
    try {
      setError(null);
      const response = await axios.post('/api/login', { email, password });
      const { token, user } = response.data;
      
      // Save token to localStorage
      localStorage.setItem('token', token);
      
      // Configure axios for future requests
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      setUser(user);
      return true;
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed');
      return false;
    }
  };

  const register = async (username, email, password) => {
    try {
      setError(null);
      const response = await axios.post('/api/register', { username, email, password });
      return { success: true, message: response.data.message };
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed');
      return { success: false, message: err.response?.data?.error || 'Registration failed' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  const forgotPassword = async (email) => {
    try {
      setError(null);
      const response = await axios.post('/api/forgot-password', { email });
      return { success: true, message: response.data.message };
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to send reset email');
      return { success: false, message: err.response?.data?.error || 'Failed to send reset email' };
    }
  };

  const resetPassword = async (token, password) => {
    try {
      setError(null);
      const response = await axios.post(`/api/reset-password/${token}`, { password });
      return { success: true, message: response.data.message };
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to reset password');
      return { success: false, message: err.response?.data?.error || 'Failed to reset password' };
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        error,
        login,
        register,
        logout,
        forgotPassword,
        resetPassword,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

export default AuthContext;