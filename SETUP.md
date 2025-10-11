# 🚀 Hướng Dẫn Cài Đặt - Legal Q&A System

## 📋 Yêu Cầu

- **Docker Desktop** (khuyến nghị) hoặc **Python 3.12**
- **Google API Key** (Gemini AI)
- **4GB RAM** tối thiểu

---

## ⚡ Quick Start (Docker - 5 phút)

### 1. Cài Docker Desktop
Download: https://www.docker.com/products/docker-desktop

### 2. Tạo file `.env`
```powershell
cd backend
# Tạo file .env với nội dung:
GOOGLE_API_KEY=your_api_key_here
```

### 3. Chạy
```powershell
cd d:\KHDL\web
.\scripts\docker-manage.ps1 start
```

### 4. Truy cập
- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🐳 Quản Lý Docker

```powershell
# Xem logs
.\scripts\docker-manage.ps1 logs

# Kiểm tra status
.\scripts\docker-manage.ps1 status

# Dừng
.\scripts\docker-manage.ps1 stop

# Xóa tất cả (reset)
.\scripts\docker-manage.ps1 clean
```

---

## 💻 Cài Đặt Local (Không dùng Docker)

### 1. Cài Python 3.12
Download: https://www.python.org/downloads/

### 2. Setup Backend
```powershell
cd backend

# Tạo virtual environment
python -m venv venv
venv\Scripts\activate

# Cài dependencies
pip install -r requirements.txt

# Tạo .env file
# GOOGLE_API_KEY=your_api_key_here

# Chạy
python app.py
```

### 3. Mở Frontend
- Mở file `frontend/index.html` trong browser
- Hoặc dùng Live Server extension (VS Code)

### 4. Truy cập
- **Backend API**: http://localhost:8000
- **Frontend**: `frontend/index.html`

---

## 🐛 Troubleshooting

### Port bị chiếm
```powershell
# Tìm process đang dùng port 8000
netstat -ano | findstr :8000

# Kill process (thay <PID>)
taskkill /PID <PID> /F
```

### Docker không start
1. Kiểm tra Docker Desktop đang chạy
2. Verify file `.env` tồn tại với API key hợp lệ
3. Xem logs: `.\scripts\docker-manage.ps1 logs`

### Backend lỗi khi start
1. Kiểm tra Python version: `python --version` (phải 3.12)
2. Cài lại dependencies: `pip install -r requirements.txt`
3. Kiểm tra GOOGLE_API_KEY trong `.env`

---

## 📚 Tài Liệu Bổ Sung

- **API Reference**: `docs/API.md`
- **Docker Chi Tiết**: `docs/DOCKER.md`
- **Cấu Trúc Project**: `README.md`

---

## ✅ Kiểm Tra Cài Đặt

```powershell
# Test backend
curl http://localhost:8000/

# Response mong đợi:
# {"status":"healthy","models_loaded":true,"total_chunks":3000}

# Test frontend
start http://localhost
# Gõ câu hỏi: "Quy định về độ tuổi kết hôn?"
```

---

**🎉 Done! Bắt đầu sử dụng hệ thống.**

Gặp vấn đề? Xem `docs/API.md` hoặc tạo GitHub Issue.
