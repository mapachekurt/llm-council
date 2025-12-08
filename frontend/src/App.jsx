import { useState, useEffect } from 'react';
import { AuthWrapper } from './components/AuthWrapper';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import { useApi } from './api';
import './App.css';

function App() {
  const api = useApi();
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Load conversation details when selected
  useEffect(() => {
    if (currentConversationId) {
      loadConversation(currentConversationId);
    }
  }, [currentConversationId]);

  const loadConversations = async () => {
    try {
      const convs = await api.getConversations();
      setConversations(convs);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await api.getMessages(id);
      setCurrentConversation({ id, messages: conv });
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const handleNewConversation = async () => {
    try {
      const newConv = await api.createConversation();
      setConversations([
        { id: newConv.id, created_at: new Date().toISOString(), message_count: 0 },
        ...conversations,
      ]);
      setCurrentConversationId(newConv.id);
      setCurrentConversation({ id: newConv.id, messages: [] });
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const handleSelectConversation = (id) => {
    setCurrentConversationId(id);
  };

  const handleSendMessage = async (content) => {
    if (!currentConversationId) return;

    setIsLoading(true);
    try {
      // Optimistically add user message to UI
      const userMessage = { role: 'user', content };
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...(prev?.messages ?? []), userMessage],
      }));

      const response = await api.sendMessage(currentConversationId, content);

      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...(prev?.messages ?? []), response],
      }));

    } catch (error) {
      console.error('Failed to send message:', error);
      // Simple error handling: remove the optimistic user message
      setCurrentConversation((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -1),
      }));
    } finally {
      setIsLoading(false);
      loadConversations(); // Reload to update titles/counts
    }
  };

  return (
    <AuthWrapper>
      <div className="app">
        <Sidebar
          conversations={conversations}
          currentConversationId={currentConversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
        />
        <ChatInterface
          conversation={currentConversation}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
        />
      </div>
    </AuthWrapper>
  );
}

export default App;
