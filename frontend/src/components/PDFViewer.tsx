import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { ScrollArea } from './ui/scroll-area';

interface PDFViewerProps {
  isOpen: boolean;
  onClose: () => void;
  pdfUrl: string;
  title: string;
}

export function PDFViewer({ isOpen, onClose, pdfUrl, title }: PDFViewerProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl h-[90vh] p-0 dark:bg-gray-800">
        <DialogHeader className="px-6 py-4 border-b dark:border-gray-700">
          <DialogTitle className="dark:text-gray-100">{title}</DialogTitle>
          <DialogDescription className="sr-only">
            Xem tài liệu pháp luật PDF
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="flex-1 h-full">
          <div className="p-6">
            <iframe
              src={pdfUrl}
              className="w-full h-[calc(90vh-100px)] border-0 rounded"
              title={title}
            />
            <div className="mt-4 p-4 bg-blue-50 dark:bg-gray-700 rounded">
              <p className="text-sm text-gray-700 dark:text-gray-300">
                📄 <strong>Lưu ý:</strong> Đây là tài liệu PDF mô phỏng. Trong ứng dụng thực tế, 
                backend sẽ cung cấp file PDF từ cơ sở dữ liệu pháp luật Việt Nam.
              </p>
            </div>
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}