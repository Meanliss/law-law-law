import { motion } from 'motion/react';
import { MessageSquare, BookOpen, Scale, FileText } from 'lucide-react';

// 🎨 HƯỚNG DẪN TỰY CHỈNH:
// 1. Thêm/bớt gợi ý: Chỉnh sửa mảng 'prompts' bên dưới
// 2. Thay đổi icon: Import icon mới từ 'lucide-react'
// 3. Thay đổi màu: Sửa gradient trong className

interface SuggestedPromptsProps {
  onSelectPrompt: (prompt: string) => void;
}

export function SuggestedPrompts({ onSelectPrompt }: SuggestedPromptsProps) {
  // 📝 DANH SÁCH GỢI Ý - THÊM/BỚT TẠI ĐÂY
  const prompts = [
    {
      icon: Scale,
      text: 'Hướng dẫn đăng ký bản quyền',
    },
    {
      icon: FileText,
      text: 'Quy định về thuế TNCN mới nhất',
    },
    {
      icon: BookOpen,
      text: 'Thủ tục thành lập công ty',
    },
    {
      icon: MessageSquare,
      text: 'Quyền lợi người lao động',
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex flex-wrap gap-2 justify-center"
    >
      {prompts.map((prompt, index) => {
        const Icon = prompt.icon;
        
        return (
          <motion.button
            key={index}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ scale: 1.05, y: -2 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => onSelectPrompt(prompt.text)}
            className="group flex items-center gap-2 px-3 py-2 rounded-xl backdrop-blur-xl bg-white/60 dark:bg-gray-800/60 hover:bg-white/80 dark:hover:bg-gray-800/80 border border-white/50 dark:border-gray-700/50 text-xs text-gray-700 dark:text-gray-300 transition-all duration-300 shadow-md hover:shadow-lg"
          >
            <Icon size={14} className="text-blue-500 dark:text-cyan-400 group-hover:scale-110 transition-transform" />
            <span>{prompt.text}</span>
          </motion.button>
        );
      })}
    </motion.div>
  );
}
