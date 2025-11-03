import { useState, useEffect } from 'react';
import { ChatInterface } from './components/ChatInterface';
import { ConversationSidebar, type Conversation } from './components/Sidebar';
import { PDFViewer } from './components/PDFViewer';
import { getDocument } from './services/api';

export default function App() {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string>('default');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  
  // PDF Viewer state
  const [pdfView, setPdfView] = useState<{
    isOpen: boolean;
    url: string;
    title: string;
    articleNum?: string;
  } | null>(null);

  // Initialize dark mode and conversations from localStorage
  useEffect(() => {
    const savedMode = localStorage.getItem('darkMode');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedMode === 'true' || (!savedMode && prefersDark)) {
      setIsDarkMode(true);
      document.documentElement.classList.add('dark');
    }

    // Load conversations from localStorage
    const savedConversations = localStorage.getItem('conversations');
    if (savedConversations) {
      const parsed = JSON.parse(savedConversations);
      setConversations(parsed.map((c: any) => ({
        ...c,
        timestamp: new Date(c.timestamp),
      })));
    } else {
      // Add some demo conversations
      const demoConversations: Conversation[] = [
        {
          id: '1',
          title: '123',
          preview: 'Quyền lợi khi bị sa thải',
          timestamp: new Date(Date.now() - 3600000),
        },
        {
          id: '2',
          title: '123',
          preview: 'Thủ tục ly hôn',
          timestamp: new Date(Date.now() - 7200000),
        },
      ];
      setConversations(demoConversations);
    }
  }, []);

  // Save conversations to localStorage when they change
  useEffect(() => {
    if (conversations.length > 0) {
      localStorage.setItem('conversations', JSON.stringify(conversations));
    }
  }, [conversations]);

  const handleToggleDarkMode = () => {
    setIsDarkMode((prev) => {
      const newMode = !prev;
      localStorage.setItem('darkMode', String(newMode));
      
      if (newMode) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      
      return newMode;
    });
  };

  const handleNewConversation = () => {
    const newId = `conv-${Date.now()}`;
    const newConversation: Conversation = {
      id: newId,
      title: 'Cuộc trò chuyện mới',
      preview: 'Bắt đầu đặt câu hỏi...',
      timestamp: new Date(),
    };
    
    setConversations([newConversation, ...conversations]);
    setActiveConversationId(newId);
    
    if (window.innerWidth < 1024) {
      setIsSidebarOpen(false);
    }
  };

  const handleSelectConversation = (id: string) => {
    setActiveConversationId(id);
    
    if (window.innerWidth < 1024) {
      setIsSidebarOpen(false);
    }
  };

  const handleDeleteConversation = (id: string) => {
    setConversations(conversations.filter((c) => c.id !== id));
    
    if (activeConversationId === id) {
      const remaining = conversations.filter((c) => c.id !== id);
      setActiveConversationId(remaining.length > 0 ? remaining[0].id : 'default');
    }
  };

  const handleUpdateConversation = (id: string, firstMessage: string) => {
    setConversations((prev) =>
      prev.map((c) =>
        c.id === id
          ? {
              ...c,
              title: firstMessage.slice(0, 50),
              preview: firstMessage.slice(0, 80),
              timestamp: new Date(),
            }
          : c
      )
    );
  };

  // Handle PDF opening from backend
  const handleOpenPDF = async (pdfFilename: string, title: string, articleNum?: string) => {
    try {
      console.log('[PDF] Loading:', { pdfFilename, title, articleNum });
      
      if (!pdfFilename || pdfFilename === 'undefined') {
        alert('Không tìm thấy thông tin file PDF. Vui lòng thử lại.');
        return;
      }
      
      const pdfResponse = await getDocument(pdfFilename);
      
      const binaryString = window.atob(pdfResponse.data);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      
      setPdfView({ 
        isOpen: true,
        url, 
        title,
        articleNum
      });
    } catch (error) {
      console.error('[PDF] Error:', error);
      alert('Không thể tải file PDF. Vui lòng thử lại.');
    }
  };

  return (
    <div className="w-full h-screen overflow-hidden flex">
      {/* Sidebar */}
      <ConversationSidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onNewConversation={handleNewConversation}
        onSelectConversation={handleSelectConversation}
        onDeleteConversation={handleDeleteConversation}
        isDarkMode={isDarkMode}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />

      {/* Main Chat Area */}
      <div className="flex-1 overflow-hidden">
        <ChatInterface
          conversationId={activeConversationId}
          isDarkMode={isDarkMode}
          onToggleDarkMode={handleToggleDarkMode}
          onUpdateConversation={handleUpdateConversation}
          onOpenPDF={handleOpenPDF}
        />
      </div>

      {/* PDF Viewer Modal */}
      {pdfView && pdfView.isOpen && (
        <PDFViewer
          isOpen={pdfView.isOpen}
          onClose={() => setPdfView(null)}
          pdfUrl={pdfView.url}
          title={pdfView.title}
          articleNum={pdfView.articleNum}
        />
      )}
    </div>
  );
}