import React from 'react';
import { Navigate } from 'react-router-dom';
import { authService } from '../services/auth';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

/**
 * Protected route component that redirects to login if user is not authenticated.
 */
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const isAuthenticated = authService.isAuthenticated();

  if (!isAuthenticated) {
    // Redirect to login page if not authenticated
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
