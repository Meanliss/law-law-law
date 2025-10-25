import { useState, useEffect } from 'react';
import { ChatInterface } from './components/ChatInterface';
import { Sidebar } from './components/Sidebar';

interface Conversation {
  id: string;
  title: string;
  lastMessage?: string;
}

export default function App() {
  const [conversations, setConversations] = useState<Conversation[]>([
    { id: '1', title: '123', lastMessage: 'Quyền lợi khi bị sa thải' },
    { id: '2', title: '123', lastMessage: 'Thủ tục ly hôn' },
  ]);
  const [activeConversation, setActiveConversation] = useState<string>('1');
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(isDarkMode));
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const handleNewConversation = () => {
    const newId = Date.now().toString();
    const newConv: Conversation = {
      id: newId,
      title: '123',
    };
    setConversations([newConv, ...conversations]);
    setActiveConversation(newId);
  };

  const handleDeleteConversation = (id: string) => {
    setConversations(conversations.filter(conv => conv.id !== id));
    if (activeConversation === id && conversations.length > 1) {
      const remaining = conversations.filter(conv => conv.id !== id);
      if (remaining.length > 0) {
        setActiveConversation(remaining[0].id);
      }
    }
  };

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
      <Sidebar 
        conversations={conversations}
        activeConversation={activeConversation}
        onSelectConversation={setActiveConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        isDarkMode={isDarkMode}
      />
      <div className="flex-1 overflow-hidden">
        <ChatInterface 
          conversationId={activeConversation} 
          isDarkMode={isDarkMode}
          onToggleDarkMode={() => setIsDarkMode(!isDarkMode)}
        />
      </div>
    </div>
  );
}