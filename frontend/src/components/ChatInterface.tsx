import { useState, useEffect, useRef } from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { DarkModeToggle } from './DarkModeToggle';
import { PDFViewer } from './PDFViewer';
import { ScrollArea } from './ui/scroll-area';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { ThumbsUp, ThumbsDown, Zap, Crown, Clock } from 'lucide-react';
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
  timing_ms?: number;
  search_method?: string;
}

interface ChatInterfaceProps {
  conversationId: string;
  isDarkMode: boolean;
  onToggleDarkMode: () => void;
  onOpenPDF: (pdfUrl: string, title: string, articleNum?: string) => void;  // ✅ THÊM
}

// ✅ FIXED: Mapping đầy đủ tất cả tên luật
const formatLawName = (jsonFile: string | undefined): string => {
  if (!jsonFile) return 'Văn bản pháp luật';
  
  const nameMap: Record<string, string> = {
    'luat_lao_donghopnhat.json': 'Bộ luật Lao động',
    'luat_so_huu_tri_tue_hopnhat.json': 'Bộ luật Sở hữu trí tuệ',
    'luat_dat_dai_hopnhat.json': 'Luật Đất đai',
    'luat_dat_dai.json': 'Luật Đất đai',
    'luat_hon_nhan_hopnhat.json': 'Luật Hôn nhân và Gia đình',
    'luat_hon_nhan.json': 'Luật Hôn nhân và Gia đình',
    'luat_dauthau_hopnhat.json': 'Luật Đấu thầu',
    'luat_dau_thau.json': 'Luật Đấu thầu',
    'chuyen_giao_cong_nghe_hopnhat.json': 'Luật Chuyển giao công nghệ',
    'chuyen_giao_cong_nghe.json': 'Luật Chuyển giao công nghệ',
    'nghi_dinh_214_2025.json': 'Nghị định 214/2025/NĐ-CP',
    'luat_hinh_su_hopnhat.json': 'Bộ luật Hình sự',  // ✅ THÊM
  };
  
  return nameMap[jsonFile] || jsonFile.replace(/_hopnhat\.json|\.json/g, '').replace(/_/g, ' ');
};

