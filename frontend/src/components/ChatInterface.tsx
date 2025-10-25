import { useState, useEffect, useRef } from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { DarkModeToggle } from './DarkModeToggle';
import { PDFViewer } from './PDFViewer';
import { ScrollArea } from './ui/scroll-area';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { ThumbsUp, ThumbsDown, Zap, Crown } from 'lucide-react';
import { askQuestion, submitFeedback, getDocument, type ChatMessage as APIChatMessage, type PDFSource } from '../services/api';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  sources?: Array<{
    title: string;
    page?: string;
    pdfUrl?: string;
  }>;
  pdf_sources?: PDFSource[];
  context?: Array<{ source: string; content: string }>;
  feedback?: 'up' | 'down' | null;
}

interface ChatInterfaceProps {
  conversationId: string;
  isDarkMode: boolean;
  onToggleDarkMode: () => void;
}

// Helper function to format law name nicely
const formatLawName = (jsonFile: string | undefined): string => {
  if (!jsonFile) return 'Văn bản pháp luật';
  
  const nameMap: Record<string, string> = {
    'luat_lao_donghopnhat.json': 'Bộ luật Lao động',
    'luat_dat_dai_hopnhat.json': 'Luật Đất đai',
    'luat_hon_nhan_hopnhat.json': 'Luật Hôn nhân và Gia đình',
    'luat_dauthau_hopnhat.json': 'Luật Đấu thầu',
    'chuyen_giao_cong_nghe_hopnhat.json': 'Luật Chuyển giao công nghệ',
    'nghi_dinh_214_2025.json': 'Nghị định 214/2025/NĐ-CP',
  };
  
  return nameMap[jsonFile] || jsonFile.replace('_hopnhat.json', '').replace(/_/g, ' ');
};

