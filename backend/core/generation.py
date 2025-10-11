"""
Answer Generation Module - LLM-based answer generation
"""

from typing import List, Dict


def generate_answer(question: str, context: List[Dict], gemini_model) -> str:
    """
    Generate answer using Full Gemini model (complex reasoning required)
    
    Args:
        question: User question
        context: List of relevant document chunks
        gemini_model: Gemini model instance
    
    Returns:
        Generated answer
    """
    context_text = '\n\n'.join([
        f"[{i+1}] {chunk['source']}\n{chunk['content']}"
        for i, chunk in enumerate(context)
    ])

    prompt = f'''Bạn là chuyên gia pháp lý Việt Nam. Hãy trả lời câu hỏi dựa trên các văn bản pháp luật được cung cấp dưới đây.

NGUỒN THAM KHẢO:
{context_text}

CÂU HỎI: {question}

YÊU CẦU TRÌNH BÀY:
- Trả lời chính xác, cụ thể, dễ hiểu
- Kết hợp tất cả văn bản liên quan
- Nêu rõ số Điều, Khoản, Điểm
- Nếu có thay đổi, ghi rõ nguồn sửa đổi
- QUAN TRỌNG: Xuống dòng rõ ràng giữa các ý, sử dụng dấu gạch đầu dòng (-) hoặc đánh số (1., 2., 3.) khi liệt kê

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
