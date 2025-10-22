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

  // ===== SỬ DỤNG localStorage để lưu vĩnh viễn =====
  let chats = JSON.parse(localStorage.getItem('chats')) || [];
  let currentChatId = localStorage.getItem('currentChatId');
  let isDark = localStorage.getItem('theme') === 'dark';
  let modelMode = localStorage.getItem('modelMode') || 'quality';
  function trimSourceText(sourceText) {
    //Intelligently extract law name and document number from source text
    const pattern1 = /^(Luật[^,]+?)\s+(số\s+\d+\/\d+\/[A-Z0-9]+)/i;
    const match1 = sourceText.match(pattern1);
    if (match1) {
      return `${match1[1]} ${match1[2]}`;
    }

    const pattern2 = /^(Nghị định[^,]+?)\s+(số\s+\d+\/\d+\/[A-Z0-9]+)/i;
    const match2 = sourceText.match(pattern2);
    if (match2) {
      return `${match2[1]} ${match2[2]}`;
    }
    const pattern3 = /^([^,]+?)\s+(số\s+\d+\/\d+\/[A-Z\-0-9]+)/i;
    const match3 = sourceText.match(pattern3);
    if (match3) {
      let lawName = match3[1];
      const words = lawName.split(/\s+/);

      const halfLength = Math.floor(words.length/2);
      const firstHalf = words.slice(0, halfLength).join(' ');
      const secondHalf = words.slice(halfLength).join(' ');
      if (firstHalf === secondHalf) {
        lawName = firstHalf;
      }
      return `${lawName} ${match3[2]}`;
    }
    return sourceText.substring(0, 100);

  }
  // Tự động điều chỉnh chiều cao textarea
  function autoResizeTextarea() {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 200) + 'px';
  }

  userInput.addEventListener('input', autoResizeTextarea);

  // Tạo hội thoại mới
  function createNewChat(mode = null) {
    const chatMode = mode || modelMode;  // Sử dụng mode hiện tại nếu không truyền vào
    const newChat = {
      id: Date.now(),
      title: "Hội thoại mới",
      messages: [],
      mode: chatMode  // ✅ Lưu mode của chat
    };
    chats.push(newChat);
    currentChatId = newChat.id;
    saveChats();
    renderSidebar();
    renderChat(newChat);
    
    console.log(`✅ Created new chat with mode: ${chatMode}`);
  }

  // Lưu chats
  function saveChats() {
    localStorage.setItem('chats', JSON.stringify(chats));
    localStorage.setItem('currentChatId', currentChatId);
  }

  // Xóa chat
  function deleteChat(chatId) {
    const chatIndex = chats.findIndex(c => c.id === chatId);
    if (chatIndex === -1) return;
    
    chats.splice(chatIndex, 1);
    
    // Nếu xóa chat đang active, chuyển sang chat khác hoặc tạo mới
    if (currentChatId === chatId) {
      if (chats.length > 0) {
        currentChatId = chats[chats.length - 1].id;
        const currentChat = chats.find(c => c.id === currentChatId);
        renderChat(currentChat);
      } else {
        createNewChat();
      }
    }
    
    saveChats();
    renderSidebar();
    console.log(`🗑️ Deleted chat ${chatId}`);
  }

  // Render sidebar
  function renderSidebar() {
    chatList.innerHTML = '';
    chats.slice().reverse().forEach(chat => {
      const li = document.createElement('li');
      
      // ✅ Hiển thị mode badge
      const modeBadge = chat.mode === 'fast' ? '⚡' : '🎯';
      
      // Chat title span
      const titleSpan = document.createElement('span');
      titleSpan.textContent = `${modeBadge} ${chat.title}`;
      titleSpan.style.flex = '1';
      titleSpan.style.cursor = 'pointer';
      
      // Delete button
      const deleteBtn = document.createElement('button');
      deleteBtn.textContent = '×';
      deleteBtn.className = 'delete-chat-btn';
      deleteBtn.title = 'Xóa cuộc trò chuyện';
      deleteBtn.onclick = (e) => {
        e.stopPropagation();
        if (confirm('Bạn có chắc muốn xóa cuộc trò chuyện này?')) {
          deleteChat(chat.id);
        }
      };
      
      li.classList.toggle('active', chat.id === currentChatId);
      li.style.display = 'flex';
      li.style.alignItems = 'center';
      li.style.justifyContent = 'space-between';
      
      titleSpan.onclick = () => {
        currentChatId = chat.id;
        
        // ✅ Khi chọn chat, chuyển mode theo chat đó
        const chatMode = chat.mode || 'quality';
        if (modelMode !== chatMode) {
          modelMode = chatMode;
          localStorage.setItem('modelMode', modelMode);
          
          // Update radio buttons
          if (modelMode === 'fast') {
            modeFast.checked = true;
          } else {
            modeQuality.checked = true;
          }
          
          console.log(`🔄 Switched to ${modelMode} mode (from chat)`);
        }
        
        renderChat(chat);
        renderSidebar();
      };
      
      li.appendChild(titleSpan);
      li.appendChild(deleteBtn);
      chatList.appendChild(li);
    });
  }

  // Render một chat
  function renderChat(chat) {
    chatDisplay.innerHTML = '';
    chatTitle.textContent = chat.title;
    chat.messages.forEach((msg, index) => {
      // ✅ Truyền đầy đủ metadata + index khi render lại
      addMessage(msg.text, msg.sender, false, false, msg.metadata, index);
    });
    chatDisplay.scrollTop = chatDisplay.scrollHeight;
  }

  // Thêm tin nhắn
  function addMessage(text, sender, save = true, animated = true, metadata = null, messageIndex = -1) {
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
      // ✅ Lưu cả metadata (sources, pdf_sources, timing...)
      chat.messages.push({ text, sender, metadata });
      
      // Cập nhật tiêu đề chat từ tin nhắn đầu tiên
      if (sender === 'user' && chat.title === "Hội thoại mới") {
        chat.title = text.slice(0, 30) + (text.length > 30 ? "..." : "");
      }
      
      saveChats();
      renderSidebar();
    }
  }

  // Thêm nút Like/Dislike
  function addFeedbackButtons(query, answer, sources) {
    const feedbackDiv = document.createElement('div');
    feedbackDiv.classList.add('feedback-buttons');

    const likeBtn = document.createElement('button');
    likeBtn.classList.add('feedback-btn', 'like-btn');
    likeBtn.innerHTML = '👍';
    likeBtn.title = 'Câu trả lời hữu ích';
    
    const dislikeBtn = document.createElement('button');
    dislikeBtn.classList.add('feedback-btn', 'dislike-btn');
    dislikeBtn.innerHTML = '👎';
    dislikeBtn.title = 'Câu trả lời chưa chính xác';

    const feedbackText = document.createElement('span');
    feedbackText.classList.add('feedback-text');

    likeBtn.onclick = async (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      await submitFeedback(query, answer, sources, 'like');
      
      // Chỉ cập nhật style của nút, không thêm/xóa element
      likeBtn.style.background = '#4caf50';
      likeBtn.style.color = 'white';
      likeBtn.disabled = true;
      dislikeBtn.disabled = true;
      dislikeBtn.style.opacity = '0.3';
      feedbackText.textContent = 'Cảm ơn phản hồi!';
    };

    dislikeBtn.onclick = async (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      await submitFeedback(query, answer, sources, 'dislike');
      
      // Chỉ cập nhật style của nút, không thêm/xóa element
      dislikeBtn.style.background = '#f44336';
      dislikeBtn.style.color = 'white';
      dislikeBtn.disabled = true;
      likeBtn.disabled = true;
      likeBtn.style.opacity = '0.3';
      feedbackText.textContent = 'Chúng tôi sẽ cải thiện!';
    };

    feedbackDiv.appendChild(likeBtn);
    feedbackDiv.appendChild(dislikeBtn);
    feedbackDiv.appendChild(feedbackText);
    chatDisplay.appendChild(feedbackDiv);
  }

  // Gửi feedback tới server
  async function submitFeedback(query, answer, sources, status) {
    const API_BASE = (() => {
      if (window.location.hostname.includes('pages.dev') || 
          window.location.hostname.includes('cloudflare')) {
        return 'https://eddiethewall-legal-qa-backend.hf.space';
      }
      else if (window.location.hostname === 'localhost' || 
               window.location.hostname === '127.0.0.1') {
        return 'http://localhost:7860';
      }
      else if (window.location.port === '80' || window.location.port === '') {
        return '/api';
      }
      else {
        return 'http://localhost:7860';
      }
    })();

    try {
      const response = await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          answer: answer,
          context: sources,
          status: status
        })
      });

      const data = await response.json();
      console.log('✓ Feedback sent:', status, data);
    } catch (error) {
      console.error('✗ Feedback error:', error);
    }
  }

  // Gửi tin nhắn
  async function sendMessage() {
    const messageText = userInput.value.trim();
    if (messageText === '') return;

    // ✅ Kiểm tra xem có cần tạo chat mới không
    if (!currentChatId) {
      createNewChat(modelMode);
    } else {
      // ✅ Kiểm tra mode của chat hiện tại
      const currentChat = chats.find(c => c.id === currentChatId);
      if (currentChat) {
        const chatMode = currentChat.mode || 'quality';
        
        // Nếu mode khác với chat hiện tại → Tạo chat mới
        if (chatMode !== modelMode) {
          console.log(`🔄 Mode changed: ${chatMode} → ${modelMode}. Creating new chat...`);
          createNewChat(modelMode);
        }
      }
    }
    
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
      
      // ✅ Lưu metadata để có thể restore lại sau khi reload
      const metadata = {
        query: messageText,
        sources: data.sources || [],
        pdf_sources: data.pdf_sources || [],
        timing: data.timing || null
      };
      
      // Hiển thị câu trả lời với metadata
      addMessage(data.answer, 'bot', true, true, metadata);
      
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
      // Hiển thị nguồn tham khảo với clickable citations
      if (data.sources && data.sources.length > 0) {
        // Create sources container
        const sourcesContainer = document.createElement('div');
        sourcesContainer.classList.add('message', 'bot', 'sources');
        sourcesContainer.style.fontSize = '0.85em';
        sourcesContainer.style.opacity = '0.9';
        
        // Add "Nguồn tham khảo" header
        const sourcesHeader = document.createElement('div');
        sourcesHeader.style.fontWeight = '600';
        sourcesHeader.style.marginBottom = '12px';
        sourcesHeader.style.fontSize = '1em';
        sourcesHeader.textContent = '📚 Nguồn tham khảo:';
        sourcesContainer.appendChild(sourcesHeader);
        
        // Create a map of PDF sources by index
        const pdfSourcesByIndex = {};
        if (data.pdf_sources && data.pdf_sources.length > 0) {
          data.pdf_sources.forEach((pdfSource, idx) => {
            pdfSourcesByIndex[idx] = pdfSource;
          });
        }
        
        // Add clickable source citations with trimmed text
        data.sources.slice(0, 3).forEach((s, i) => {
          const pdfSource = pdfSourcesByIndex[i];
          
          // Create card-style container for each source
          const sourceCard = document.createElement('div');
          sourceCard.style.marginBottom = '10px';
          sourceCard.style.padding = '12px';
          sourceCard.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%)';
          sourceCard.style.borderLeft = '3px solid #667eea';
          sourceCard.style.borderRadius = '6px';
          sourceCard.style.transition = 'all 0.2s ease';
          sourceCard.style.cursor = pdfSource ? 'pointer' : 'default';
          
          // Header: Source title with article number
          const sourceHeader = document.createElement('div');
          sourceHeader.style.display = 'flex';
          sourceHeader.style.alignItems = 'center';
          sourceHeader.style.gap = '8px';
          
          const numberBadge = document.createElement('span');
          numberBadge.style.display = 'inline-flex';
          numberBadge.style.alignItems = 'center';
          numberBadge.style.justifyContent = 'center';
          numberBadge.style.minWidth = '24px';
          numberBadge.style.height = '24px';
          numberBadge.style.padding = '0 6px';
          numberBadge.style.background = '#667eea';
          numberBadge.style.color = 'white';
          numberBadge.style.borderRadius = '12px';
          numberBadge.style.fontSize = '0.9em';
          numberBadge.style.fontWeight = '600';
          numberBadge.textContent = i + 1;
          
          const sourceTitle = document.createElement('div');
          sourceTitle.style.flex = '1';
          sourceTitle.style.fontSize = '0.95em';
          sourceTitle.style.fontWeight = '500';
          sourceTitle.style.color = pdfSource ? '#667eea' : 'inherit';
          sourceTitle.style.lineHeight = '1.4';
          
          // Smart trim the source text
          const trimmedSource = trimSourceText(s.source);

          if (pdfSource && pdfSource.article_num) {
            // Parse article_num which contains "Dieu 3, Khoan 5" format
            let articleRef = pdfSource.article_num.trim();
            
            // Replace Vietnamese characters
            articleRef = articleRef
              .replace(/Dieu/gi, 'Điều')
              .replace(/Khoan/gi, 'Khoản');
            
            // Handle cases where article_num might be just a number like "3"
            if (/^\d+$/.test(articleRef)) {
              articleRef = `Điều ${articleRef}`;
            }
            
            // Clean up spacing around commas
            articleRef = articleRef.replace(/\s*,\s*/g, ', ');
            
            // Debug: Log what we received
            console.log(`[Source ${i+1}] article_num:`, pdfSource.article_num, '→', articleRef);
            
            sourceTitle.innerHTML = `${trimmedSource} <span style="color: #d84315; font-weight: 600; margin-left: 6px;">[${articleRef}]</span>`;
          } else {
            sourceTitle.textContent = trimmedSource;
          }
          
          sourceHeader.appendChild(numberBadge);
          sourceHeader.appendChild(sourceTitle);
          
          // Add PDF icon if clickable
          if (pdfSource && pdfSource.pdf_file) {
            const pdfIcon = document.createElement('span');
            pdfIcon.style.fontSize = '1.2em';
            pdfIcon.textContent = '📄';
            pdfIcon.style.opacity = '0.7';
            sourceHeader.appendChild(pdfIcon);
          }
          
          sourceCard.appendChild(sourceHeader);
          
          // Click handler (if PDF available)
          if (pdfSource && pdfSource.pdf_file && pdfSource.article_num) {
            sourceCard.onclick = () => {
              if (window.PDFViewer) {
                console.log(`📖 [Source Card Click] Opening ${pdfSource.pdf_file} at ${pdfSource.article_num}`);
                window.PDFViewer.open(
                  pdfSource.pdf_file,
                  [pdfSource.highlight_text || ''],
                  [pdfSource.article_num]
                );
              }
            };
            
            // Hover effects
            sourceCard.onmouseenter = () => {
              sourceCard.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%)';
              sourceCard.style.borderLeftColor = '#764ba2';
              sourceCard.style.transform = 'translateX(4px)';
              sourceCard.style.boxShadow = '0 2px 8px rgba(102, 126, 234, 0.2)';
            };
            
            sourceCard.onmouseleave = () => {
              sourceCard.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%)';
              sourceCard.style.borderLeftColor = '#667eea';
              sourceCard.style.transform = 'translateX(0)';
              sourceCard.style.boxShadow = 'none';
            };
          }
          
          sourcesContainer.appendChild(sourceCard);
        });
        
        // Optional: Add summary footer for multiple PDFs
        if (data.pdf_sources && data.pdf_sources.length > 0) {
          const pdfGroups = {};
          data.pdf_sources.forEach(source => {
            if (!pdfGroups[source.pdf_file]) {
              pdfGroups[source.pdf_file] = new Set();
            }
            if (source.article_num) {
              pdfGroups[source.pdf_file].add(source.article_num);
            }
          });
          
          if (Object.keys(pdfGroups).length > 0) {
            const footerDiv = document.createElement('div');
            footerDiv.style.marginTop = '12px';
            footerDiv.style.paddingTop = '12px';
            footerDiv.style.borderTop = '1px solid rgba(128, 128, 128, 0.2)';
            footerDiv.style.fontSize = '0.85em';
            footerDiv.style.opacity = '0.7';
            footerDiv.style.fontStyle = 'italic';
            
            const pdfNames = Object.keys(pdfGroups);
            const totalArticles = Object.values(pdfGroups).reduce((sum, set) => sum + set.size, 0);
            
            footerDiv.textContent = `💡 Click vào các thẻ để xem ${totalArticles} điều từ ${pdfNames.length} văn bản`;
            
            sourcesContainer.appendChild(footerDiv);
          }
        }
        
        chatDisplay.appendChild(sourcesContainer);
        
        // Thêm nút Like/Dislike ở cuối cùng
        addFeedbackButtons(messageText, data.answer, data.sources || []);
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

  // Clear all chats button
  const clearAllChatsBtn = document.getElementById('clear-all-chats');
  clearAllChatsBtn.addEventListener('click', () => {
    if (confirm('⚠️ Bạn có chắc chắn muốn xóa HẾT TẤT CẢ cuộc hội thoại?\n\nHành động này KHÔNG THỂ HOÀN TÁC!')) {
      // Xóa hết data từ localStorage
      localStorage.removeItem('chats');
      localStorage.removeItem('currentChatId');
      
      // Reset biến trong memory
      chats = [];
      currentChatId = null;
      
      // Tạo chat mới
      createNewChat();
      
      console.log('🗑️ All chats deleted successfully');
    }
  });

  // Model mode selector
  modeFast.addEventListener('change', () => {
    if (modeFast.checked) {
      const oldMode = modelMode;
      modelMode = 'fast';
      localStorage.setItem('modelMode', 'fast');
      console.log('✅ Switched to FAST mode (all Flash Lite)');
      
      // ✅ Nếu có chat hiện tại và mode khác → Thông báo sẽ tạo chat mới
      if (currentChatId && oldMode !== 'fast') {
        const currentChat = chats.find(c => c.id === currentChatId);
        if (currentChat && currentChat.mode !== 'fast') {
          console.log('💡 Next message will create a new FAST chat');
        }
      }
    }
  });

  modeQuality.addEventListener('change', () => {
    if (modeQuality.checked) {
      const oldMode = modelMode;
      modelMode = 'quality';
      localStorage.setItem('modelMode', 'quality');
      console.log('✅ Switched to QUALITY mode (Flash Lite for intent, Flash for answer)');
      
      // ✅ Nếu có chat hiện tại và mode khác → Thông báo sẽ tạo chat mới
      if (currentChatId && oldMode !== 'quality') {
        const currentChat = chats.find(c => c.id === currentChatId);
        if (currentChat && currentChat.mode !== 'quality') {
          console.log('💡 Next message will create a new QUALITY chat');
        }
      }
    }
  });

  // Theme toggle
  themeToggle.addEventListener('click', () => {
    isDark = !isDark;
    document.body.classList.toggle('dark');
    themeToggle.textContent = isDark ? '☀️' : '🌙';
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  });

  // Khôi phục theme và model mode
  if (isDark) {
    document.body.classList.add('dark');
    themeToggle.textContent = '☀️';
  }
  
  // Khôi phục model mode selection
  if (modelMode === 'fast') {
    modeFast.checked = true;
  } else {
    modeQuality.checked = true;
  }

  // Khởi tạo
  if (chats.length === 0) {
    createNewChat();
  } else {
    // Khôi phục chat cuối cùng hoặc chat đã chọn
    const lastChat = chats.find(c => c.id == currentChatId) || chats[chats.length - 1];
    currentChatId = lastChat.id;
    renderChat(lastChat);
    renderSidebar();
  }
});
