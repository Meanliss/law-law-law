import { motion, AnimatePresence } from 'motion/react';
import { Plus, MessageSquare, Trash2, ChevronLeft, Menu } from 'lucide-react';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';

export interface Conversation {
  id: string;
  title: string;
  preview: string;
  timestamp: Date;
}

interface ConversationSidebarProps {
  conversations: Conversation[];
  activeConversationId: string;
  onNewConversation: () => void;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
  isDarkMode: boolean;
  isOpen: boolean;
  onToggle: () => void;
}

export function ConversationSidebar({
  conversations,
  activeConversationId,
  onNewConversation,
  onSelectConversation,
  onDeleteConversation,
  isDarkMode,
  isOpen,
  onToggle,
}: ConversationSidebarProps) {
  return (
    <>
      {/* Mobile Toggle Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onToggle}
        className="lg:hidden fixed top-6 left-4 z-50 w-10 h-10 rounded-2xl backdrop-blur-2xl bg-white/80 dark:bg-gray-800/80 border border-white/50 dark:border-gray-700/50 shadow-xl flex items-center justify-center"
      >
        {isOpen ? <ChevronLeft size={20} /> : <Menu size={20} />}
      </motion.button>

      {/* Backdrop for Mobile */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onToggle}
            className="lg:hidden fixed inset-0 bg-black/40 backdrop-blur-sm z-30"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.div
        initial={{ x: -320 }}
        animate={{ x: isOpen ? 0 : -320 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="fixed lg:relative top-0 left-0 h-full w-80 z-40 lg:z-0 flex flex-col"
      >
        {/* Glass Container */}
        <div className="h-full backdrop-blur-2xl bg-white/70 dark:bg-gray-900/70 border-r border-white/50 dark:border-gray-700/50 shadow-2xl relative overflow-hidden">
          {/* Animated Background Orb */}
          <motion.div
            animate={{
              x: [0, 50, 0],
              y: [0, -50, 0],
              scale: [1, 1.2, 1],
            }}
            transition={{ duration: 15, repeat: Infinity, ease: 'linear' }}
            className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-blue-400/20 to-cyan-400/20 dark:from-blue-500/10 dark:to-cyan-500/10 rounded-full blur-3xl pointer-events-none"
          />

          <div className="relative z-10 h-full flex flex-col p-4">
            {/* New Conversation Button */}
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                <Button
                  onClick={onNewConversation}
                  className="w-full h-auto py-4 rounded-2xl bg-gradient-to-br from-blue-500 via-cyan-500 to-teal-500 hover:from-blue-600 hover:via-cyan-600 hover:to-teal-600 text-white border-0 shadow-xl shadow-blue-500/30 relative overflow-hidden group"
                >
                  {/* Shimmer Effect */}
                  <motion.div
                    animate={{ x: ['-100%', '200%'] }}
                    transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                  />

                  <div className="relative z-10 flex items-center justify-center gap-2">
                    <Plus size={20} />
                    <span>Cuộc trò chuyện mới</span>
                  </div>
                </Button>
              </motion.div>
            </motion.div>

            {/* Conversations List */}
            <div className="flex-1 mt-4 overflow-hidden">
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="mb-3"
              >
                <h3 className="text-sm text-gray-600 dark:text-gray-400 px-2">
                  Lịch sử trò chuyện
                </h3>
              </motion.div>

              <ScrollArea className="h-[calc(100%-2rem)]">
                <div className="space-y-2 pr-2">
                  <AnimatePresence mode="popLayout">
                    {conversations.length === 0 ? (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-center py-8 px-4"
                      >
                        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-800 mx-auto mb-3 flex items-center justify-center">
                          <MessageSquare size={24} className="text-gray-400 dark:text-gray-500" />
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Chưa có cuộc trò chuyện nào
                        </p>
                      </motion.div>
                    ) : (
                      conversations.map((conversation, index) => (
                        <motion.div
                          key={conversation.id}
                          layout
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: -20 }}
                          transition={{ delay: index * 0.05 }}
                        >
                          <div
                            className={`group relative overflow-hidden rounded-2xl backdrop-blur-xl border transition-all duration-300 ${activeConversationId === conversation.id
                                ? 'bg-gradient-to-br from-blue-500/20 via-cyan-500/20 to-teal-500/20 border-blue-400/50 dark:border-cyan-500/50 shadow-lg shadow-blue-500/20'
                                : 'bg-white/60 dark:bg-gray-800/60 border-white/50 dark:border-gray-700/50 hover:bg-white/80 dark:hover:bg-gray-800/80 hover:scale-[1.02]'
                              }`}
                          >
                            {/* Hover Gradient Effect */}
                            <motion.div
                              initial={{ opacity: 0 }}
                              whileHover={{ opacity: 1 }}
                              className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-cyan-500/10 to-transparent pointer-events-none"
                            />

                            <button
                              onClick={() => onSelectConversation(conversation.id)}
                              className="relative z-10 w-full text-left p-4"
                            >
                              <div className="flex items-start gap-3">
                                <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center flex-shrink-0 shadow-md">
                                  <MessageSquare size={16} className="text-white" />
                                </div>

                                <div className="flex-1 min-w-0">
                                  <h4 className="font-semibold text-gray-900 dark:text-gray-100 line-clamp-2 mb-1 text-sm leading-snug">
                                    {conversation.title}
                                  </h4>
                                  <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 leading-relaxed">
                                    {conversation.preview}
                                  </p>
                                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                                    {formatRelativeTime(conversation.timestamp)}
                                  </p>
                                </div>
                              </div>
                            </button>

                            {/* Delete Button */}
                            <motion.div
                              initial={{ opacity: 0, x: 10 }}
                              whileHover={{ opacity: 1, x: 0 }}
                              className="absolute top-2 right-2 z-20 opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                              <motion.button
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.9 }}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onDeleteConversation(conversation.id);
                                }}
                                className="w-8 h-8 rounded-xl backdrop-blur-xl bg-red-500/80 hover:bg-red-600/90 text-white flex items-center justify-center shadow-lg"
                              >
                                <Trash2 size={14} />
                              </motion.button>
                            </motion.div>
                          </div>
                        </motion.div>
                      ))
                    )}
                  </AnimatePresence>
                </div>
              </ScrollArea>
            </div>

            {/* Bottom Info */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="mt-4 pt-4 border-t border-white/50 dark:border-gray-700/50"
            >
              <div className="px-2 py-3 rounded-2xl backdrop-blur-xl bg-gradient-to-br from-blue-500/10 via-cyan-500/10 to-transparent border border-blue-200/30 dark:border-blue-700/30">
                <p className="text-xs text-gray-600 dark:text-gray-400 text-center">
                  🤖 Trợ lý AI Pháp luật
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500 text-center mt-1">
                  Powered by AI
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </motion.div>
    </>
  );
}

// Helper function to format relative time
function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffInMs = now.getTime() - date.getTime();
  const diffInMinutes = Math.floor(diffInMs / 60000);
  const diffInHours = Math.floor(diffInMs / 3600000);
  const diffInDays = Math.floor(diffInMs / 86400000);

  if (diffInMinutes < 1) return 'Vừa xong';
  if (diffInMinutes < 60) return `${diffInMinutes} phút trước`;
  if (diffInHours < 24) return `${diffInHours} giờ trước`;
  if (diffInDays < 7) return `${diffInDays} ngày trước`;

  return date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
}
