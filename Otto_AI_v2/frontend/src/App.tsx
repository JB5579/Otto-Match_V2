import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './app/contexts/AuthContext';
import { ComparisonProvider } from './context/ComparisonContext';
import ComparisonFab from './components/comparison/ComparisonFab';
import ComparisonView from './components/comparison/ComparisonView';
import { ProtectedRoute } from './app/components/ProtectedRoute';
import { HomePage } from './app/pages/HomePage';
import { LoginForm } from './app/components/auth/LoginForm';
import { SignUpForm } from './app/components/auth/SignUpForm';
import { AuthCallback } from './app/components/auth/AuthCallback';

/**
 * Story 3-6: Vehicle Comparison Tools
 * - ComparisonProvider: Global comparison state management
 * - ComparisonFab: Floating action button for comparison access
 * - ComparisonView: Modal for side-by-side comparison display
 */
function App() {
  return (
    <React.StrictMode>
      <BrowserRouter>
        <AuthProvider>
          <ComparisonProvider>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/login" element={<LoginForm />} />
              <Route path="/signup" element={<SignUpForm />} />
              <Route path="/auth/callback" element={<AuthCallback />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>

            {/* Story 3-6: Comparison UI Components */}
            <ComparisonFab />
            <ComparisonView />
          </ComparisonProvider>
        </AuthProvider>
      </BrowserRouter>
    </React.StrictMode>
  );
}

export default App;
