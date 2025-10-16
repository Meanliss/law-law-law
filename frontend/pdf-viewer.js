// PDF Viewer with Auto-Highlight using PDF.js

if (typeof pdfjsLib !== 'undefined') {
  pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
}

const PDFViewer = {
  pdfDoc: null,
  currentPage: 1,
  totalPages: 0,
  scale: 1.5,
  isOpen: false,
  searchTerms: [],

  async open(pdfFile, highlightTexts = [], articleNumbers = []) {
    const panel = document.getElementById('pdf-viewer-panel');
    panel.classList.add('active');
    this.isOpen = true;
    
    // Format article numbers for display (e.g., "Dieu 8" -> "Điều 8")
    this.searchTerms = articleNumbers.map(a => a.replace(/Dieu/i, 'Điều'));
    
    console.log('📖 [PDF] Opening:', pdfFile);
    console.log('📋 [PDF] Will search for:', this.searchTerms);
    
    document.getElementById('pdf-title').textContent = pdfFile;
    await this.loadPDF(pdfFile);
  },

  close() {
    document.getElementById('pdf-viewer-panel').classList.remove('active');
    this.isOpen = false;
    this.pdfDoc = null;
    this.currentPage = 1;
    this.searchTerms = [];
  },

  async loadPDF(filename) {
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
      
      // Convert base64 to Uint8Array
      const binaryString = atob(data.data);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      
      // Load PDF with PDF.js
      const loadingTask = pdfjsLib.getDocument({ data: bytes });
      this.pdfDoc = await loadingTask.promise;
      this.totalPages = this.pdfDoc.numPages;
      
      console.log(`📄 [PDF] Total pages: ${this.totalPages}`);
      
      // Find page with first search term
      if (this.searchTerms.length > 0) {
        const pageNum = await this.findPageWithText(this.searchTerms[0]);
        this.currentPage = pageNum || 1;
      }
      
      await this.renderPage(this.currentPage);
      this.showSearchInfo();
      
    } catch (error) {
      console.error('❌ [PDF] Error loading PDF:', error);
      alert('Không thể tải PDF: ' + error.message);
    }
  },

  async findPageWithText(searchText) {
    console.log('🔍 [PDF] Searching for:', searchText);
    
    // Search through all pages
    for (let pageNum = 1; pageNum <= this.totalPages; pageNum++) {
      const page = await this.pdfDoc.getPage(pageNum);
      const textContent = await page.getTextContent();
      const pageText = textContent.items.map(item => item.str).join(' ');
      
      if (pageText.includes(searchText)) {
        console.log(`✅ [PDF] Found "${searchText}" on page ${pageNum}`);
        return pageNum;
      }
    }
    
    console.log(`⚠️ [PDF] "${searchText}" not found`);
    return 1;
  },

  async renderPage(pageNum) {
    if (!this.pdfDoc || pageNum < 1 || pageNum > this.totalPages) return;
    
    this.currentPage = pageNum;
    const page = await this.pdfDoc.getPage(pageNum);
    const canvas = document.getElementById('pdf-canvas');
    const context = canvas.getContext('2d');
    const viewport = page.getViewport({ scale: this.scale });
    
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    
    await page.render({ canvasContext: context, viewport: viewport }).promise;
    await this.renderTextLayer(page, viewport);
    
    document.getElementById('current-page').textContent = pageNum;
    document.getElementById('total-pages').textContent = this.totalPages;
    document.getElementById('prev-page').disabled = pageNum <= 1;
    document.getElementById('next-page').disabled = pageNum >= this.totalPages;
  },

  async renderTextLayer(page, viewport) {
    const textContent = await page.getTextContent();
    const textLayer = document.getElementById('text-layer');
    textLayer.innerHTML = '';
    
    textLayer.style.width = viewport.width + 'px';
    textLayer.style.height = viewport.height + 'px';
    
    // Render text layer
    await pdfjsLib.renderTextLayer({
      textContentSource: textContent,
      container: textLayer,
      viewport: viewport,
      textDivs: []
    }).promise;
    
    // Auto-highlight search terms
    setTimeout(() => this.highlightSearchTerms(textLayer), 300);
  },

  highlightSearchTerms(textLayer) {
    if (!this.searchTerms || this.searchTerms.length === 0) return;
    
    console.log('🎨 [Highlight] Highlighting:', this.searchTerms);
    
    const spans = textLayer.querySelectorAll('span');
    let highlightCount = 0;
    
    this.searchTerms.forEach(term => {
      spans.forEach((span, index) => {
        const spanText = span.textContent || '';
        
        // Check if span contains the search term
        if (spanText.includes(term)) {
          span.classList.add('highlight');
          highlightCount++;
          
          // Highlight next 15 spans for context
          for (let i = 1; i <= 15 && index + i < spans.length; i++) {
            const nextSpan = spans[index + i];
            const nextText = nextSpan.textContent || '';
            
            // Stop at next article
            if (nextText.match(/Điều\s+\d+/)) break;
            
            nextSpan.classList.add('highlight');
          }
        }
      });
    });
    
    console.log(`✅ [Highlight] Applied ${highlightCount} highlights`);
  },

  showSearchInfo() {
    const infoDiv = document.getElementById('article-info');
    if (!infoDiv) return;
    
    if (this.searchTerms.length > 0) {
      infoDiv.innerHTML = `
        <div style="padding: 12px; background: rgba(255, 235, 59, 0.2); border-left: 4px solid #ffc107; margin: 8px;">
          <strong>🔍 Đã tìm thấy và tô sáng:</strong> ${this.searchTerms.join(', ')}
          <div style="font-size: 0.85em; opacity: 0.8; margin-top: 4px;">
            📍 Trang ${this.currentPage} | Sử dụng mũi tên để chuyển trang
          </div>
        </div>
      `;
    } else {
      infoDiv.innerHTML = '';
    }
  },

  nextPage() {
    if (this.currentPage < this.totalPages) this.renderPage(this.currentPage + 1);
  },

  prevPage() {
    if (this.currentPage > 1) this.renderPage(this.currentPage - 1);
  }
};

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('close-pdf')?.addEventListener('click', () => PDFViewer.close());
  document.getElementById('next-page')?.addEventListener('click', () => PDFViewer.nextPage());
  document.getElementById('prev-page')?.addEventListener('click', () => PDFViewer.prevPage());
  
  document.addEventListener('keydown', (e) => {
    if (!PDFViewer.isOpen) return;
    if (e.key === 'Escape') PDFViewer.close();
    else if (e.key === 'ArrowRight') PDFViewer.nextPage();
    else if (e.key === 'ArrowLeft') PDFViewer.prevPage();
  });
});

window.PDFViewer = PDFViewer;
