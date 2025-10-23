import { MessageCircle, Trash2, Plus } from 'lucide-react';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';

interface Conversation {
  id: string;
  title: string;
  lastMessage?: string;
}

interface SidebarProps {
  conversations: Conversation[];
  activeConversation: string;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
  isDarkMode: boolean;
}

export function Sidebar({ 
  conversations, 
  activeConversation, 
  onSelectConversation, 
  onNewConversation,
  onDeleteConversation,
  isDarkMode
}: SidebarProps) {
  return (
    <aside className="w-72 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
      <div className="p-4">
        <Button 
          onClick={onNewConversation}
          className="w-full bg-blue-500 hover:bg-blue-600 dark:bg-blue-600 dark:hover:bg-blue-700 text-white gap-2"
        >
          <Plus size={18} />
          Cuộc trò chuyện mới
        </Button>
      </div>
      <ScrollArea className="flex-1 px-2">
        <div className="space-y-1">
          {conversations.map((conversation) => (
            <div 
              key={conversation.id}
              className={`group relative rounded-lg transition-colors ${
                activeConversation === conversation.id 
                  ? 'bg-gray-200 dark:bg-gray-700' 
                  : 'hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <button
                onClick={() => onSelectConversation(conversation.id)}
                className="w-full text-left px-3 py-3 pr-10"
              >
                <div className="flex items-center gap-2">
                  <MessageCircle size={16} className="text-pink-500 dark:text-pink-400 flex-shrink-0" />
                  <span className="text-gray-700 dark:text-gray-200 truncate">{conversation.title}</span>
                </div>
                {conversation.lastMessage && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate ml-6">
                    {conversation.lastMessage}
                  </p>
                )}
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteConversation(conversation.id);
                }}
                className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity p-1.5 hover:bg-gray-300 dark:hover:bg-gray-600 rounded"
              >
                <Trash2 size={14} className="text-gray-600 dark:text-gray-300" />
              </button>
            </div>
          ))}
        </div>
      </ScrollArea>
    </aside>
  );
}