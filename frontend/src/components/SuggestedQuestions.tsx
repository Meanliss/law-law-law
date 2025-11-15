import { MessageCircle, X } from 'lucide-react';
import { Button } from './ui/button';

interface SuggestedQuestionsProps {
  questions: string[];
  onSelectQuestion: (question: string) => void;
  onClear: () => void;
  isDarkMode: boolean;
}

export function SuggestedQuestions({ questions, onSelectQuestion, onClear, isDarkMode }: SuggestedQuestionsProps) {
  if (!questions || questions.length === 0) return null;

  return (
    <div
      className={`mb-4 p-4 rounded-lg animate-fade-in ${
        isDarkMode
          ? 'bg-gradient-to-r from-blue-900/20 to-purple-900/20 border border-blue-800/30'
          : 'bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200'
      }`}
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <MessageCircle size={18} className="text-blue-500 flex-shrink-0" />
          <h3 className={`text-sm font-semibold ${isDarkMode ? 'text-gray-200' : 'text-gray-700'}`}>
            Câu hỏi gợi ý
          </h3>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={onClear}
          className="h-6 w-6 p-0 hover:bg-gray-200 dark:hover:bg-gray-700"
        >
          <X size={14} className={isDarkMode ? 'text-gray-400' : 'text-gray-500'} />
        </Button>
      </div>

      <div className="space-y-2">
        {questions.map((question, index) => {
          // Extract question text (remove emoji if present)
          const cleanQuestion = question.replace(/^💭\s*/, '').trim();
          
          return (
            <button
              key={index}
              onClick={() => onSelectQuestion(cleanQuestion)}
              className={`w-full text-left p-3 rounded-lg transition-all ${
                isDarkMode
                  ? 'bg-gray-800/50 hover:bg-gray-800 text-gray-200 hover:border-blue-500'
                  : 'bg-white hover:bg-blue-50 text-gray-700 hover:border-blue-400'
              } border border-transparent hover:shadow-sm`}
            >
              <span className="text-sm leading-relaxed">{cleanQuestion}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
