import { useState, useRef, useEffect } from 'react';
import { motion } from 'motion/react';
import { Send, Zap, Crown } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  isDarkMode: boolean;
  mode?: 'fast' | 'quality';
  onModeChange?: (mode: 'fast' | 'quality') => void;
}

export function ChatInput({ onSend, disabled, isDarkMode, mode = 'fast', onModeChange }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [message]);

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
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="relative"
    >
      {/* Glassmorphic Container - ChatGPT Style */}
      <div
        className={`relative overflow-hidden rounded-3xl backdrop-blur-xl border transition-all duration-300 ${
          isFocused
            ? 'bg-white/90 dark:bg-gray-800/90 border-gray-300/60 dark:border-gray-600/60 shadow-lg'
            : 'bg-white/70 dark:bg-gray-800/70 border-gray-300/50 dark:border-gray-700/50 shadow-md'
        }`}
      >
        {/* Animated Gradient Background */}
        <motion.div
          animate={{
            background: isFocused
              ? [
                  'linear-gradient(135deg, rgba(59,130,246,0.1), rgba(6,182,212,0.1))',
                  'linear-gradient(225deg, rgba(6,182,212,0.1), rgba(59,130,246,0.1))',
                  'linear-gradient(315deg, rgba(59,130,246,0.1), rgba(6,182,212,0.1))',
                ]
              : 'linear-gradient(135deg, rgba(0,0,0,0), rgba(0,0,0,0))',
          }}
          transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-0 pointer-events-none"
        />

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="relative z-10">
          <div className="flex items-center gap-2 px-4 py-3">
            {/* Mode Selector - Hidden, can be toggled via button if needed */}
            {onModeChange && (
              <div className="flex gap-1 mr-1">
                <motion.button
                  type="button"
                  whileHover={{ scale: 1.08 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => onModeChange('fast')}
                  className={`p-2 rounded-xl transition-all duration-300 ${
                    mode === 'fast'
                      ? 'bg-gradient-to-br from-blue-500 to-cyan-500 text-white shadow-sm'
                      : 'bg-transparent text-gray-400 dark:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700/50'
                  }`}
                  title="Fast Mode"
                >
                  <Zap size={16} />
                </motion.button>
                <motion.button
                  type="button"
                  whileHover={{ scale: 1.08 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => onModeChange('quality')}
                  className={`p-2 rounded-xl transition-all duration-300 ${
                    mode === 'quality'
                      ? 'bg-gradient-to-br from-purple-500 to-pink-500 text-white shadow-sm'
                      : 'bg-transparent text-gray-400 dark:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700/50'
                  }`}
                  title="Quality Mode"
                >
                  <Crown size={16} />
                </motion.button>
              </div>
            )}

            {/* Textarea */}
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                disabled={disabled}
                placeholder="Nhập câu hỏi của bạn..."
                rows={1}
                className="w-full bg-transparent resize-none outline-none text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 max-h-[200px] disabled:opacity-50"
                style={{ minHeight: '24px' }}
              />
            </div>

            {/* Send Button - ChatGPT Style */}
            <motion.button
              type="submit"
              disabled={disabled || !message.trim()}
              whileHover={{ scale: message.trim() && !disabled ? 1.05 : 1 }}
              whileTap={{ scale: message.trim() && !disabled ? 0.95 : 1 }}
              className={`relative overflow-hidden rounded-xl p-2 transition-all duration-300 ${
                message.trim() && !disabled
                  ? 'bg-blue-500 hover:bg-blue-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed'
              }`}
            >
              <Send size={18} className="relative z-10" />
            </motion.button>
          </div>
        </form>
      </div>


    </motion.div>
  );
}
