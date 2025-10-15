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
    const highlightedSpans = new Set(); // Track already highlighted spans
    
    // Strategy 1: Highlight by EXACT article numbers (most precise)
    if (this.articleNumbers && this.articleNumbers.length > 0) {
      console.log('🔍 [Strategy 1] Looking for articles:', this.articleNumbers);
      
      this.articleNumbers.forEach(articleNum => {
        const normalizedArticle = this.normalizeText(articleNum);
        
        // Look for exact matches like "Điều 8" or "Dieu 8"
        spans.forEach((span, index) => {
          const spanText = span.textContent || '';
          const normalizedSpan = this.normalizeText(spanText);
          
          // Match patterns like "Điều 8." or "Điều 8:" or "Điều 8 "
          const patterns = [
            normalizedArticle + '.',
            normalizedArticle + ':',
            normalizedArticle + ' ',
            normalizedArticle + ','
          ];
          
          const isMatch = patterns.some(pattern => 
            normalizedSpan.includes(pattern) || 
            normalizedSpan === normalizedArticle
          );
          
          if (isMatch && !highlightedSpans.has(index)) {
            span.classList.add('highlight');
            highlightedSpans.add(index);
            highlightCount++;
            console.log(`✅ [Highlight] Found article: "${spanText}"`);
            
            // Highlight the TITLE of the article (next 3-5 spans)
            for (let i = 1; i <= 5 && index + i < spans.length; i++) {
              const nextSpan = spans[index + i];
              if (!highlightedSpans.has(index + i)) {
                nextSpan.classList.add('highlight');
                highlightedSpans.add(index + i);
                highlightCount++;
              }
              // Stop at the end of the title (when we hit content)
              const nextText = nextSpan.textContent || '';
              if (nextText.trim().length > 50) break;
            }
            
            // Highlight content below (next 15 spans for the article body)
            for (let i = 6; i <= 20 && index + i < spans.length; i++) {
              const nextSpan = spans[index + i];
              const nextText = this.normalizeText(nextSpan.textContent || '');
              
              // Stop if we hit another article
              if (nextText.match(/^dieu\s+\d+/) || nextText.match(/^chuong\s+/)) {
                break;
              }
              
              if (!highlightedSpans.has(index + i)) {
                nextSpan.classList.add('highlight');
                highlightedSpans.add(index + i);
                highlightCount++;
              }
            }
          }
        });
      });
    }
    
    // Strategy 2: Highlight by SPECIFIC content phrases (only if strategy 1 found nothing)
    if (highlightCount === 0 && this.highlightTexts && this.highlightTexts.length > 0) {
      console.log('🔍 [Strategy 2] Looking for specific content phrases');
      
      this.highlightTexts.forEach(text => {
        // Only use longer, specific phrases (> 20 characters)
        if (text.length < 20) return;
        
        const firstChunk = this.normalizeText(text.substring(0, 30));
        
        spans.forEach((span, index) => {
          const spanText = this.normalizeText(span.textContent || '');
          
          if (spanText.includes(firstChunk) && !highlightedSpans.has(index)) {
            // Highlight this span and next few
            for (let i = 0; i < 8 && index + i < spans.length; i++) {
              if (!highlightedSpans.has(index + i)) {
                spans[index + i].classList.add('highlight');
                highlightedSpans.add(index + i);
                highlightCount++;
              }
            }
          }
        });
      });
    }
    
    console.log(`🎯 [Highlight] Applied ${highlightCount} highlights to ${highlightedSpans.size} spans`);
    
    // NO FALLBACK - if nothing matches, show nothing highlighted
    if (highlightCount === 0) {
      console.warn('⚠️ [Highlight] No matches found. PDF will open without highlights.');
    }
  },

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
