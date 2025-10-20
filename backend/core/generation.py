"""
Answer Generation Module - LLM-based answer generation
"""

from typing import List, Dict


def generate_answer(question: str, context: List[Dict], gemini_model, chat_history: List[Dict] = None) -> str:
    """
    Generate answer using Full Gemini model (complex reasoning required)
    
    Args:
        question: User question
        context: List of relevant document chunks
        gemini_model: Gemini model instance
        chat_history: Optional chat history for context (only for quality mode)
    
    Returns:
        Generated answer
    """
    context_text = '\n\n'.join([
        f"[{i+1}] {chunk['source']}\n{chunk['content']}"
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

    prompt = f'''Bạn là chuyên gia pháp lý Việt Nam. Hãy trả lời câu hỏi một cách ĐẦY ĐỦ, CHÍNH XÁC dựa trên văn bản pháp luật được cung cấp.

{f"""LỊCH SỬ HỘI THOẠI:
{history_text}

(Sử dụng lịch sử để hiểu ngữ cảnh, nhưng trả lời dựa trên nguồn tham khảo bên dưới)

""" if history_text else ""}NGUỒN THAM KHẢO:
{context_text}

CÂU HỎI: {question}

YÊU CẦU TRÌNH BÀY:
1. **Trả lời đầy đủ, rõ ràng:**
   - Giải thích chi tiết các quy định liên quan
   - Nêu đầy đủ điều kiện, thủ tục (nếu có)
   - Phân tích các trường hợp cụ thể

2. **Trích dẫn chính xác:**
   - Sử dụng định dạng: (Điều X, Khoản Y, Điểm Z)
   - Đặt trích dẫn trong ngoặc kép "..." khi cần
   - VD: Theo quy định tại (Điều 8, Khoản 1), "Nam từ đủ 20 tuổi trở lên, nữ từ đủ 18 tuổi trở lên"

3. **Cấu trúc rõ ràng:**
   - Xuống dòng giữa các ý chính
   - Sử dụng gạch đầu dòng (-) hoặc đánh số (1., 2., 3.)
   - Phân đoạn hợp lý

4. **Nội dung:**
   - Giải thích các khái niệm pháp lý
   - Nêu rõ hậu quả pháp lý (nếu có)
   - Đưa ra lời khuyên thực tế (nếu phù hợp)

VÍ DỤ TRẢ LỜI TỐT:
"Về độ tuổi kết hôn, theo quy định tại (Điều 8, Khoản 1) của Luật Hôn nhân và Gia đình năm 2014:

**Điều kiện về độ tuổi:**
- Nam phải từ đủ 20 tuổi trở lên
- Nữ phải từ đủ 18 tuổi trở lên

**Trường hợp vi phạm:**
Việc kết hôn khi một bên hoặc cả hai bên chưa đủ tuổi được gọi là "tảo hôn", đây là hành vi bị nghiêm cấm theo (Điều 3, Khoản 8).

**Hậu quả pháp lý:**
Nếu vi phạm quy định về độ tuổi kết hôn, việc kết hôn có thể bị tòa án tuyên bố hủy theo (Điều 11)."

TRẢ LỜI:'''
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
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
