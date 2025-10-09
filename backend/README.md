# Legal Q&A Backend

Backend API cho hệ thống hỏi đáp pháp luật Việt Nam.

## 🚀 Cài đặt

### 1. Cài đặt dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Chuẩn bị dữ liệu

Tạo thư mục `data/` và đặt các file JSON luật vào đó:

```
backend/
├── data/
│   ├── luat_hon_nhan_hopnhat.json
│   ├── luat_lao_donghopnhat.json
│   └── ...
```

### 3. Chạy server

```bash
python app.py
```

Server sẽ chạy tại: `http://localhost:8000`

## 📚 API Endpoints

### Health Check
```bash
GET http://localhost:8000/
```

### Hỏi đáp
```bash
POST http://localhost:8000/ask
Content-Type: application/json

{
  "question": "Quy định độ tuổi kết hôn?",
  "use_advanced": true
}
```

### Thống kê
```bash
GET http://localhost:8000/stats
```

## 📖 API Docs

Swagger UI: `http://localhost:8000/docs`
