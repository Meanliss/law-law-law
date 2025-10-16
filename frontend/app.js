document.addEventListener('DOMContentLoaded', () => {
  const chatDisplay = document.getElementById('chat-display');
  const userInput = document.getElementById('user-input');
  const sendButton = document.getElementById('send-button');
  const themeToggle = document.getElementById('theme-toggle');
  const newChatBtn = document.getElementById('new-chat');
  const chatList = document.getElementById('chat-list');
  const chatTitle = document.getElementById('chat-title');
  const modeFast = document.getElementById('mode-fast');
  const modeQuality = document.getElementById('mode-quality');

  // QUAN TRỌNG: Đang sử dụng biến JavaScript (lưu trong RAM)
  // Nếu muốn lưu vĩnh viễn, uncomment các dòng localStorage bên dưới
  let chats = [];
  let currentChatId = null;
  let isDark = false;
  let modelMode = 'quality'; // 'fast' hoặc 'quality'

  // ===== CÁCH DÙNG localStorage (Chỉ khi chạy local) =====
  // Bước 1: Comment 3 dòng trên
  // Bước 2: Uncomment 3 dòng dưới đây:
  // let chats = JSON.parse(localStorage.getItem('chats')) || [];
  // let currentChatId = localStorage.getItem('currentChatId');
  // let isDark = localStorage.getItem('theme') === 'dark';

  // Tự động điều chỉnh chiều cao textarea
  function autoResizeTextarea() {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 200) + 'px';
  }

  userInput.addEventListener('input', autoResizeTextarea);

  // Tạo hội thoại mới
  function createNewChat() {
    const newChat = {
      id: Date.now(),
      title: "Hội thoại mới",
      messages: []
    };
    chats.push(newChat);
    currentChatId = newChat.id;
    saveChats();
    renderSidebar();
    renderChat(newChat);
  }

  // Lưu chats
  function saveChats() {
    // Nếu dùng localStorage, uncomment dòng dưới:
    // localStorage.setItem('chats', JSON.stringify(chats));
    // localStorage.setItem('currentChatId', currentChatId);
  }

  // Render sidebar
  function renderSidebar() {
    chatList.innerHTML = '';
    chats.slice().reverse().forEach(chat => {
      const li = document.createElement('li');
      li.textContent = chat.title;
      li.classList.toggle('active', chat.id === currentChatId);
      li.onclick = () => {
        currentChatId = chat.id;
        renderChat(chat);
        renderSidebar();
      };
      chatList.appendChild(li);
    });
  }

  // Render một chat
  function renderChat(chat) {
    chatDisplay.innerHTML = '';
    chatTitle.textContent = chat.title;
    chat.messages.forEach(msg => {
      addMessage(msg.text, msg.sender, false, false);
    });
    chatDisplay.scrollTop = chatDisplay.scrollHeight;
  }

  // Thêm tin nhắn
  function addMessage(text, sender, save = true, animated = true) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);

    if (animated) {
      messageDiv.style.animation = 'slideIn 0.3s ease-out';
    }

    // Fix: Chuyển \n thành <br> để hiển thị xuống dòng
    const formattedText = text.replace(/\n/g, '<br>');
    messageDiv.innerHTML = formattedText;
    chatDisplay.appendChild(messageDiv);
    chatDisplay.scrollTop = chatDisplay.scrollHeight;

    if (save && currentChatId) {
      const chat = chats.find(c => c.id === currentChatId);
      chat.messages.push({ text, sender });
      
      // Cập nhật tiêu đề chat từ tin nhắn đầu tiên
      if (sender === 'user' && chat.title === "Hội thoại mới") {
        chat.title = text.slice(0, 30) + (text.length > 30 ? "..." : "");
      }
      
      saveChats();
      renderSidebar();
    }
  }

  // Gửi tin nhắn
  async function sendMessage() {
    const messageText = userInput.value.trim();
    if (messageText === '') return;

    if (!currentChatId) createNewChat();
    
    addMessage(messageText, 'user');
    userInput.value = '';
    userInput.style.height = 'auto';
    sendButton.disabled = true;
    userInput.disabled = true;

    // Hiển thị typing indicator (fixed width to prevent bubble resize)
    const typingDiv = document.createElement('div');
    typingDiv.classList.add('message', 'bot', 'typing-indicator');
    typingDiv.innerHTML = `
      <div style="display: flex; align-items: center; gap: 6px;">
        <div class="typing-dots" style="transform: scale(0.7);">
          <span></span><span></span><span></span>
        </div>
        <span style="font-style: italic; opacity: 0.6; font-size: 12px; white-space: nowrap;">Đang suy luận...</span>
      </div>
    `;
    chatDisplay.appendChild(typingDiv);
    chatDisplay.scrollTop = chatDisplay.scrollHeight;

    try {
      // Gọi API backend
      // Auto-detect: Nếu chạy qua Nginx (Docker) dùng /api/, ngược lại dùng :8000
     // 🌍 Auto-detect environment and set API base URL
      const API_BASE = (() => {
  // Production: Cloudflare Pages → Hugging Face backend
        if (window.location.hostname.includes('pages.dev') || 
            window.location.hostname.includes('cloudflare')) {
          return 'https://eddiethewall-legal-qa-backend.hf.space';  // 👈 Your HF backend URL
        }
        // Local development
        else if (window.location.hostname === 'localhost' || 
                 window.location.hostname === '127.0.0.1') {
          return 'http://localhost:7860';  // Updated to HF port
        }
        // Docker/Nginx
        else if (window.location.port === '80' || window.location.port === '') {
          return '/api';
        }
        // Fallback
        else {
          return 'http://localhost:7860';
        }
      })();

    console.log('🔗 Using API Backend:', API_BASE);  // Debug log
      
      const response = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: messageText,
          use_advanced: true,
          model_mode: modelMode  // Send selected mode: 'fast' or 'quality'
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      typingDiv.remove();
      
      // Hiển thị câu trả lời
      addMessage(data.answer, 'bot');
      
      // Hiển thị performance timing (nếu có)
      if (data.timing) {
        const timingText = `⚡ Performance: ${data.timing.total_ms}ms (Search: ${data.timing.search_ms}ms + Generation: ${data.timing.generation_ms}ms)`;
        
        const timingDiv = document.createElement('div');
        timingDiv.classList.add('message', 'bot');
        timingDiv.style.fontSize = '0.75em';
        timingDiv.style.opacity = '0.5';
        timingDiv.style.fontStyle = 'italic';
        timingDiv.style.padding = '4px 12px';
        timingDiv.textContent = timingText;
        chatDisplay.appendChild(timingDiv);
      }
      
      // Hiển thị nguồn tham khảo và nút xem PDF
      if (data.sources && data.sources.length > 0) {
        const sourcesText = `\n\n📚 Nguồn tham khảo:\n${data.sources.slice(0, 3).map((s, i) => 
          `${i + 1}. ${s.source}`
        ).join('\n')}`;
        
        const sourcesDiv = document.createElement('div');
        sourcesDiv.classList.add('message', 'bot', 'sources');
        sourcesDiv.style.fontSize = '0.85em';
        sourcesDiv.style.opacity = '0.8';
        sourcesDiv.style.whiteSpace = 'pre-wrap';
        sourcesDiv.textContent = sourcesText;
        chatDisplay.appendChild(sourcesDiv);
        
        // Display PDF buttons with highlighting
        if (data.pdf_sources && data.pdf_sources.length > 0) {
          const pdfButtonsDiv = document.createElement('div');
          pdfButtonsDiv.style.marginTop = '12px';
          pdfButtonsDiv.style.display = 'flex';
          pdfButtonsDiv.style.flexWrap = 'wrap';
          pdfButtonsDiv.style.gap = '8px';
          
          // Group by PDF file with deduplication
          const pdfGroups = {};
          data.pdf_sources.forEach(source => {
            if (!pdfGroups[source.pdf_file]) {
              pdfGroups[source.pdf_file] = {
                highlights: new Set(),  // Use Set to avoid duplicates
                articles: new Set()
              };
            }
            
            // Add highlight text (deduplicated)
            if (source.highlight_text && source.highlight_text.trim()) {
              pdfGroups[source.pdf_file].highlights.add(source.highlight_text);
            }
            
            // Add article number (deduplicated)
            if (source.article_num && source.article_num.trim()) {
              pdfGroups[source.pdf_file].articles.add(source.article_num);
            }
          });
          
          // Create button for each PDF
          Object.entries(pdfGroups).forEach(([pdfFile, data]) => {
            const btn = document.createElement('button');
            btn.classList.add('view-pdf-btn');
            btn.textContent = `📄 Xem ${pdfFile}`;
            
            btn.onclick = () => {
              if (window.PDFViewer) {
                // Convert Sets to Arrays
                const highlightTexts = Array.from(data.highlights);
                const articleNumbers = Array.from(data.articles);
                
                console.log('📖 [PDF Button] Opening:', pdfFile);
                console.log('🔍 [PDF Button] Highlights:', highlightTexts);
                console.log('📋 [PDF Button] Articles:', articleNumbers);
                
                // Pass both to PDF viewer
                window.PDFViewer.open(pdfFile, highlightTexts, articleNumbers);
              }
            };
            
            pdfButtonsDiv.appendChild(btn);
          });
          
          chatDisplay.appendChild(pdfButtonsDiv);
        }
      }
      
    } catch (error) {
  typingDiv.remove();
  
  let errorMessage = '⚠️ Xin lỗi, đã có lỗi xảy ra. ';
  
  if (error.message.includes('Failed to fetch')) {
  errorMessage += `Không thể kết nối đến server. Vui lòng đảm bảo backend đang chạy tại ${API_BASE}`;
  } else {
    errorMessage += 'Vui lòng thử lại sau. Chi tiết: ' + error.message;
  }
      
      addMessage(errorMessage, 'bot');
      console.error('Error calling API:', error);
    } finally {
      sendButton.disabled = false;
      userInput.disabled = false;
      userInput.focus();
      chatDisplay.scrollTop = chatDisplay.scrollHeight;
    }
  }

  // Event listeners
  sendButton.addEventListener('click', sendMessage);
  
  userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  newChatBtn.addEventListener('click', createNewChat);

  // Model mode selector
  modeFast.addEventListener('change', () => {
    if (modeFast.checked) {
      modelMode = 'fast';
      console.log('✅ Switched to FAST mode (all Flash Lite)');
    }
  });

  modeQuality.addEventListener('change', () => {
    if (modeQuality.checked) {
      modelMode = 'quality';
      console.log('✅ Switched to QUALITY mode (Flash Lite for intent, Flash for answer)');
    }
  });

  // Theme toggle
  themeToggle.addEventListener('click', () => {
    isDark = !isDark;
    document.body.classList.toggle('dark');
    themeToggle.textContent = isDark ? '☀️' : '🌙';
    
    // Nếu dùng localStorage, uncomment dòng dưới:
    // localStorage.setItem('theme', isDark ? 'dark' : 'light');
  });

  // Khôi phục theme
  if (isDark) {
    document.body.classList.add('dark');
    themeToggle.textContent = '☀️';
  }

  // Khởi tạo
  if (chats.length === 0) {
    createNewChat();
  } else {
    currentChatId = chats[chats.length - 1].id;
    renderChat(chats[chats.length - 1]);
    renderSidebar();
  }
});