export function ChatInterface({ conversationId, isDarkMode, onToggleDarkMode }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [mode, setMode] = useState<'fast' | 'quality'>('fast');
  const [pdfViewer, setPdfViewer] = useState<{ isOpen: boolean; url: string; title: string; pdfData?: string }>({
    isOpen: false,
    url: '',
    title: '',
    pdfData: undefined
  });
  const [chatHistory, setChatHistory] = useState<APIChatMessage[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Reset messages when conversation changes
    setMessages([{
      id: '1',
      text: 'Xao trình! Tôi là trợ lý pháp luật AI. Tôi có thể giúp bạn tư vấn về các vấn đề pháp luật tại Việt Nam. Bạn có câu hỏi gì không?',
      sender: 'ai',
      timestamp: new Date()
    }]);
    setChatHistory([]);
  }, [conversationId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isTyping]);

  const handleSendMessage = async (text: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages((prev: Message[]) => [...prev, userMessage]);
    setIsTyping(true);

    try {
      // Call backend API
      const response = await askQuestion(text, mode, chatHistory);
      
      // Convert PDF sources to display format - limit to 3 sources
      const displaySources = response.pdf_sources.slice(0, 3).map((pdfSource) => ({
        title: formatLawName(pdfSource.json_file),
        page: pdfSource.article_num || undefined,
        pdfUrl: pdfSource.pdf_file
      }));

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.answer,
        sender: 'ai',
        timestamp: new Date(),
        sources: displaySources,
        pdf_sources: response.pdf_sources,
        context: response.sources,
        feedback: null
      };
      
      setMessages((prev: Message[]) => [...prev, aiMessage]);
      
      // Update chat history for context
      setChatHistory([
        ...chatHistory,
        { role: 'user', content: text },
        { role: 'assistant', content: response.answer }
      ]);
      
    } catch (error) {
      console.error('Error asking question:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Xin lỗi, đã có lỗi xảy ra khi xử lý câu hỏi của bạn. Vui lòng thử lại.',
        sender: 'ai',
        timestamp: new Date(),
        feedback: null
      };
      setMessages((prev: Message[]) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleFeedback = async (messageId: string, feedback: 'up' | 'down') => {
    // Find the message
    const message = messages.find((msg: Message) => msg.id === messageId);
    if (!message || !message.context) return;

    // Toggle feedback
    const newFeedback = message.feedback === feedback ? null : feedback;
    
    setMessages((prev: Message[]) => prev.map((msg: Message) => 
      msg.id === messageId 
        ? { ...msg, feedback: newFeedback }
        : msg
    ));

    // Send feedback to backend if not null
    if (newFeedback) {
      try {
        // Find corresponding user question
        const messageIndex = messages.findIndex((msg: Message) => msg.id === messageId);
        let userQuestion = '';
        
        // Look backwards for the user message
        for (let i = messageIndex - 1; i >= 0; i--) { 
          if (messages[i].sender === 'user') {
            userQuestion = messages[i].text;
            break;
          }
        }

        await submitFeedback(
          userQuestion,
          message.text,
          message.context,
          newFeedback === 'up' ? 'like' : 'dislike'
        );
        
        console.log('Feedback submitted successfullyb ka');
      } catch (error) {
        console.error('Error submitting feedback bla bla bla:', error);
      }
    }
  };

  const handleOpenPDF = async (pdfFilename: string, title: string) => {
    try {
      console.log('Loading PDF:', pdfFilename);
      
      // Get PDF from backend
      const pdfResponse = await getDocument(pdfFilename);
      
      // Convert base64 to blob URL
      const binaryString = window.atob(pdfResponse.data);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      
      setPdfViewer({ 
        isOpen: true, 
        url, 
        title,
        pdfData: pdfResponse.data 
      });
    } catch (error) {
      console.error('Error loading PDF:', error);
      alert('Không thể tải file PDF. Vui lòng thử lại.');
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header - Fixed */}
      <div className="flex-shrink-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
        <h1 className="text-gray-900 dark:text-gray-100">Trợ lý Pháp luật AI</h1>
        <DarkModeToggle isDark={isDarkMode} onToggle={onToggleDarkMode} />
      </div>
      
      {/* Messages Area - Scrollable */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto p-6 space-y-6">
            {messages.map((message) => (
              <div key={message.id}>
                <ChatMessage message={message} isDarkMode={isDarkMode} />
              {message.sender === 'ai' && message.sources && (
                <div className="ml-11 mt-4">
                  <Card className="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-sm text-gray-600 dark:text-gray-400">📚 Nguồn tham khảo:</span>
                    </div>
                    <div className="space-y-2">
                      {message.sources.map((source, idx) => (
                        <div key={idx} className="flex items-start gap-2 text-sm">
                          <button
                            onClick={() => source.pdfUrl && handleOpenPDF(source.pdfUrl, source.title)}
                            className="w-5 h-5 rounded-full bg-blue-500 dark:bg-blue-600 text-white flex items-center justify-center flex-shrink-0 text-xs hover:bg-blue-600 dark:hover:bg-blue-700 cursor-pointer transition-colors"
                          >
                            {idx + 1}
                          </button>
                          <div className="flex-1">
                            <button
                              onClick={() => source.pdfUrl && handleOpenPDF(source.pdfUrl, source.title)}
                              className="text-left hover:underline w-full"
                            >
                              <div className="flex flex-col gap-1">
                                <span className="text-gray-700 dark:text-gray-300">
                                  {source.title}
                                </span>
                                {source.page && (
                                  <span className="text-red-500 dark:text-red-400 text-xs">
                                    📄 {source.page}
                                  </span>
                                )}
                              </div>
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-orange-500 dark:text-orange-400 mt-3 flex items-center gap-1">
                      <span>💡</span>
                      Click vào các link để xem tài liệu đầy đủ
                    </p>
                  </Card>
                  <div className="flex items-center gap-2 mt-3">
                    <Button
                      variant="ghost"
                      size="sm"
                      className={`gap-1 ${message.feedback === 'up' ? 'bg-gray-200 dark:bg-gray-700' : ''}`}
                      onClick={() => handleFeedback(message.id, 'up')}
                    >
                      <ThumbsUp size={16} />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className={`gap-1 ${message.feedback === 'down' ? 'bg-gray-200 dark:bg-gray-700' : ''}`}
                      onClick={() => handleFeedback(message.id, 'down')}
                    >
                      <ThumbsDown size={16} />
                    </Button>
                  </div>
                </div>
              )}
              </div>
            ))}
              {isTyping && (
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white flex-shrink-0">
                  AI
                </div>
                <Card className="p-4 flex-1 bg-white dark:bg-gray-800">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </Card>
              </div>
            )}
            <div ref={scrollRef} />
          </div>
      </div>
      
      {/* Input Area - Fixed at bottom */}
      <div className="flex-shrink-0 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-2 mb-3">
            <Button
              variant={mode === 'fast' ? 'default' : 'outline'}
              size="sm"
              className={`gap-1 ${mode === 'fast' ? 'bg-blue-500 hover:bg-blue-600 dark:bg-blue-600 dark:hover:bg-blue-700' : 'dark:border-gray-600 dark:text-gray-300'}`}
              onClick={() => setMode('fast')}
            >
              <Zap size={14} />
              Fast
            </Button>
            <Button
              variant={mode === 'quality' ? 'default' : 'outline'}
              size="sm"
              className={`gap-1 ${mode === 'quality' ? 'bg-pink-500 hover:bg-pink-600 dark:bg-pink-600 dark:hover:bg-pink-700' : 'dark:border-gray-600 dark:text-gray-300'}`}
              onClick={() => setMode('quality')}
            >
              <Crown size={14} />
              Quality
            </Button>
          </div>
          <ChatInput onSend={handleSendMessage} disabled={isTyping} isDarkMode={isDarkMode} />
        </div>
      </div>

      <PDFViewer
        isOpen={pdfViewer.isOpen}
        onClose={() => setPdfViewer({ ...pdfViewer, isOpen: false })}
        pdfUrl={pdfViewer.url}
        title={pdfViewer.title}
      />
    </div>
  );
}
