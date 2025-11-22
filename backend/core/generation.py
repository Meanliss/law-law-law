"""
Answer Generation Module - LLM-based answer generation
"""

from typing import List, Dict
import json
from pathlib import Path


def generate_answer(question: str, context: List[Dict], gemini_model, chat_history: List[Dict] = None, use_advanced: bool = False) -> str:
    """
    Generate answer using Gemini model with mode-specific prompts
    
    Args:
        question: User question
        context: List of relevant document chunks
        gemini_model: Gemini model instance (always Flash)
        chat_history: Optional chat history for context
        use_advanced: True = Detail mode (reasoning prompt), False = Summary mode (concise prompt)
    
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
        # ========== DETAIL MODE: Deep Analysis Prompt - CHI TIẾT, PHÂN TÍCH SÂU, AGENT STYLE ==========
        prompt = f'''Bạn là chuyên gia pháp lý Việt Nam với khả năng PHÂN TÍCH VÀ SUY LUẬN CHUYÊN SÂU. 
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
📋 YÊU CẦU TRẢ LỜI (PHÂN TÍCH CHUYÊN SÂU + AGENT STYLE):

**PHẦN 1 - TÓM TẮT KẾT LUẬN:**

- Đưa ra câu trả lời trực tiếp, rõ ràng (2-4 câu)
- Nêu kết luận chính về vấn đề pháp lý được hỏi
- Xác định mức độ rủi ro (Cao/Trung bình/Thấp)

⚠️ **NẾU KHÔNG CHẮC CHẮN:** Nếu thông tin trong nguồn tham khảo không đủ để đưa ra câu trả lời chắc chắn, hãy bắt đầu bằng:
"⚠️ Tôi không hoàn toàn chắc chắn với câu trả lời này do [lý do: thiếu thông tin/nguồn không rõ ràng/vấn đề phức tạp], nhưng dựa trên nguồn hiện có, đây là câu trả lời bạn có thể tham khảo:"

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
- Thời hạn xử lý (nếu có quy định)

**PHẦN 4 - HẬU QUẢ PHÁP LÝ & RỦI RO:**
- Hậu quả nếu VI PHẠM quy định (chính xác + chi tiết):
  • Nếu bạn làm/không làm A thì sẽ phải chịu hậu quả gì?
  • Ai sẽ bị xử phạt, mức xử phạt bao nhiêu?
  • Ảnh hưởng gì đến quyền lợi pháp lý của các bên?
- Chế tài xử phạt (nếu có): hành chính, dân sự, hình sự
- Quyền lợi và nghĩa vụ của các bên
- Những rủi ro/hậu quả phụ (ảnh hưởng không trực tiếp đến quyền lợi)

**PHẦN 5 - LƯU Ý THỰC TẾ + KHUYẾN NGHỊ HÀNH ĐỘNG:**
- Các điểm cần chú ý khi áp dụng
- Trường hợp ngoại lệ, đặc biệt (nếu có)
- Các vấn đề phát sinh thường gặp trong thực tiễn
- Khuyến nghị hành động CỤ THỂ từng bước (Nên làm gì, không nên làm gì)
- Các tài liệu/hồ sơ nên chuẩn bị sẵn

═══════════════════════════════════════════════════════════
⚠️ QUY TẮC TRÌNH BÀY (BẮT BUỘC):
- Sử dụng **dấu gạch đầu dòng** (-) cho tất cả các danh sách.
- **Xuống dòng KÉP** (2 lần enter) giữa các đoạn văn và các mục để tạo khoảng trắng thoáng mắt.
- **In đậm** các từ khóa quan trọng.
- KHÔNG viết thành các khối văn bản dày đặc (wall of text).

═══════════════════════════════════════════════════════════
✅ ĐỊNH DẠNG TRÍCH DẪN (BẮT BUỘC PHẢI CHÍNH XÁC):
- Quy định pháp luật: (Điều X, Khoản Y, Điểm Z) của [Tên văn bản] năm [năm]
- Trích dẫn nguyên văn: "nội dung chính xác từ nguồn tham khảo"
- Ví dụ: Theo (Điều 8, Khoản 1, Điểm a) của Luật Hôn nhân và Gia đình năm 2014, "Nam từ đủ 20 tuổi trở lên..."

═══════════════════════════════════════════════════════════

HÃY TRẢ LỜI THEO CẤU TRÚC TRÊN, CHI TIẾT VÀ CHUYÊN SÂU:'''
    else:
        # ========== SUMMARY MODE: Concise prompt - NGẮN GỌN NHƯNG VẪN CHÍNH XÁC ==========
        prompt = f'''Bạn là chuyên gia pháp lý Việt Nam. Trả lời NGẮN GỌN, CHÍNH XÁC, TRỰC TIẾP.

{f"""═══════════════════════════════════════════════════════════
📚 NGỮ CẢNH HỘI THOẠI:
{history_text}

