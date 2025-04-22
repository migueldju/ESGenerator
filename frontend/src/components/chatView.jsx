import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPaperPlane, faRedo } from '@fortawesome/free-solid-svg-icons';
import { useAuth } from '../contexts/AuthContext';
import { useConversations } from '../contexts/conversationContext';
import AuthButton from './auth/AuthButton';
import axios from 'axios';
import '../styles/chatView.css';

const ChatView = () => {
  const [messages, setMessages] = useState([
    {
      type: 'bot',
      content: `<h2>Welcome to ESGenerator</h2>
                <p>Please provide a detailed description of your company's activities, products, services, and sector to help me determine the applicable ESRS reporting standards.</p>`,
      isWelcome: true
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [companyInfo, setCompanyInfo] = useState({
    initialized: false,
    naceSector: 'Not classified yet',
    esrsSector: 'Not determined yet'
  });
  const [conversationId, setConversationId] = useState(null);

  const chatContainerRef = useRef(null);
  const textareaRef = useRef(null);
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const [placeholderText, setPlaceholder] = useState("Enter your company description...");

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
      
      if (textareaRef.current.scrollHeight > 150) {
        textareaRef.current.style.overflowY = 'scroll';
      } else {
        textareaRef.current.style.overflowY = 'hidden';
      }
    }
  }, [inputValue]);

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage = {
      type: 'user',
      content: inputValue
    };
    
    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue('');
    setIsLoading(true);

    try {
      const data = {
        message: currentInput,
        conversation_id: conversationId
      };

      const response = await axios.post('/api/chat', data);
      const responseData = response.data;

      if (responseData.is_first_message) {
        setCompanyInfo({
          initialized: true,
          naceSector: responseData.nace_sector,
          esrsSector: responseData.esrs_sector
        });
        setConversationId(responseData.conversation_id);
        setPlaceholder("Ask your question here...");
      }

      setMessages(prev => [...prev, { 
        type: 'bot', 
        content: responseData.answer 
      }]);
    } catch (error) {
      console.error('Error:', error);
      
      let errorMessage = "I'm sorry, there was an error processing your request. Please try again.";
      
      if (!isAuthenticated && error.response && error.response.status === 401) {
        errorMessage = "You need to log in to save this conversation. Your session will be lost if you leave or refresh the page.";
      }
      
      setMessages(prev => [...prev, { 
        type: 'bot', 
        content: errorMessage
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    try {
      if (conversationId && isAuthenticated) {
        await axios.delete(`/api/conversations/${conversationId}`);
      }
      
      setMessages([
        {
          type: 'bot',
          content: `<h2>Welcome to ESGenerator</h2>
                    <p>Please provide a detailed description of your company's activities, products, services, and sector to help me determine the applicable ESRS reporting standards.</p>`,
          isWelcome: true
        }
      ]);
      setInputValue('');
      setCompanyInfo({
        initialized: false,
        naceSector: 'Not classified yet',
        esrsSector: 'Not determined yet'
      });
      setConversationId(null);
      setPlaceholder("Enter your company description...");
    } catch (error) {
      console.error('Error resetting chat:', error);
    }
  };

  return (
    <div className="container">
      <div className="top-bar">
        <div className="nav-container">
          <button className="nav-button active">Chat</button>
          <button 
            className="nav-button inactive" 
            onClick={() => navigate('/editor')}
          >
            Editor
          </button>
        </div>
        <AuthButton />
      </div>
      
      <div className="header">
        <h1>ESGenerator</h1>
      </div>
      
      {companyInfo.initialized && (
        <div className="sub-header">
          <div className="sector-info">
            <div className="sector-box">
              <h3>NACE Sector:</h3>
              <p>{companyInfo.naceSector}</p>
            </div>
            <div className="sector-box">
              <h3>Sector-specific Standards:</h3>
              <p>{companyInfo.esrsSector}</p>
            </div>
            <button 
              className="reset-button" 
              title="Start new conversation"
              onClick={handleReset}
            >
              <FontAwesomeIcon icon={faRedo} /> New Chat
            </button>
          </div>
        </div>
      )}
      
      <div className="chat-container" ref={chatContainerRef}>
        {messages.map((message, index) => (
          <div 
            key={index} 
            className={`message ${message.type}-message ${message.isWelcome ? 'welcome-message' : ''}`}
            dangerouslySetInnerHTML={{ __html: message.content }}
          />
        ))}
        
        {isLoading && (
          <div className="message bot-message loading">
            <div className="loading-dots">
              <div className="dot"></div>
              <div className="dot"></div>
              <div className="dot"></div>
            </div>
          </div>
        )}
      </div>
      
      <div className="input-container">
        <textarea
          ref={textareaRef}
          id="user-input"
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholderText}
          rows="1"
        />
        <button 
          id="send-button"
          onClick={handleSendMessage}
        >
          <FontAwesomeIcon icon={faPaperPlane} />
        </button>
      </div>
    </div>
  );
};

export default ChatView;