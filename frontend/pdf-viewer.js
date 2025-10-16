// Simple Native PDF Viewer - No Canvas, No Lag

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
      
      // Use different URL parameters for different browsers
      const userAgent = navigator.userAgent.toLowerCase();
      if (userAgent.includes('chrome') || userAgent.includes('edge')) {
        iframe.src = `${blobUrl}#page=${pageNum}&view=FitH&zoom=125`;
      } else if (userAgent.includes('firefox')) {
        iframe.src = `${blobUrl}#page=${pageNum}`;
      } else {
        iframe.src = blobUrl;
      }
      
      console.log(`📄 [PDF] Loaded in iframe, jumping to page ${pageNum}`);
      
      // Show search instructions with copy button
      this.showSearchInstructions(articleNumbers);
      
    } catch (error) {
      console.error('❌ [PDF] Error loading PDF:', error);
      alert('Không thể tải PDF: ' + error.message);
    }
  },

  estimatePageFromArticle(articleNum) {
    const match = articleNum.match(/\d+/);
    if (!match) return 1;
    
    const num = parseInt(match[0]);
    
    if (num <= 10) {
      return 5 + num;
    } else if (num <= 50) {
      return 15 + Math.floor(num / 2);
    } else {
      return 60 + Math.floor((num - 50) / 3);
    }
  },

  showSearchInstructions(articleNumbers) {
    const infoDiv = document.getElementById('article-info');
    if (!infoDiv) return;
    
    if (articleNumbers && articleNumbers.length > 0) {
      // Format articles nicely (Dieu 8 -> Điều 8)
      const formattedArticles = articleNumbers
        .map(a => a.replace(/Dieu/i, 'Điều'))
        .join(', ');
      
      infoDiv.innerHTML = `
        <div style="padding: 16px; background: linear-gradient(135deg, rgba(255, 235, 59, 0.15) 0%, rgba(255, 193, 7, 0.15) 100%); border-left: 4px solid #ffc107; margin: 12px;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <span style="font-size: 20px;">🔍</span>
            <strong style="font-size: 16px;">Tìm kiếm trong PDF:</strong>
          </div>
          
          <div style="background: rgba(255, 255, 255, 0.6); padding: 12px; border-radius: 6px; margin-bottom: 12px;">
            <div style="font-size: 15px; font-weight: 600; color: #d84315; margin-bottom: 8px;">
              ${formattedArticles}
            </div>
            <button 
              onclick="navigator.clipboard.writeText('${formattedArticles}').then(() => alert('✅ Đã copy: ${formattedArticles}\\n\\nBước tiếp:\\n1️⃣ Nhấn Ctrl+F\\n2️⃣ Nhấn Ctrl+V (paste)\\n3️⃣ Nhấn Enter')).catch(() => alert('❌ Không thể copy. Vui lòng copy thủ công.'));" 
              style="padding: 8px 16px; background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600; box-shadow: 0 2px 4px rgba(0,0,0,0.2); transition: transform 0.2s;"
              onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.3)';"
              onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(0,0,0,0.2)';">
              📋 Copy để tìm kiếm
            </button>
          </div>
          
          <div style="font-size: 13px; opacity: 0.85; line-height: 1.8; background: rgba(255, 255, 255, 0.3); padding: 10px; border-radius: 6px;">
            <div style="font-weight: 600; margin-bottom: 6px;">💡 Cách tìm kiếm:</div>
            <div>1️⃣ Nhấn nút <strong>"Copy để tìm kiếm"</strong> ở trên</div>
            <div>2️⃣ Nhấn <kbd style="background: #fff; padding: 2px 6px; border-radius: 3px; border: 1px solid #ccc; font-family: monospace;">Ctrl+F</kbd> (Windows) hoặc <kbd style="background: #fff; padding: 2px 6px; border-radius: 3px; border: 1px solid #ccc; font-family: monospace;">Cmd+F</kbd> (Mac)</div>
            <div>3️⃣ Nhấn <kbd style="background: #fff; padding: 2px 6px; border-radius: 3px; border: 1px solid #ccc; font-family: monospace;">Ctrl+V</kbd> để paste</div>
            <div>4️⃣ Nhấn <kbd style="background: #fff; padding: 2px 6px; border-radius: 3px; border: 1px solid #ccc; font-family: monospace;">Enter</kbd> → Trình duyệt sẽ tô sáng!</div>
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
