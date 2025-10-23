import { Card } from './ui/card';
import { User } from 'lucide-react';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  sources?: Array<{
    title: string;
    page?: string;
  }>;
}

interface ChatMessageProps {
  message: Message;
  isDarkMode: boolean;
}

function highlightReferences(text: string): React.ReactNode[] {
  // Match patterns like [1], [2], [3], or [theo đúng]
  const parts = text.split(/(\[\d+\]|\[theo đúng\])/g);
  
  return parts.map((part, index) => {
    if (/\[\d+\]|\[theo đúng\]/.test(part)) {
      return (
        <span
          key={index}
          className="inline-block bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-1.5 py-0.5 rounded text-sm mx-0.5"
        >
          {part}
        </span>
      );
    }
    return <span key={index}>{part}</span>;
  });
}

export function ChatMessage({ message, isDarkMode }: ChatMessageProps) {
  const isAI = message.sender === 'ai';

  return (
    <div className={`flex items-start gap-3`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isAI 
          ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white' 
          : 'bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300'
      }`}>
        {isAI ? 'AI' : <User size={18} />}
      </div>
      <div className="flex-1">
        <Card className={`p-4 ${
          isAI ? 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700' : 'bg-gray-200 dark:bg-gray-700 border-0'
        }`}>
          <p className="text-gray-800 dark:text-gray-200 whitespace-pre-wrap">
            {isAI ? highlightReferences(message.text) : message.text}
          </p>
        </Card>
      </div>
    </div>
  );
}