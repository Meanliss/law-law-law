import { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Send, Trash2 } from 'lucide-react';
import { motion } from 'motion/react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  isDarkMode: boolean;
}

export function ChatInput({ onSend, disabled, isDarkMode }: ChatInputProps) {
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
      {/* Glassmorphic Container */}
      <div
        className={`relative overflow-hidden rounded-3xl backdrop-blur-2xl border transition-all duration-500 ${
          isFocused
            ? 'bg-white/80 dark:bg-gray-800/80 border-blue-500/50 dark:border-cyan-500/50 shadow-2xl shadow-blue-500/20 dark:shadow-cyan-500/20 scale-[1.02]'
            : 'bg-white/60 dark:bg-gray-800/60 border-gray-300/50 dark:border-gray-700/50 shadow-xl shadow-gray-500/10 dark:shadow-gray-900/30'
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
          <div className="flex items-end gap-3 p-4">
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
                className="w-full bg-transparent resize-none outline-none text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 max-h-[200px] disabled:opacity-50"
                style={{ minHeight: '24px' }}
              />

              {/* Floating Sparkle Effect on Focus */}
              {isFocused && (
                <motion.div
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: [0, 1, 0], scale: [0, 1, 0] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="absolute -top-1 right-0"
                >
                  <Sparkles size={16} className="text-blue-500 dark:text-cyan-400" />
                </motion.div>
              )}
            </div>

            {/* Send Button */}
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Button
                type="submit"
                disabled={disabled || !message.trim()}
                className={`relative overflow-hidden rounded-2xl px-4 py-2 h-auto transition-all duration-300 ${
                  message.trim() && !disabled
                    ? 'bg-gradient-to-br from-blue-500 via-cyan-500 to-teal-500 hover:from-blue-600 hover:via-cyan-600 hover:to-teal-600 text-white shadow-lg shadow-blue-500/30'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500'
                }`}
              >
                {/* Shimmer Effect */}
                {message.trim() && !disabled && (
                  <motion.div
                    animate={{
                      x: ['-100%', '200%'],
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: 'linear',
                    }}
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                  />
                )}

                <Send size={18} className="relative z-10" />
              </Button>
            </motion.div>
          </div>
        </form>
      </div>

      {/* Floating Tips */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="text-xs text-gray-500 dark:text-gray-400 mt-2 flex items-center gap-2"
      >
        <span className="flex items-center gap-1">
          <kbd className="px-1.5 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600">
            Enter
          </kbd>
          để gửi
        </span>
        <span className="text-gray-400">•</span>
        <span className="flex items-center gap-1">
          <kbd className="px-1.5 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600">
            Shift + Enter
          </kbd>
          xuống dòng
        </span>
      </motion.div>
    </motion.div>
  );
}