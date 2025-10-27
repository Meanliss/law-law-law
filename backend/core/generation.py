"""
Answer Generation Module - LLM-based answer generation
"""

from typing import List, Dict


def generate_answer(question: str, context: List[Dict], gemini_model, chat_history: List[Dict] = None, use_advanced: bool = False) -> str:
    """
    Generate answer using Gemini model with mode-specific prompts
    
    Args:
        question: User question
        context: List of relevant document chunks
        gemini_model: Gemini model instance (Flash for Quality, Lite for Fast)
        chat_history: Optional chat history for context (only for quality mode)
        use_advanced: True = Quality mode (reasoning prompt), False = Fast mode (concise prompt)
    
    Returns:
        Generated answer
    """
    context_text = '\n\n'.join([
        f"[{i+1}] {chunk.get('json_file', chunk.get('source', 'Unknown'))}\n{chunk['content']}"
        for i, chunk in enumerate(context)
    ])

    # ✅ Format chat history nếu có (chỉ lấy 2-3 cặp hỏi-đáp gần nhất)
    history_text = ""
    if chat_history and len(chat_history) > 0:
        recent_history = chat_history[-6:]  # Lấy tối đa 6 message (3 cặp hỏi-đáp)
        history_lines = []
        for msg in recent_history:
            role = "👤 Người dùng" if msg.get('role') == 'user' else "🤖 Trợ lý"
            content = msg.get('content', '')[:200]  # Giới hạn 200 ký tự mỗi message
            history_lines.append(f"{role}: {content}")
        history_text = '\n'.join(history_lines)

    # ✅ CHỌN PROMPT THEO MODE
    if use_advanced:
        # ========== QUALITY MODE: Reasoning prompt với phân tích sâu ==========
        prompt = f'''Bạn là chuyên gia pháp lý Việt Nam với khả năng PHÂN TÍCH và SUY LUẬN CAO nhưng không tự xưng mình là chuyên gia pháp lý mà luôn nhắc người dùng bạn chỉ là AI hãy tìm luật sư để cho câu trả lời chính xác hơn.

{f"""LỊCH SỬ HỘI THOẠI:
{history_text}

(Sử dụng lịch sử để hiểu ngữ cảnh, nhưng trả lời dựa trên nguồn tham khảo bên dưới)

""" if history_text else ""}NGUỒN THAM KHẢO:
{context_text}

CÂU HỎI: {question}

YÊU CẦU TRẢ LỜI:

**BƯỚC 1 - PHÂN TÍCH CÂU HỎI:**
- Xác định các yếu tố pháp lý cần giải quyết
- Nhận diện các điều kiện, trường hợp đặc biệt

**BƯỚC 2 - XÂY DỰNG LOGIC SUY LUẬN:**
- Liệt kê các quy định pháp luật liên quan
- Phân tích mối quan hệ giữa các quy định
- Áp dụng quy định vào tình huống cụ thể

**BƯỚC 3 - KẾT LUẬN:**
- Đưa ra câu trả lời rõ ràng, đầy đủ
- Trích dẫn chính xác (Điều X, Khoản Y, Điểm Z)
- Giải thích hậu quả pháp lý (nếu có)

**CẤU TRÚC TRẢ LỜI:**
1. **Tóm tắt câu trả lời** (2-3 câu ngắn gọn)
2. **Phân tích chi tiết:**
   - Quy định pháp luật liên quan với trích dẫn chính xác
   - Điều kiện, thủ tục (nếu có)
   - Các trường hợp đặc biệt, ngoại lệ
3. **Hậu quả pháp lý** (nếu vi phạm)
4. **Lưu ý thực tế** (nếu cần)

**ĐỊNH DẠNG TRÍCH DẪN:**
- Quy định: (Điều X, Khoản Y, Điểm Z)
- Trích dẫn văn bản: "nội dung chính xác"
- VD: Theo (Điều 8, Khoản 1), "Nam từ đủ 20 tuổi trở lên"

VÍ DỤ TRẢ LỜI TỐT:
"**Tóm tắt:** Nam phải từ đủ 20 tuổi, nữ từ đủ 18 tuổi mới được kết hôn theo pháp luật Việt Nam.

**Phân tích chi tiết:**

Theo quy định tại (Điều 8, Khoản 1, Điểm a) của Luật Hôn nhân và Gia đình năm 2014:
- Nam phải từ đủ 20 tuổi trở lên
- Nữ phải từ đủ 18 tuổi trở lên

Đây là một trong những điều kiện kết hôn bắt buộc, nằm trong nhóm "Điều kiện kết hôn" được quy định rõ ràng.

**Trường hợp vi phạm:**
Việc kết hôn khi chưa đủ tuổi được gọi là "tảo hôn" (Điều 3, Khoản 8), là hành vi bị nghiêm cấm theo pháp luật.

**Hậu quả pháp lý:**
- Hôn nhân có thể bị Tòa án tuyên bố HỦY theo (Điều 11, Khoản 1)
- Người vi phạm có thể bị xử phạt hành chính theo quy định

**Lưu ý:** Trong trường hợp đặc biệt, nếu tại thời điểm Tòa án giải quyết mà cả hai bên đã đủ điều kiện kết hôn và có con chung, hôn nhân có thể được công nhận hợp pháp (Điều 11, Khoản 2)."

TRẢ LỜI:'''
    else:
        # ========== FAST MODE: Concise prompt ==========
        prompt = f'''Bạn là chuyên gia pháp lý Việt Nam. Trả lời NGẮN GỌN, CHÍNH XÁC.

NGUỒN THAM KHẢO:
{context_text}

CÂU HỎI: {question}

YÊU CẦU:
- Trả lời TỐI ĐA 4-6 câu, súc tích
- Trích dẫn chính xác (Điều X, Khoản Y)
- Đi thẳng vào vấn đề, không dài dòng
- Không cần phân tích sâu

TRẢ LỜI:'''
    
    try:
        response = gemini_model.generate_content(prompt)
        answer = response.text.strip()
        
        # Log mode
        mode_name = "QUALITY (Reasoning)" if use_advanced else "FAST (Concise)"
        print(f'[GENERATION] Mode: {mode_name}, Length: {len(answer)} chars')
        
        return answer
    except Exception as e:
        print(f'[ERROR] Gemini API error: {e}')
        return 'Xin lỗi, không thể tạo câu trả lời lúc này.'


def get_rejection_message() -> str:
    """
    Get standard rejection message for non-legal queries
    
    Returns:
        Rejection message
    """
    return """Xin lỗi, câu hỏi của bạn dường như không liên quan đến pháp luật Việt Nam.

Tôi chỉ có thể trả lời các câu hỏi về:
- Luật pháp, quy định, nghị định, thông tư
- Quyền và nghĩa vụ theo pháp luật
- Thủ tục pháp lý (kết hôn, ly hôn, mua bán đất đai, lao động...)
- Xử phạt vi phạm hành chính
- Các quy định về thuế, phí, lệ phí

Ví dụ các câu hỏi hợp lệ:
• Quy định về độ tuổi kết hôn?
• Điều kiện mua bán đất đai?
• Quyền lợi người lao động khi bị sa thải?"""
