// Simple PDF Viewer using browser's native PDF renderer

const PDFViewer = {
  isOpen: false,

  async open(pdfFile, highlightTexts = [], articleNumbers = []) {
    const panel = document.getElementById('pdf-viewer-panel');
    panel.classList.add('active');
    this.isOpen = true;
    
    console.log('📖 [PDF] Opening:', pdfFile);
    console.log('📋 [PDF] Articles:', articleNumbers);
    
    document.getElementById('pdf-title').textContent = pdfFile;
    await this.loadPDF(pdfFile, articleNumbers);
  },

  close() {
    document.getElementById('pdf-viewer-panel').classList.remove('active');
    this.isOpen = false;
    const iframe = document.getElementById('pdf-iframe');
    if (iframe) {
      iframe.src = '';
    }
  },

  async loadPDF(filename, articleNumbers) {
    try {
      // Auto-detect API base URL
      const API_BASE = (() => {
        if (window.location.hostname.includes('pages.dev') || 
            window.location.hostname.includes('cloudflare')) {
          return 'https://eddiethewall-legal-qa-backend.hf.space';
        } else if (window.location.hostname === 'localhost' || 
                   window.location.hostname === '127.0.0.1') {
          return 'http://localhost:7860';
        } else {
          return 'https://eddiethewall-legal-qa-backend.hf.space';
        }
      })();
      
      console.log('🔗 [PDF] Fetching from:', `${API_BASE}/api/get-document`);
      
      const response = await fetch(`${API_BASE}/api/get-document`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: filename })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log(`✅ [PDF] Loaded ${data.filename}, size: ${data.size} bytes`);
      
      // Convert base64 to blob
      const binaryString = atob(data.data);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      
      const blob = new Blob([bytes], { type: 'application/pdf' });
      const blobUrl = URL.createObjectURL(blob);
      
      // Estimate page number from article
      let pageNum = 1;
      if (articleNumbers && articleNumbers.length > 0) {
        pageNum = this.estimatePageFromArticle(articleNumbers[0]);
      }
      
      // Load PDF in iframe with native viewer
      const iframe = document.getElementById('pdf-iframe');
      iframe.src = `${blobUrl}#page=${pageNum}&view=FitH`;
      
      console.log(`📄 [PDF] Loaded in iframe, jumping to page ${pageNum}`);
      
      // Show article info
      this.showArticleInfo(articleNumbers);
      
    } catch (error) {
      console.error('❌ [PDF] Error loading PDF:', error);
      alert('Không thể tải PDF: ' + error.message);
    }
  },

  estimatePageFromArticle(articleNum) {
    // Extract article number (e.g., "Dieu 8" -> 8)
    const match = articleNum.match(/\d+/);
    if (!match) return 1;
    
    const num = parseInt(match[0]);
    
    // Rough estimate: articles are usually ~1-2 pages each
    // Start from page 5 (skip cover/intro) + article number
    return Math.max(1, 5 + num);
  },

  showArticleInfo(articleNumbers) {
    const infoDiv = document.getElementById('article-info');
    if (!infoDiv) return;
    
    if (articleNumbers && articleNumbers.length > 0) {
      const articles = articleNumbers.map(a => a.replace('Dieu', 'Điều')).join(', ');
      infoDiv.innerHTML = `
        <div style="padding: 12px; background: rgba(255, 235, 59, 0.2); border-left: 4px solid #ffc107; margin-bottom: 8px;">
          <strong>📍 Tìm kiếm:</strong> ${articles}
          <div style="font-size: 0.85em; opacity: 0.8; margin-top: 4px;">
            Sử dụng Ctrl+F để tìm kiếm trong PDF
          </div>
        </div>
      `;
    } else {
      infoDiv.innerHTML = '';
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('close-pdf')?.addEventListener('click', () => PDFViewer.close());
  
  document.addEventListener('keydown', (e) => {
    if (PDFViewer.isOpen && e.key === 'Escape') {
      PDFViewer.close();
    }
  });
});

window.PDFViewer = PDFViewer;
