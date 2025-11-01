import { useState, useEffect } from 'react';
import { ChatInterface } from './components/ChatInterface';
import { Sidebar } from './components/Sidebar';
import { PDFViewer } from './components/PDFViewer';
import { getDocument } from './services/api';  // ✅ THÊM

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

  // ✅ SỬA STATE cho PDF viewer
  const [pdfView, setPdfView] = useState<{
    isOpen: boolean;
    url: string;
    title: string;
    articleNum?: string;
  } | null>(null);

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

  // ✅ SỬA HANDLER: Load PDF từ backend
  const handleOpenPDF = async (pdfFilename: string, title: string, articleNum?: string) => {
    try {
      console.log('[PDF] Loading:', { pdfFilename, title, articleNum });
      
      // ✅ Kiểm tra filename hợp lệ
      if (!pdfFilename || pdfFilename === 'undefined') {
        alert('Không tìm thấy thông tin file PDF. Vui lòng thử lại.');
        return;
      }
      
      // ✅ Fetch PDF từ backend
      const pdfResponse = await getDocument(pdfFilename);
      
      // ✅ Convert base64 to blob URL
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
          onOpenPDF={handleOpenPDF}
        />
      </div>
      
      {/* ✅ PDF MODAL - CHỈ MỞ KHI CÓ pdfView */}
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