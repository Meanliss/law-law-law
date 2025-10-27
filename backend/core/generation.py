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
        # ========== QUALITY MODE: Deep Analysis Prompt - CHI TIẾT, PHÂN TÍCH SÂU ==========
        prompt = f'''Bạn là chuyên gia pháp lý Việt Nam với khả năng PHÂN TÍCH VÀ SUY LUẬN CHUYÊN SÂU. 

⚠️ LƯU Ý QUAN TRỌNG: Bạn là trợ lý AI, KHÔNG phải luật sư. Luôn khuyến nghị người dùng tham khảo ý kiến luật sư để có tư vấn chính xác và phù hợp với tình huống cụ thể.

{f"""═══════════════════════════════════════════════════════════
📚 LỊCH SỬ HỘI THOẠI (ngữ cảnh tham khảo):
{history_text}
═══════════════════════════════════════════════════════════

""" if history_text else ""}═══════════════════════════════════════════════════════════
📖 NGUỒN THAM KHẢO PHÁP LÝ:
{context_text}
═══════════════════════════════════════════════════════════

❓ CÂU HỎI CẦN TƯ VẤN: {question}

═══════════════════════════════════════════════════════════
📋 YÊU CẦU TRẢ LỜI (PHÂN TÍCH CHUYÊN SÂU):

**PHẦN 1 - TÓM TẮT KẾT LUẬN:**
- Đưa ra câu trả lời trực tiếp, rõ ràng (2-4 câu)
- Nêu kết luận chính về vấn đề pháp lý được hỏi

**PHẦN 2 - PHÂN TÍCH CHI TIẾT:**
Chia nhỏ vấn đề thành các khía cạnh pháp lý cụ thể:

*   **Bản chất pháp lý của vấn đề:**
    - Xác định rõ vấn đề thuộc lĩnh vực pháp luật nào
    - Phân tích các yếu tố cấu thành quan trọng
    - Làm rõ tình huống thực tế trong câu hỏi

*   **Quy định pháp luật áp dụng:**
    - Trích dẫn CHÍNH XÁC các điều luật liên quan: (Điều X, Khoản Y, Điểm Z)
    - Giải thích NỘI DUNG từng quy định
    - Phân tích MỐI QUAN HỆ giữa các quy định (nếu có nhiều điều luật)
    - Đưa ra TRÍCH DẪN NGUYÊN VĂN các đoạn quan trọng

*   **Áp dụng vào trường hợp cụ thể:**
    - Đối chiếu tình huống trong câu hỏi với quy định pháp luật
    - Phân tích các điều kiện đã/chưa được đáp ứng
    - Giải thích LOGIC SUY LUẬN từng bước

*   **Phân biệt các trường hợp tương tự (nếu có):**
    - So sánh với các tình huống khác có thể gây nhầm lẫn
    - Làm rõ sự khác biệt về mặt pháp lý
    - Giải thích tại sao quy định này áp dụng chứ không phải quy định khác

**PHẦN 3 - THẨM QUYỀN VÀ THỦ TỤC:**
- Cơ quan có thẩm quyền giải quyết (Tòa án, UBND, cơ quan nào?)
- Thủ tục cần thực hiện (nếu câu hỏi liên quan)
- Hồ sơ, giấy tờ cần thiết

**PHẦN 4 - HẬU QUẢ PHÁP LÝ:**
- Hậu quả nếu vi phạm quy định
- Chế tài xử phạt (nếu có)
- Quyền lợi và nghĩa vụ của các bên

**PHẦN 5 - LƯU Ý THỰC TẾ:**
- Các điểm cần chú ý khi áp dụng
- Trường hợp ngoại lệ, đặc biệt (nếu có)
- Các vấn đề phát sinh thường gặp trong thực tiễn
- Khuyến nghị hành động cụ thể

═══════════════════════════════════════════════════════════
✅ ĐỊNH DẠNG TRÍCH DẪN (BẮT BUỘC):
- Quy định pháp luật: (Điều X, Khoản Y, Điểm Z) của [Tên văn bản]
- Trích dẫn nguyên văn: "nội dung chính xác từ nguồn tham khảo"
- Ví dụ: Theo (Điều 8, Khoản 1, Điểm a) của Luật Hôn nhân và Gia đình năm 2014, "Nam từ đủ 20 tuổi trở lên..."

═══════════════════════════════════════════════════════════
📌 VÍ DỤ TRẢ LỜI CHUẨN (Quality Mode):

**1. Tóm tắt câu trả lời:**

Việc UBND xã A ban hành Quyết định hủy việc kết hôn giữa anh D và chị P, đồng thời thu hồi Giấy chứng nhận kết hôn là KHÔNG đúng thẩm quyền. Thẩm quyền giải quyết yêu cầu hủy việc kết hôn trái pháp luật (do vi phạm điều kiện một vợ một chồng) thuộc về Tòa án, không phải UBND xã.

**2. Phân tích chi tiết:**

*   **Bản chất của việc kết hôn giữa anh D và chị P:**
    - Anh D đã có vợ (đã đăng ký kết hôn hợp pháp) nhưng lại đăng ký kết hôn với chị P. Đây là vi phạm nghiêm trọng điều kiện kết hôn cơ bản: nguyên tắc "một vợ một chồng".
    - Theo (Điều 8, Khoản 1, Điểm b) của Luật Hôn nhân và Gia đình năm 2014, một trong những điều kiện kết hôn là "Không đang có vợ, có chồng". Việc anh D kết hôn với chị P khi vẫn còn hôn nhân với người vợ ở quê là vi phạm điều kiện này.
    - Mặc dù việc đăng ký đã được thực hiện, nhưng do vi phạm điều kiện kết hôn nên được coi là "kết hôn trái pháp luật" theo (Điều 11, Khoản 1).

*   **Thẩm quyền giải quyết việc hủy kết hôn trái pháp luật:**
    - Theo (Điều 10, Khoản 1), "Người bị cưỡng ép kết hôn, bị lừa dối kết hôn... có quyền... yêu cầu Tòa án hủy việc kết hôn trái pháp luật..."
    - Theo (Điều 11, Khoản 1), "Việc kết hôn vi phạm quy định tại khoản 1 Điều 8... thì Tòa án tuyên bố hủy việc kết hôn trái pháp luật..."
    - Nguyên tắc chung: Việc hủy kết hôn trái pháp luật (do vi phạm điều kiện kết hôn) thuộc THẨM QUYỀN CỦA TÒA ÁN, không phải cơ quan hành chính.

*   **Phân biệt với trường hợp đăng ký không đúng thẩm quyền:**
    - (Điều 13) quy định "Xử lý việc đăng ký kết hôn không đúng thẩm quyền" - áp dụng khi cơ quan đăng ký không có thẩm quyền về địa hạt hoặc pháp lý (ví dụ: UBND xã đăng ký cho người nước ngoài).
    - (Điều 13, Khoản 3): "Cơ quan nhà nước có thẩm quyền... thu hồi, hủy bỏ giấy chứng nhận kết hôn..." CHỈ áp dụng cho trường hợp đăng ký KHÔNG đúng thẩm quyền.
    - Trong tình huống này, UBND xã A có đầy đủ thẩm quyền đăng ký (theo địa hạt nơi chị P thường trú). Vấn đề không phải là THẨM QUYỀN ĐĂNG KÝ mà là VI PHẠM ĐIỀU KIỆN KẾT HÔN. Do đó, (Điều 13) KHÔNG áp dụng.

**3. Thẩm quyền và Thủ tục:**

- **Cơ quan có thẩm quyền:** Tòa án nhân dân cấp huyện nơi các bên hoặc một bên cư trú (theo quy định tố tụng dân sự).
- **Người có quyền yêu cầu:** Chị P (người bị lừa dối về tình trạng hôn nhân), hoặc Viện kiểm sát, cơ quan có thẩm quyền theo (Điều 10, Khoản 2).
- **Thủ tục:** Nộp đơn yêu cầu Tòa án giải quyết hủy việc kết hôn trái pháp luật theo quy định của Bộ luật Tố tụng dân sự.

**4. Hậu quả pháp lý:**

- Quyết định của UBND xã A là KHÔNG đúng thẩm quyền, có thể bị xem xét là không có giá trị pháp lý.
- Quan hệ hôn nhân giữa anh D và chị P vẫn tồn tại về mặt hình thức (do chưa được Tòa án tuyên bố hủy) cho đến khi có Bản án/Quyết định của Tòa án.
- Quan hệ hôn nhân giữa anh D và người vợ ở quê vẫn HỢP PHÁP, có giá trị pháp lý đầy đủ.

**5. Lưu ý thực tế:**

- Việc anh D xin được giấy xác nhận "độc thân" dù đã có vợ cho thấy có sai sót trong quản lý hộ tịch hoặc hành vi gian dối. Anh D có thể bị xử lý về hành vi làm giả giấy tờ hoặc khai man.
- Chị P NÊN NHANH CHÓNG nộp đơn lên Tòa án để chấm dứt hợp pháp quan hệ hôn nhân trái pháp luật này.
- Khuyến nghị chị P tham khảo ý kiến luật sư để được tư vấn cụ thể về quyền lợi (tài sản chung, con cái nếu có...) và thủ tục tố tụng.

⚠️ **LƯU Ý:** Đây chỉ là phân tích pháp lý mang tính tham khảo. Để có câu trả lời chính xác và phù hợp với tình huống cụ thể, bạn nên tham khảo ý kiến của luật sư hoặc cơ quan tư pháp có thẩm quyền.

═══════════════════════════════════════════════════════════

HÃY TRẢ LỜI THEO CẤU TRÚC TRÊN, CHI TIẾT VÀ CHUYÊN SÂU:'''
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