export function ChatInterface({ conversationId, isDarkMode, onToggleDarkMode, onOpenPDF }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [mode, setMode] = useState<'fast' | 'quality'>('fast');
  //const [pdfViewer, setPdfViewer] = useState<{ isOpen: boolean; url: string; title: string; pdfData?: string; articleNum?: string }>({
    //isOpen: false,
    //url: '',
    //title: '',
    //pdfData: undefined,
    //articleNum: undefined
  //});
  const [chatHistory, setChatHistory] = useState<APIChatMessage[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages([{
      id: '1',
      text: 'Xin chào! Tôi là trợ lý pháp luật AI. Tôi có thể giúp bạn tư vấn về các vấn đề pháp luật tại Việt Nam. Bạn có câu hỏi gì không?',
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
      const response = await askQuestion(text, mode, chatHistory);
      
      // ✅ Convert PDF sources với tên đã format
      const displaySources = response.pdf_sources.slice(0, 3).map((pdfSource) => ({
        title: formatLawName(pdfSource.json_file),  // ✅ Dùng hàm format
        page: pdfSource.article_num ? `Điều ${pdfSource.article_num}` : undefined,
        pdfUrl: pdfSource.pdf_file,
        articleNum: pdfSource.article_num?.toString()
      }));

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.answer,
        sender: 'ai',
        timestamp: new Date(),
        sources: displaySources,
        pdf_sources: response.pdf_sources,
        context: response.sources,
        feedback: null,
        timing_ms: response.timing_ms,
        search_method: response.search_method
      };
      
      setMessages((prev: Message[]) => [...prev, aiMessage]);
      
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
    const message = messages.find((msg: Message) => msg.id === messageId);
    if (!message || !message.context) return;

    const newFeedback = message.feedback === feedback ? null : feedback;
    
    setMessages((prev: Message[]) => prev.map((msg: Message) => 
      msg.id === messageId 
        ? { ...msg, feedback: newFeedback }
        : msg
    ));

    if (newFeedback) {
      try {
        const messageIndex = messages.findIndex((msg: Message) => msg.id === messageId);
        let userQuestion = '';
        
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
        
        console.log('Feedback submitted successfully');
      } catch (error) {
        console.error('Error submitting feedback:', error);
      }
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="flex-shrink-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Trợ lý Pháp luật AI</h1>
        <DarkModeToggle isDark={isDarkMode} onToggle={onToggleDarkMode} />
      </div>
      
      {/* Messages Area */}
      <div className="flex-1 relative">
        <div className="absolute inset-0">
          <ScrollArea className="h-full">
            <div className="max-w-4xl mx-auto p-6 space-y-6">
            {messages.map((message) => (
              <div key={message.id}>
                <ChatMessage message={message} isDarkMode={isDarkMode} />
              
              {/* ✅ SOURCES SECTION - CẢI THIỆN UI NHƯNG GIỮ LOGIC CŨ */}
              {message.sender === 'ai' && message.sources && (
                <div className="ml-11 mt-4">
                  <Card className="p-4 bg-gradient-to-br from-blue-50 to-white dark:from-gray-800 dark:to-gray-850 border-2 border-blue-200 dark:border-blue-700">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-sm font-semibold text-blue-700 dark:text-blue-300">📚 Nguồn tham khảo:</span>
                    </div>
                    <div className="space-y-2">
                        {message.sources.map((source, idx) => {
                          const articleNum = source.page?.replace('Điều ', '') || '';

                          return (
                            <div key={idx} className="flex items-start gap-3 text-sm group">
                              <button
                                onClick={() => source.pdfUrl && onOpenPDF(source.pdfUrl, source.title, articleNum)}
                                className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-600 to-blue-700 text-white flex items-center justify-center flex-shrink-0 text-xs font-bold hover:from-blue-700 hover:to-blue-800 cursor-pointer transition-all shadow-md hover:shadow-lg hover:scale-110"
                              >
                                {idx + 1}
                              </button>
                              <div className="flex-1">
                                <button
                                  onClick={() => source.pdfUrl && onOpenPDF(source.pdfUrl, source.title, articleNum)}
                                  className="text-left hover:underline w-full group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors"
                                >
                                  <div className="flex flex-col gap-1">
                                    <span className="font-semibold text-gray-900 dark:text-gray-100">
                                      {source.title}
                                    </span>
                                    {source.page && (
                                      <span className="text-blue-600 dark:text-blue-400 text-xs font-medium">
                                        {source.page}
                                      </span>
                                    )}
                                  </div>
                                </button>
                              </div>
                            </div>
                          );
                        })}
                    </div>
                    <p className="text-xs text-orange-600 dark:text-orange-400 mt-3 flex items-center gap-1 font-medium">
                      <span>💡</span>
                      Click vào các số để xem tài liệu đầy đủ
                    </p>
                  </Card>
                  
                  {/* Feedback Buttons */}
                  <div className={`flex items-center gap-2 mt-3 transition-all duration-500 ${
                    message.feedback ? 'opacity-0 translate-y-2 pointer-events-none' : 'opacity-100 translate-y-0'
                  }`}>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="gap-1 hover:scale-110 transition-transform active:scale-95"
                      onClick={() => handleFeedback(message.id, 'up')}
                    >
                      <ThumbsUp size={16} className="transition-colors hover:text-green-500" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="gap-1 hover:scale-110 transition-transform active:scale-95"
                      onClick={() => handleFeedback(message.id, 'down')}
                    >
                      <ThumbsDown size={16} className="transition-colors hover:text-red-500" />
                    </Button>
                  </div>
                  
                  {/* Feedback Response */}
                  {message.feedback && (
                    <div className="mt-3 animate-fade-in">
                      <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${
                        message.feedback === 'up' 
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' 
                          : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                      }`}>
                        {message.feedback === 'up' ? (
                          <>
                            <ThumbsUp size={14} className="animate-bounce" />
                            <span>Cảm ơn phản hồi của bạn!</span>
                          </>
                        ) : (
                          <>
                            <ThumbsDown size={14} className="animate-bounce" />
                            <span>Chúng tôi sẽ cải thiện!</span>
                          </>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              {/* Timing */}
              {message.sender === 'ai' && message.timing_ms && (
                <div className="ml-11 mt-2 flex justify-end">
                  <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700">
                    <Clock size={12} />
                    <span>{(message.timing_ms / 1000).toFixed(2)}s</span>
                    {message.timing_ms < 2000 && (
                      <span className="inline-flex items-center gap-1 text-green-600 dark:text-green-400">
                        <Zap size={10} />
                      </span>
                    )}
                  </div>
                </div>
              )}
              </div>
            ))}
            
            {/* Typing Indicator */}
            {isTyping && (
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white flex-shrink-0 font-bold text-sm">
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
          </ScrollArea>
        </div>
      </div>
      
      {/* Input Area */}
      <div className="flex-shrink-0 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-2 mb-3">
            <Button
              variant={mode === 'fast' ? 'default' : 'outline'}
              size="sm"
              className={`gap-1 ${mode === 'fast' ? 'bg-blue-500 hover:bg-blue-600' : ''}`}
              onClick={() => setMode('fast')}
            >
              <Zap size={14} />
              Fast
            </Button>
            <Button
              variant={mode === 'quality' ? 'default' : 'outline'}
              size="sm"
              className={`gap-1 ${mode === 'quality' ? 'bg-pink-500 hover:bg-pink-600' : ''}`}
              onClick={() => setMode('quality')}
            >
              <Crown size={14} />
              Quality
            </Button>
          </div>
          <ChatInput onSend={handleSendMessage} disabled={isTyping} isDarkMode={isDarkMode} />
        </div>
      </div>  
    </div>
  );
}