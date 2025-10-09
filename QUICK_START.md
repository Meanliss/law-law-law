# 🚀 Quick Start Guide - Legal Q&A System

## ✅ Đã cài đặt thành công!

Tất cả dependencies đã được cài đặt:
- ✅ FastAPI & Uvicorn
- ✅ Google Generative AI
- ✅ Sentence Transformers
- ✅ FAISS (CPU)
- ✅ BM25, Underthesea
- ✅ Torch & Transformers

---

## 🎯 Cách chạy hệ thống

### 1. **Khởi động Backend**

Mở terminal trong VS Code và chạy:

```powershell
cd backend
python app.py
```

Server sẽ chạy tại: **http://localhost:8000**

Bạn sẽ thấy:
```
🚀 Đang khởi động Legal Q&A System...
✅ Google AI đã sẵn sàng
✅ Tổng cộng: X chunks
🎉 Server sẵn sàng!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. **Mở Frontend**

- Mở file `index.html` bằng **Live Server** extension
- Hoặc double-click `index.html` trong browser

### 3. **Test hệ thống**

1. Gõ câu hỏi: "Quy định độ tuổi kết hôn?"
2. Nhấn Enter hoặc nút Send
3. Chờ AI trả lời (~5-10s)

---

## 📁 Thêm dữ liệu luật

Tạo thư mục `backend/data/` và copy file JSON luật vào:

```
backend/
└── data/
    ├── luat_hon_nhan_hopnhat.json
    ├── luat_lao_donghopnhat.json
    └── ...
```

**Restart backend** để load dữ liệu mới.

---

## 🔧 Troubleshooting

### Backend không khởi động?

```powershell
# Kiểm tra Python
python --version

# Kiểm tra dependencies
pip list | findstr "fastapi"
```

### Frontend không kết nối?

1. Đảm bảo backend đang chạy (http://localhost:8000)
2. Mở Console (F12) xem lỗi
3. Check CORS settings

### Lỗi "No module named..."?

```powershell
pip install -r requirements.txt
```

---

## 📚 API Endpoints

### Health Check
```
GET http://localhost:8000/
```

### Hỏi đáp
```
POST http://localhost:8000/ask
{
  "question": "Câu hỏi của bạn",
  "use_advanced": true
}
```

### Swagger UI
```
http://localhost:8000/docs
```

---

## 💡 Tips

1. **Cache**: Lần đầu chạy sẽ mất 2-3 phút để build index. Các lần sau chỉ mất vài giây!
2. **Advanced mode**: Tốt hơn cho câu hỏi phức tạp
3. **Simple mode**: Nhanh hơn cho câu hỏi đơn giản

---

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Check terminal output
2. Xem file `backend/README.md`
3. Test API: `backend/test_api.py`

---

**🎉 Chúc bạn sử dụng thành công!**
