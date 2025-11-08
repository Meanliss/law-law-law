import { motion, AnimatePresence } from 'motion/react';
import { X, FileText, ExternalLink } from 'lucide-react';
import { Button } from './ui/button';
import { useState, useEffect } from 'react';

interface PDFViewerProps {
  isOpen: boolean;
  url: string;
  title: string;
  articleNum?: string;
  pageNum?: number;
  onClose: () => void;
}

export function PDFViewer({ isOpen, url, title, articleNum, pageNum, onClose }: PDFViewerProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [pdfLoaded, setPdfLoaded] = useState(false);

  // ✅ Build URL with page number for auto-scroll
  const pdfUrlWithPage = pageNum && pageNum > 0 ? `${url}#page=${pageNum}` : url;

  // ✅ Notification khi mở PDF với điều cụ thể
  useEffect(() => {
    console.log('[PDFViewer] useEffect:', { isOpen, articleNum, pageNum, url });
    if (isOpen && articleNum) {
      setPdfLoaded(false);
      const searchText = `Điều ${articleNum}`;
      setSearchQuery(searchText);
      
      // Delay để hiển thị notification
      setTimeout(() => setPdfLoaded(true), 500);
    }
  }, [isOpen, articleNum, pageNum]);

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
              
              <div className="relative z-10 p-6 border-b border-gray-200/50 dark:border-gray-700/50">
                {/* Tiêu đề và nút đóng */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-500 via-cyan-500 to-teal-500 flex items-center justify-center shadow-lg">
                      <FileText size={20} className="text-white" />
                    </div>
                    <div>
                      <h2 className="font-semibold text-gray-900 dark:text-gray-100">
                        {title}
                      </h2>
                      {articleNum && (
                        <p className="text-sm text-blue-600 dark:text-cyan-400 font-medium">
                          📍 Điều {articleNum}
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

                {/* Search/Highlight Box */}
                {articleNum && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-500/10 dark:bg-blue-500/5 border border-blue-500/30 dark:border-blue-500/20"
                  >
                    <motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ duration: 1.5, repeat: Infinity }}>
                      <FileText size={16} className="text-blue-600 dark:text-cyan-400" />
                    </motion.div>
                    <span className="text-sm text-blue-600 dark:text-cyan-400 font-medium">
                      🔍 Tìm kiếm: Điều {articleNum}
                    </span>
                  </motion.div>
                )}
              </div>
            </div>

            {/* PDF Content */}
            <div className="flex-1 overflow-hidden bg-gray-100 dark:bg-gray-950">
              {/* ✅ Cách 1: Dùng embed tag (tốt hơn iframe cho PDF) */}
              <embed
                src={pdfUrlWithPage}
                type="application/pdf"
                className="w-full h-full"
                title={title}
              />
              
              {/* ✅ Fallback: Nếu PDF không load, show button để open ở tab mới */}
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-900 dark:to-gray-950 pointer-events-none">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 2 }}
                  className="pointer-events-auto text-center space-y-4"
                >
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    Không thể hiển thị PDF trong trình duyệt
                  </p>
                  <Button
                    onClick={() => window.open(pdfUrlWithPage, '_blank')}
                    className="gap-2 bg-blue-600 hover:bg-blue-700"
                  >
                    <ExternalLink size={16} />
                    Mở PDF ở tab mới
                  </Button>
                </motion.div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
