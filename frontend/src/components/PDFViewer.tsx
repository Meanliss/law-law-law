// src/components/PDFViewer.tsx
import { useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Worker, Viewer } from '@react-pdf-viewer/core';
import { defaultLayoutPlugin } from '@react-pdf-viewer/default-layout';
import { searchPlugin } from '@react-pdf-viewer/search';
import '@react-pdf-viewer/core/lib/styles/index.css';
import '@react-pdf-viewer/default-layout/lib/styles/index.css';
import '@/styles/pdf-viewer.css';

interface PDFViewerProps {
  isOpen: boolean;
  onClose: () => void;
  pdfUrl: string;
  title: string;
  articleNum?: string;
}

export function PDFViewer({
  isOpen,
  onClose,
  pdfUrl,
  title,
  articleNum,
}: PDFViewerProps) {
  const defaultLayoutPluginInstance = defaultLayoutPlugin({
    sidebarTabs: () => [],
    renderToolbar: (Toolbar) => (
      <Toolbar>
        {(slots) => {
          const {
            CurrentPageInput,
            EnterFullScreen,
            GoToNextPage,
            GoToPreviousPage,
            NumberOfPages,
            ShowSearchPopover,
            Zoom,
            ZoomIn,
            ZoomOut,
          } = slots;
          return (
            <div className="flex items-center justify-between w-full px-2 py-1 bg-gray-50 dark:bg-gray-800 border-b dark:border-gray-700">
              <div className="flex items-center gap-1">
                <ZoomOut />
                <Zoom />
                <ZoomIn />
              </div>
              <div className="flex-1 max-w-xs mx-4">
                <ShowSearchPopover />
              </div>
              <div className="flex items-center gap-2 text-sm">
                <GoToPreviousPage />
                <CurrentPageInput /> / <NumberOfPages />
                <GoToNextPage />
                <EnterFullScreen />
              </div>
            </div>
          );
        }}
      </Toolbar>
    ),
  });

  const searchPluginInstance = searchPlugin();

  useEffect(() => {
    if (!isOpen || !articleNum) return;
    const timer = setTimeout(() => {
      searchPluginInstance.highlight(`Điều ${articleNum}`);
    }, 1000);
    return () => clearTimeout(timer);
  }, [isOpen, articleNum, searchPluginInstance]);

  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl w-[90vw] h-[90vh] p-0 flex flex-col overflow-hidden">
        <DialogHeader className="px-4 py-2 border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-800 flex-shrink-0">
          <DialogTitle className="text-sm font-bold dark:text-gray-100 flex items-center gap-2">
            <span className="truncate">{title}</span>
            {articleNum && (
              <span className="px-2 py-0.5 bg-gradient-to-r from-blue-500 to-purple-500 text-white text-xs rounded-full">
                Điều {articleNum}
              </span>
            )}
          </DialogTitle>
          <DialogDescription className="sr-only">Xem tài liệu PDF</DialogDescription>
        </DialogHeader>

        <div className="flex-shrink-0">
          {defaultLayoutPluginInstance.toolbarPluginInstance.renderDefaultLayoutToolbar?.()}
        </div>

        <div className="flex-1 overflow-auto bg-gray-100 dark:bg-gray-900">
          {pdfUrl ? (
            <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js">
              <div className="h-full min-h-screen">
                <Viewer
                  fileUrl={pdfUrl}
                  plugins={[defaultLayoutPluginInstance, searchPluginInstance]}
                  defaultScale={1.5}
                />
              </div>
            </Worker>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600 mx-auto mb-4" />
                <p className="text-lg font-medium dark:text-gray-100">Đang tải PDF...</p>
              </div>
            </div>
          )}
        </div>

        {articleNum && (
          <div className="px-4 py-1.5 border-t dark:border-gray-700 bg-yellow-50 dark:bg-yellow-900/10 text-xs flex-shrink-0">
            <p className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
              Tìm kiếm tự động:
              <mark className="bg-yellow-300 dark:bg-yellow-700 px-1 py-0.5 rounded font-bold">
                "Điều {articleNum}"
              </mark>
              • Dùng thanh tìm kiếm để điều hướng
            </p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}