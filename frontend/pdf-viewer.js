// PDF Viewer Panel with Smart Text Highlighting

if (typeof pdfjsLib !== 'undefined') {
  pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
}

const PDFViewer = {
  pdfDoc: null,
  currentPage: 1,
  totalPages: 0,
  scale: 1.5,
  highlightTexts: [],
  articleNumbers: [],
  isOpen: false,

  async open(pdfFile, highlightTexts = [], articleNumbers = []) {
    const panel = document.getElementById('pdf-viewer-panel');
    panel.classList.add('active');
    this.isOpen = true;
    this.highlightTexts = highlightTexts;
    this.articleNumbers = articleNumbers;
    
    console.log('📖 [PDF] Opening:', pdfFile);
    console.log('🔍 [PDF] Highlight texts:', highlightTexts);
    console.log('📋 [PDF] Article numbers:', articleNumbers);
    
    document.getElementById('pdf-title').textContent = pdfFile;
    await this.loadPDF(pdfFile);
  },

  close() {
    document.getElementById('pdf-viewer-panel').classList.remove('active');
    this.isOpen = false;
    this.pdfDoc = null;
    this.currentPage = 1;
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
      
      // Load PDF from bytes
      const loadingTask = pdfjsLib.getDocument({ data: bytes });
      this.pdfDoc = await loadingTask.promise;
      this.totalPages = this.pdfDoc.numPages;
      
      console.log(`📄 [PDF] Total pages: ${this.totalPages}`);
      
      // Search for page with article or highlight text
      const pageWithHighlight = await this.findPageWithHighlight();
      this.currentPage = pageWithHighlight || 1;
      
      await this.renderPage(this.currentPage);
    } catch (error) {
      console.error('❌ [PDF] Error loading PDF:', error);
      alert('Không thể tải PDF: ' + error.message);
    }
  },
  
  async findPageWithHighlight() {
    console.log('🔍 [PDF] Searching for highlights across all pages...');
    
    // Search through all pages
    for (let pageNum = 1; pageNum <= this.totalPages; pageNum++) {
      const page = await this.pdfDoc.getPage(pageNum);
      const textContent = await page.getTextContent();
      const pageText = textContent.items.map(item => item.str).join(' ');
      
      // Check for article numbers first (most reliable)
      if (this.articleNumbers && this.articleNumbers.length > 0) {
        for (const articleNum of this.articleNumbers) {
          const normalized = this.normalizeText(articleNum);
          const pageNormalized = this.normalizeText(pageText);
          
          if (pageNormalized.includes(normalized)) {
            console.log(`✅ [PDF] Found article "${articleNum}" on page ${pageNum}`);
            return pageNum;
          }
        }
      }
      
      // Check for highlight text content
      if (this.highlightTexts && this.highlightTexts.length > 0) {
        for (const searchText of this.highlightTexts) {
          // Extract key phrases (first 50 chars)
          const keyPhrase = searchText.substring(0, 50);
          const normalized = this.normalizeText(keyPhrase);
          const pageNormalized = this.normalizeText(pageText);
          
          if (pageNormalized.includes(normalized)) {
            console.log(`✅ [PDF] Found content on page ${pageNum}`);
            return pageNum;
          }
        }
      }
    }
    
    console.log('⚠️ [PDF] No matches found, starting at page 1');
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
    
    // Render text layer with PDF.js
    await pdfjsLib.renderTextLayer({
      textContentSource: textContent,
      container: textLayer,
      viewport: viewport,
      textDivs: []
    }).promise;
    
    // Apply highlights after text is fully rendered
    setTimeout(() => this.applyHighlights(textLayer), 500);
  },

  applyHighlights(textLayer) {
    console.log('🎨 [Highlight] Starting highlight process...');
    
    const spans = textLayer.querySelectorAll('span');
    console.log(`📝 [Highlight] Found ${spans.length} text spans`);
    
    if (spans.length === 0) {
      console.error('❌ [Highlight] No spans found in text layer!');
      return;
    }
    
    let highlightCount = 0;
    
    // ONLY highlight if we have article numbers - no fuzzy matching!
    if (!this.articleNumbers || this.articleNumbers.length === 0) {
      console.warn('⚠️ [Highlight] No article numbers provided. Skipping highlights.');
      return;
    }
    
    console.log('🔍 [Highlight] Looking for articles:', this.articleNumbers);
    
    // Find the starting point of each article
    this.articleNumbers.forEach(articleNum => {
      const normalizedArticle = this.normalizeText(articleNum);
      console.log('🔎 [Highlight] Searching for:', normalizedArticle);
      
      let foundArticle = false;
      
      for (let i = 0; i < spans.length; i++) {
        const span = spans[i];
        const spanText = span.textContent || '';
        const normalizedSpan = this.normalizeText(spanText);
        
        // Look for exact article header like "Điều 8." or "Điều 8:"
        const isArticleHeader = 
          normalizedSpan.startsWith(normalizedArticle + '.') ||
          normalizedSpan.startsWith(normalizedArticle + ':') ||
          normalizedSpan.startsWith(normalizedArticle + ' ') ||
          normalizedSpan === normalizedArticle;
        
        if (isArticleHeader && !foundArticle) {
          foundArticle = true;
          console.log(`✅ [Highlight] Found article at span ${i}: "${spanText}"`);
          
          // Highlight the article number itself
          span.classList.add('highlight');
          highlightCount++;
          
          // Highlight the article title (usually next 1-3 spans)
          let titleLength = 0;
          for (let j = i + 1; j < spans.length && titleLength < 3; j++) {
            const nextSpan = spans[j];
            const nextText = nextSpan.textContent || '';
            
            nextSpan.classList.add('highlight');
            highlightCount++;
            titleLength++;
            
            // Stop at line break or when we hit numbered items (1., a., etc.)
            if (nextText.match(/^\s*\d+\./) || nextText.match(/^\s*[a-z]\)/)) {
              break;
            }
          }
          
          // Highlight the first paragraph/item (usually next 10-15 spans after title)
          let contentLength = 0;
          const startContent = i + titleLength + 1;
          
          for (let j = startContent; j < spans.length && contentLength < 15; j++) {
            const contentSpan = spans[j];
            const contentText = this.normalizeText(contentSpan.textContent || '');
            
            // Stop if we hit another article
            if (contentText.match(/^dieu\s+\d+/)) {
              console.log(`🛑 [Highlight] Stopped at next article: ${contentSpan.textContent}`);
              break;
            }
            
            // Stop if we hit another chapter
            if (contentText.match(/^chuong\s+/)) {
              console.log(`🛑 [Highlight] Stopped at next chapter`);
              break;
            }
            
            contentSpan.classList.add('highlight');
            highlightCount++;
            contentLength++;
          }
          
          // Don't look for this article again
          break;
        }
      }
      
      if (!foundArticle) {
        console.warn(`⚠️ [Highlight] Article "${articleNum}" not found on this page`);
      }
    });
    
    console.log(`🎯 [Highlight] Total highlights applied: ${highlightCount}`);
    
    if (highlightCount === 0) {
      console.warn('⚠️ [Highlight] No highlights applied. Article may be on a different page.');
    }
  },  // ⚠️ THIS COMMA WAS MISSING! ⚠️

  normalizeText(text) {
    if (!text) return '';
    return text
      .toString()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/[đĐ]/g, 'd')
      .trim();
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
