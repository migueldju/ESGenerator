// frontend/src/app.jsx
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ChatView from './components/chatView';
import EditorView from './components/editorView';
import ResetPassword from './components/auth/ResetPassword';
import ProtectedRoute from './components/ProtectedRoute';
import './styles/app.css';

function App() {
  return (
    <Routes>
      <Route path="/" element={<ChatView />} />
      
      {/* The EditorView is protected but allows guest access with a prompt */}
      <Route path="/editor" element={
        <ProtectedRoute>
          <EditorView />
        </ProtectedRoute>
      } />
      
      <Route path="/reset-password/:token" element={<ResetPassword />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;