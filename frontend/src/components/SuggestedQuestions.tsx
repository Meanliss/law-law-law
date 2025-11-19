import { useState, MouseEvent } from 'react';
import { X, ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import { Button } from './ui/button';

interface SuggestedQuestionsProps {
  questions: string[];
  onSelectQuestion: (question: string) => void;
  onClear: () => void;
  isDarkMode: boolean;
}

export function SuggestedQuestions({ questions, onSelectQuestion, onClear, isDarkMode }: SuggestedQuestionsProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!questions || questions.length === 0) return null;

  // Limit to 2 questions as requested
  const displayQuestions = questions.slice(0, 2);

  return (
    <div
      className={`mb-2 rounded-lg transition-all duration-300 ${
        isDarkMode
          ? 'bg-gradient-to-r from-blue-900/20 to-purple-900/20 border border-blue-800/30'
          : 'bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200'
      }`}
    >
      <div 
        className="flex items-center justify-between p-2 cursor-pointer hover:opacity-80 transition-opacity"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-blue-500" />
          <span className={`text-xs font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
            {isExpanded ? 'Gợi ý câu hỏi tiếp theo' : 'Xem gợi ý câu hỏi tiếp theo'}
          </span>
        </div>
        <div className="flex items-center gap-1">
          {isExpanded ? (
            <ChevronDown size={16} className={isDarkMode ? 'text-gray-400' : 'text-gray-500'} />
          ) : (
            <ChevronUp size={16} className={isDarkMode ? 'text-gray-400' : 'text-gray-500'} />
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={(e: MouseEvent) => {
              e.stopPropagation();
              onClear();
            }}
            className="h-5 w-5 p-0 hover:bg-gray-200 dark:hover:bg-gray-700 ml-1"
          >
            <X size={14} className={isDarkMode ? 'text-gray-400' : 'text-gray-500'} />
          </Button>
        </div>
      </div>

      {isExpanded && (
        <div className="px-2 pb-2 space-y-2 animate-in slide-in-from-top-1 fade-in duration-200">
          {displayQuestions.map((question, index) => {
            // Extract question text (remove emoji if present)
            const cleanQuestion = question.replace(/^💭\s*/, '').trim();
            
            return (
              <button
                key={index}
                onClick={() => onSelectQuestion(cleanQuestion)}
                className={`w-full text-left p-2 rounded-md text-xs transition-all ${
                  isDarkMode
                    ? 'bg-gray-800/50 hover:bg-gray-800 text-gray-200 hover:border-blue-500'
                    : 'bg-white hover:bg-blue-50 text-gray-700 hover:border-blue-400'
                } border border-transparent hover:shadow-sm truncate`}
              >
                <span className="truncate">{cleanQuestion}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
