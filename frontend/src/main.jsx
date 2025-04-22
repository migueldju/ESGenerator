// frontend/src/main.jsx - Updated with ConversationProvider
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ConversationProvider } from './contexts/conversationContext' // Changed from ConversationContext
import { DocumentProvider } from './contexts/DocumentContext'
import App from './app.jsx'
import './styles/index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <ConversationProvider>
          <DocumentProvider>
            <App />
          </DocumentProvider>
        </ConversationProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
)