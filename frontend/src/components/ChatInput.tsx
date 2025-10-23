import { useState } from 'react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Send, Trash2 } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  isDarkMode: boolean;
}

export function ChatInput({ onSend, disabled, isDarkMode }: ChatInputProps) {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className="flex items-start gap-2">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="flex-shrink-0 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300"
        >
          <Trash2 size={18} />
        </Button>
        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Nhập câu hỏi pháp luật của bạn..."
          className="flex-1 min-h-[60px] max-h-[200px] resize-none bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600 dark:text-gray-100 dark:placeholder-gray-400"
          disabled={disabled}
        />
        <Button 
          type="submit" 
          disabled={!message.trim() || disabled}
          size="icon"
          className="flex-shrink-0 bg-blue-500 hover:bg-blue-600 dark:bg-blue-600 dark:hover:bg-blue-700 rounded-full w-10 h-10"
        >
          <Send size={18} />
        </Button>
      </div>
    </form>
  );
}