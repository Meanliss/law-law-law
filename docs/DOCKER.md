# 🐳 Docker - Hướng Dẫn Nâng Cao

> **Quick Start?** Xem `../SETUP.md` thay vì file này.

Tài liệu này dành cho DevOps và advanced users.

---

## � Kiến Trúc Docker

```
┌─────────────────────────────────────────┐
│         http://localhost:80             │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │   Nginx Container (Alpine)       │   │
│  │   - Serve frontend files         │   │
│  │   - Proxy /api/* → backend:8000  │   │
│  │   - Gzip compression             │   │
│  └──────────┬───────────────────────┘   │
│             │                            │
│             ▼                            │
│  ┌──────────────────────────────────┐   │
│  │   FastAPI Backend (Python 3.12)  │   │
│  │   - Port: 8000                   │   │
│  │   - Hot reload: Enabled          │   │
│  │   - Volume: ./backend → /app     │   │
│  └──────────────────────────────────┘   │
│                                         │
│  Volumes:                               │
│  └─ legal-qa-cache (persistent)         │
└─────────────────────────────────────────┘
```

---

## 🔧 Cấu Hình Chi Tiết

### docker-compose.yml
### docker-compose.yml

**Services:**
- `backend`: Python 3.12 FastAPI app
- `frontend`: Nginx static file server + reverse proxy

**Networks:**
- `legal-qa-network`: Bridge network cho internal communication

**Volumes:**
- `legal-qa-cache`: Persistent cache (BM25 + FAISS)
- `./backend`: Hot reload (bind mount)
- `./frontend`: Static files (bind mount)

---

## 📋 Lệnh Docker Nâng Cao

### Quản lý containers
```powershell
# Xem containers đang chạy
docker-compose ps

# Xem logs
docker-compose logs -f              # All services
docker-compose logs -f backend      # Backend only
docker-compose logs -f frontend     # Frontend only

# Dừng containers
docker-compose stop

# Start lại containers
docker-compose start

# Restart containers
docker-compose restart

# Dừng và xóa containers
docker-compose down

# Dừng và xóa cả volumes (cache)
docker-compose down -v
```

### Build và update
```powershell
# Rebuild sau khi thay đổi code
docker-compose up --build

# Rebuild chỉ backend
docker-compose up --build backend

# Force rebuild (không dùng cache)
docker-compose build --no-cache
```

### Debug
```powershell
# Vào terminal của container backend
docker-compose exec backend bash

## 📋 Lệnh Docker Nâng Cao

```powershell
# Quản lý containers
docker-compose ps                    # Status
docker-compose logs -f backend       # Logs (follow)
docker-compose exec backend bash     # Shell vào container
docker stats                         # Resource usage

# Build & Deploy
docker-compose build --no-cache      # Force rebuild
docker-compose up --build backend    # Rebuild chỉ backend

# Volume management
docker volume ls                     # List volumes
docker volume rm legal-qa-cache      # Xóa cache
```

---

## 🔧 Configuration

### Environment Variables
File `backend/.env`:
```env
GOOGLE_API_KEY=your_api_key_here
```

### Port Mapping
```yaml
# docker-compose.yml
ports:
  - "8080:80"    # Frontend custom port
  - "8001:8000"  # Backend custom port
```

---

## � Production Deployment

### Docker Hub
```powershell
# Tag & push
docker tag web-backend your-username/legal-qa:latest
docker push your-username/legal-qa:latest

# Pull & run on server
docker pull your-username/legal-qa:latest
docker-compose up -d
```

### Disable Hot Reload
```yaml
# docker-compose.yml (production)
backend:
  volumes:
    - legal-qa-cache:/app/cache  # Chỉ cache, không mount code
  command: uvicorn app:app --host 0.0.0.0 --port 8000  # Bỏ --reload
```

---

## � Troubleshooting

```powershell
# Container không start
docker-compose logs backend

# Port bị chiếm
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Reset toàn bộ
docker-compose down -v
docker-compose up --build

# Memory issues
# Docker Desktop → Settings → Resources → Memory (4GB minimum)
```

---

## 🔐 Security Best Practices

1. ✅ Không commit `.env` (đã có trong `.gitignore`)
2. ✅ Dùng secrets cho production
3. ✅ Update base images thường xuyên
4. ✅ Scan vulnerabilities: `docker scan web-backend`

---

## 📚 Tài Liệu Tham Khảo

- [Docker Docs](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [FastAPI Docker](https://fastapi.tiangolo.com/deployment/docker/)

---

**Version**: 2.0.0  
**Last Updated**: October 11, 2025

2. **Multi-stage builds**: Giảm image size (nâng cao)
3. **Docker volumes**: Persist data giữa các lần restart
4. **Health checks**: Tự động restart khi unhealthy
5. **Resource limits**: Set CPU/memory limits trong production