""" if history_text else ""}═══════════════════════════════════════════════════════════
📖 NGUỒN THAM KHẢO:
{context_text}

═══════════════════════════════════════════════════════════
❓ CÂU HỎI: {question}

═══════════════════════════════════════════════════════════
📋 YÊU CẦU (SUMMARY MODE - NGẮN GỌN):

**Cấu trúc trả lời:**

⚠️ **NẾU KHÔNG CHẮC CHẮN:** Bắt đầu bằng:
"⚠️ Tôi không hoàn toàn chắc chắn với câu trả lời này do [lý do], nhưng dựa trên nguồn hiện có, đây là câu trả lời bạn có thể tham khảo:"

**1. Kết luận trực tiếp** (1-2 câu):

- Đáp án chính xác, rõ ràng
- Đi thẳng vào vấn đề được hỏi

**2. Cơ sở pháp lý** (2-3 điểm):

- Trích dẫn điều luật: (Điều X, Khoản Y) của [Tên văn bản]
- Nội dung ngắn gọn của quy định
- Cách áp dụng vào trường hợp cụ thể

**3. Hậu quả/Rủi ro** (nếu có):

- Hậu quả nếu vi phạm quy định
- Mức xử phạt hoặc chế tài (nếu có)

**4. Hành động cần làm** (nếu có):

- Khuyến nghị cụ thể, thực tế
- Cơ quan có thẩm quyền giải quyết

**Yêu cầu bắt buộc:**
✅ CHÍNH XÁC - trích dẫn chính xác điều luật, không truy cập dự đoán
✅ TRỰC TIẾP - không dài dòng, đi thẳng vào vấn đề
✅ RÕ RÀNG - dễ hiểu, không mơ hồ
✅ ĐỊNH DẠNG - (Điều X, Khoản Y) của [Tên văn bản]
✅ TRÌNH BÀY - Sử dụng gạch đầu dòng và xuống dòng kép để dễ đọc.

TRẢ LỜI (Nhớ dùng Markdown thoáng mắt):'''
    
    try:
        response = gemini_model.generate_content(prompt)
        answer = response.text.strip()
        
        # Log mode
        mode_name = "DETAIL (Deep Reasoning)" if use_advanced else "SUMMARY (Concise)"
        print(f'[GENERATION] Mode: {mode_name}, Length: {len(answer)} chars')
        
        return answer
    except Exception as e:
        print(f'[ERROR] Gemini API error: {e}')
        return 'Xin lỗi, không thể tạo câu trả lời lúc này.'


def generate_suggested_questions(question: str, answer: str, gemini_model, max_questions: int = 3) -> List[str]:
    """
    Generate suggested follow-up questions based on the answer
    
    Args:
        question: Original user question
        answer: Generated answer
        gemini_model: Gemini model instance
        max_questions: Maximum number of questions to suggest (default 3)
    
    Returns:
        List of suggested questions
    """
    try:
        prompt = f"""Dựa trên câu hỏi và câu trả lời về pháp luật sau, hãy gợi ý {max_questions} câu hỏi tiếp theo mà người dùng có thể quan tâm.

CÂU HỎI GỐC: {question}

CÂU TRẢ LỜI: {answer[:500]}...

YÊU CẦU:
- Gợi ý {max_questions} câu hỏi liên quan hoặc mở rộng vấn đề
- Mỗi câu hỏi trên 1 dòng
- Format: "💭 Có lẽ bạn sẽ quan tâm đến [vấn đề], có cần tôi trả lời cho bạn không?"
- Ngắn gọn, dễ hiểu, liên quan trực tiếp

CHỈ TRẢ LỜI CÁC CÂU HỎI, KHÔNG GIẢI THÍCH:"""
        
        response = gemini_model.generate_content(prompt)
        text = response.text.strip()
        
        # Parse questions
        questions = []
        for line in text.split('\n'):
            line = line.strip()
            if line and ('💭' in line or 'quan tâm' in line.lower()):
                questions.append(line)
        
        return questions[:max_questions]
    
    except Exception as e:
        print(f'[ERROR] Failed to generate suggested questions: {e}')
        return []


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

def format_sources_for_display(sources: List[Dict]) -> dict:
    """
    Format sources with proper law names from domain registry
    RETURNS: Dict with sources array and display text
    """
    if not sources:
        return {"sources": [], "display": ""}
    
    # Load registry
    try:
        registry_path = Path("data/domain_registry.json")
        if registry_path.exists():
            with open(registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
        else:
            registry = {}
    except Exception as e:
        print(f"[WARNING] Cannot load registry: {e}")
        registry = {}
    
    # Group by domain
    by_domain = {}
    sources_list = []
    
    for src in sources:
        metadata = src.get('metadata', {})
        law_id = metadata.get('law_id', metadata.get('domain_id', 'unknown'))
        
        # Lookup proper name
        law_name = None
        
        # Try exact match
        if law_id in registry:
            law_name = registry[law_id]['name']
        else:
            # Try without _hopnhat suffix
            clean_id = law_id.replace('_hopnhat', '').replace('luat_', '')
            if clean_id in registry:
                law_name = registry[clean_id]['name']
        
        # Fallback to metadata
        if not law_name:
            law_name = metadata.get('law_name', law_id)
        
        article_num = metadata.get('article_num', '?')
        
        # Add to sources list for frontend
        sources_list.append({
            "law_name": law_name,
            "domain_id": law_id,
            "article_num": str(article_num)
        })
        
        # Group for display text
        if law_name not in by_domain:
            by_domain[law_name] = set()
        by_domain[law_name].add(str(article_num))
    
    # Format display text
    lines = ["📚 Nguồn tham khảo:\n"]
    for idx, (law_name, articles) in enumerate(by_domain.items(), 1):
        article_list = sorted(articles, key=lambda x: int(x) if x.isdigit() else 999)
        lines.append(f"{idx}. **{law_name}**")
        lines.append(f"   📊 {len(article_list)} điều được tham chiếu")
        lines.append("")
    
    return {
        "sources": sources_list,
        "display": "\n".join(lines)
    }