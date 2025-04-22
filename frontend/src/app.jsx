// frontend/src/App.jsx
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ChatView from './components/ChatView';
import EditorView from './components/EditorView';
import ResetPassword from './components/auth/ResetPassword';
import ProtectedRoute from './components/ProtectedRoute';
import './styles/App.css';

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<ChatView />} />
        <Route path="/editor" element={
          <ProtectedRoute>
            <EditorView />
          </ProtectedRoute>
        } />
        <Route path="/reset-password/:token" element={<ResetPassword />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;