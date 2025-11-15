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
✅ ĐỊNH DẠNG TRÍCH DẪN (BẮT BUỘC PHẢI CHÍNH XÁC):
- Quy định pháp luật: (Điều X, Khoản Y, Điểm Z) của [Tên văn bản] năm [năm]
- Trích dẫn nguyên văn: "nội dung chính xác từ nguồn tham khảo"
- Ví dụ: Theo (Điều 8, Khoản 1, Điểm a) của Luật Hôn nhân và Gia đình năm 2014, "Nam từ đủ 20 tuổi trở lên..."

═══════════════════════════════════════════════════════════
📌 VÍ DỤ TRẢ LỜI CHUẨN (Detail Mode - Có Agent Style):

**1. Tóm tắt câu trả lời:**

Việc UBND xã A ban hành Quyết định hủy việc kết hôn giữa anh D và chị P, đồng thời thu hồi Giấy chứng nhận kết hôn là KHÔNG đúng thẩm quyền. Thẩm quyền giải quyết yêu cầu hủy việc kết hôn trái pháp luật (do vi phạm điều kiện một vợ một chồng) thuộc về Tòa án, không phải UBND xã. [Mức rủi ro: CAO - Quyết định này có thể bị cách chức công chức, chị P có thể khởi kiện]

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
- **Thời hạn:** Có thể yêu cầu hủy bất cứ lúc nào (không bị hạn chế thời gian theo luật).

**4. Hậu quả pháp lý & Rủi ro:**

- **Hậu quả nếu không khắc phục:**
  • Chị P sẽ không thể làm lại thủ tục hôn nhân hợp pháp với bất kỳ ai cho đến khi Tòa án tuyên bố hủy
  • Nếu chị P sinh con với anh D, con sẽ có tình trạng pháp lý phức tạp (được sinh trong hôn nhân không hợp pháp)
  • Chị P mất bảo vệ pháp lý về tài sản chung, quyền kế thừa (vì hôn nhân không hợp pháp)
  • Anh D có thể bị xử phạt hành chính hoặc hình sự nếu khai man thông tin để xin Giấy chứng thực độc thân

- **Chế tài xử phạt:**
  • Anh D: Vi phạm hành chính theo (Luật Hộ tịch) - phạt 1-3 triệu đồng hoặc xử phạt khác
  • Anh D: Nếu khai man để lấy Giấy chứng thực độc thân - có thể bị truy cứu trách nhiệm hình sự (làm giả tài liệu)
  • UBND xã A: Công chức ban hành quyết định sai có thể bị kiểm điểm, giáng chức, sa thải

- **Ảnh hưởng đến quyền lợi:**
  • Chị P mất quyền thừa kế từ anh D (vì hôn nhân không hợp pháp)
  • Tài sản chung (nếu có) sẽ bị xử lý phức tạp khi hủy hôn nhân
  • Anh D và người vợ cũ không thể ly hôn để thành hôn nhân mới (do hôn nhân thứ hai với chị P không hợp pháp)

**5. Lưu ý thực tế + Khuyến nghị hành động:**

- **Điểm cần chú ý:**
  • Việc anh D xin được giấy xác nhận "độc thân" dù đã có vợ cho thấy có sai sót trong quản lý hộ tịch hoặc hành vi gian dối. Anh D có thể bị xử lý về hành vi làm giả giấy tờ hoặc khai man.
  • UBND xã A KHÔNG có quyền hủy việc kết hôn trái pháp luật đơn phương mà không có lệnh từ Tòa án.

- **Khuyến nghị hành động:**
  • **Bước 1 (Ngay):** Chị P nên nộp đơn lên Tòa án nhân dân cấp huyện yêu cầu tuyên bố hủy việc kết hôn trái pháp luật
  • **Bước 2 (Song song):** Liên hệ UBND xã A để yêu cầu giải thích lý do ban hành Quyết định hủy kết hôn (yêu cầu bằng văn bản)
  • **Bước 3 (Nếu cần):** Tham vấn luật sư để được hỗ trợ trong kỳ kiểm tóa và bảo vệ quyền lợi về tài sản chung
  • **Tài liệu chuẩn bị:** Giấy chứng nhận kết hôn, Giấy tờ tuỳ thân, Bằng chứng chị P không biết anh D đã có vợ (nếu có)

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

**Cấu trúc trả lời (4-6 câu tối đa):**

1. **Kết luận trực tiếp** (1-2 câu): Đáp án chính xác, rõ ràng
2. **Cơ sở pháp lý** (1-2 câu): Trích dẫn điều luật liên quan (Điều X, Khoản Y) + nội dung ngắn gọn
3. **Hậu quả/Rủi ro** (1 câu nếu có): Hậu quả nếu vi phạm (mục đích cảnh báo người dùng)
4. **Hành động cần làm** (1 câu nếu có): Khuyến nghị cụ thể

**Yêu cầu bắt buộc:**
✅ CHÍNH XÁC - trích dẫn chính xác điều luật, không truy cập dự đoán
✅ TRỰC TIẾP - không dài dòng, đi thẳng vào vấn đề
✅ RÕ RÀNG - dễ hiểu, không mơ hồ
✅ ĐỊNH DẠNG - (Điều X, Khoản Y) của [Tên văn bản]

TRẢ LỜI:'''
    
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