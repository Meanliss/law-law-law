// src/components/PDFViewer.tsx
import { motion, AnimatePresence } from 'motion/react';
import { X, FileText } from 'lucide-react';
import { Button } from './ui/button';

interface PDFViewerProps {
  isOpen: boolean;
  pdfUrl: string; // Đổi từ url -> pdfUrl
  title: string;
  articleNum?: string;
  onClose: () => void;
}

export function PDFViewer({ isOpen, pdfUrl, title, articleNum, onClose }: PDFViewerProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="fixed inset-4 md:inset-8 z-50 flex flex-col overflow-hidden rounded-3xl backdrop-blur-2xl bg-white/95 dark:bg-gray-900/95 border border-gray-200/50 dark:border-gray-700/50 shadow-2xl"
          >
            {/* Header with Glass Effect */}
            <div className="flex-shrink-0 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-cyan-500/10 to-teal-500/10 dark:from-blue-500/5 dark:via-cyan-500/5 dark:to-teal-500/5" />

              <div className="relative z-10 flex items-center justify-between p-4 md:p-6 border-b border-gray-200/50 dark:border-gray-700/50">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-500 via-cyan-500 to-teal-500 flex items-center justify-center shadow-lg">
                    <FileText size={20} className="text-white" />
                  </div>
                  <div>
                    <h2 className="font-semibold text-gray-900 dark:text-gray-100 text-sm md:text-base">
                      {title}
                    </h2>
                    {articleNum && (
                      <p className="text-xs md:text-sm text-blue-600 dark:text-cyan-400 font-medium">
                        📍 Đang xem: Điều {articleNum}
                      </p>
                    )}
                  </div>
                </div>

                <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
                  <Button
                    onClick={onClose}
                    variant="ghost"
                    className="w-10 h-10 p-0 rounded-2xl hover:bg-gray-200/50 dark:hover:bg-gray-800/50"
                  >
                    <X size={20} />
                  </Button>
                </motion.div>
              </div>
            </div>

            {/* PDF Content */}
            <div className="flex-1 overflow-hidden bg-gray-100 dark:bg-gray-900">
              {pdfUrl ? (
                <iframe
                  src={`${pdfUrl}#page=1&zoom=120`}
                  className="w-full h-full border-0"
                  title={title}
                />
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600 mx-auto mb-4" />
                    <p className="text-lg font-medium dark:text-gray-100">Đang tải PDF...</p>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}