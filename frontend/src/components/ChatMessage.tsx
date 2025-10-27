import { Card } from './ui/card';
import { User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

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
          {isAI ? (
            <div className="prose prose-sm dark:prose-invert max-w-none prose-p:my-2 prose-headings:my-3 prose-ul:my-2 prose-ol:my-2 prose-li:my-1">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw]}
                components={{
                  p: ({ children }: any) => <p className="text-gray-800 dark:text-gray-200">{children}</p>,
                  strong: ({ children }: any) => <strong className="font-bold text-gray-900 dark:text-gray-100">{children}</strong>,
                  em: ({ children }: any) => <em className="italic text-gray-800 dark:text-gray-200">{children}</em>,
                  ul: ({ children }: any) => <ul className="list-disc list-inside space-y-1 text-gray-800 dark:text-gray-200">{children}</ul>,
                  ol: ({ children }: any) => <ol className="list-decimal list-inside space-y-1 text-gray-800 dark:text-gray-200">{children}</ol>,
                  h1: ({ children }: any) => <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">{children}</h1>,
                  h2: ({ children }: any) => <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">{children}</h2>,
                  h3: ({ children }: any) => <h3 className="text-base font-bold text-gray-900 dark:text-gray-100 mb-1">{children}</h3>,
                  code: ({ children, className }: any) => {
                    const isInline = !className;
                    return isInline ? (
                      <code className="bg-gray-100 dark:bg-gray-700 text-red-600 dark:text-red-400 px-1 py-0.5 rounded text-sm">{children}</code>
                    ) : (
                      <code className="block bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 p-2 rounded overflow-x-auto">{children}</code>
                    );
                  },
                }}
              >
                {message.text}
              </ReactMarkdown>
            </div>
          ) : (
            <p className="text-gray-800 dark:text-gray-200 whitespace-pre-wrap">
              {message.text}
            </p>
          )}
        </Card>
      </div>
    </div>
  );
}