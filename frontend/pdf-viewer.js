// PDF Viewer Panel with Text Highlighting

if (typeof pdfjsLib !== 'undefined') {
  pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
}

const PDFViewer = {
  pdfDoc: null,
  currentPage: 1,
  totalPages: 0,
  scale: 1.5,
  highlightTexts: [],
  isOpen: false,

  async open(pdfFile, highlightTexts = []) {
    const panel = document.getElementById('pdf-viewer-panel');
    panel.classList.add('active');
    this.isOpen = true;
    this.highlightTexts = highlightTexts;
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
      // POST request to avoid IDM detection (no .pdf in URL)
      const response = await fetch('http://localhost:8000/api/get-document', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename: filename })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log(`[PDF] Loaded ${data.filename}, size: ${data.size} bytes`);
      
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
      
      // Search for page with highlight text
      const pageWithHighlight = await this.findPageWithHighlight();
      this.currentPage = pageWithHighlight || 1;
      
      await this.renderPage(this.currentPage);
    } catch (error) {
      console.error('Error loading PDF:', error);
      alert('Không thể tải PDF: ' + error.message);
    }
  },
  
  async findPageWithHighlight() {
    if (!this.highlightTexts || this.highlightTexts.length === 0) return 1;
    
    console.log('[PDF] Searching for highlights:', this.highlightTexts);
    
    // Search through all pages
    for (let pageNum = 1; pageNum <= this.totalPages; pageNum++) {
      const page = await this.pdfDoc.getPage(pageNum);
      const textContent = await page.getTextContent();
      const pageText = textContent.items.map(item => item.str).join(' ').toLowerCase();
      
      // Check if any highlight text is in this page
      for (const searchText of this.highlightTexts) {
        const normalized = this.normalizeText(searchText.toLowerCase());
        if (pageText.includes(normalized) || normalized.includes(pageText)) {
          console.log(`[PDF] Found highlight on page ${pageNum}`);
          return pageNum;
        }
      }
    }
    
    console.log('[PDF] No highlight found, starting at page 1');
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
    
    // Set text layer size to match canvas
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
    setTimeout(() => this.applyHighlights(textLayer), 300);
  },

  applyHighlights(textLayer) {
    if (!this.highlightTexts || this.highlightTexts.length === 0) return;
    
    console.log('[Highlight] Texts to highlight:', this.highlightTexts);
    
    const spans = textLayer.querySelectorAll('span');
    let highlightCount = 0;
    
    // Build full page text for context matching
    let fullPageText = '';
    const spanMap = [];
    spans.forEach((span, index) => {
      const text = span.textContent || '';
      spanMap.push({
        span: span,
        start: fullPageText.length,
        end: fullPageText.length + text.length,
        text: text
      });
      fullPageText += text;
    });
    
    const normalizedPageText = this.normalizeText(fullPageText.toLowerCase());
    
    // For each highlight text, find exact matches in page
    this.highlightTexts.forEach(searchText => {
      const normalizedSearch = this.normalizeText(searchText.toLowerCase());
      
      // Find all occurrences of search text in page
      let startPos = 0;
      while ((startPos = normalizedPageText.indexOf(normalizedSearch, startPos)) !== -1) {
        const endPos = startPos + normalizedSearch.length;
        
        // Find spans that overlap with this match
        spanMap.forEach(item => {
          if (item.start < endPos && item.end > startPos) {
            item.span.classList.add('highlight');
            highlightCount++;
          }
        });
        
        startPos = endPos;
      }
    });
    
    console.log(`[Highlight] Applied ${highlightCount} highlights`);
  },

  normalizeText(text) {
    return text
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
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
