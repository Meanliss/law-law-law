# 🏛️ Legal Document Q&A System

> Advanced RAG (Retrieval-Augmented Generation) system for Vietnamese legal documents with Docker support

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🌟 Features

### Core Capabilities
- ✅ **Hybrid Search**: BM25 (keyword) + FAISS (semantic) with reranking
- ✅ **Intent Detection**: 3-layer system (rule-based → keyword → LLM)
- ✅ **Query Expansion**: Pattern-based expansion for 8 legal domains
- ✅ **Dual LLM Models**: 
  - Gemini Flash (answer generation)
  - Gemini Flash Lite (intent detection - 50% cheaper)
- ✅ **Smart Caching**: MD5 hash-based cache invalidation
- ✅ **Vietnamese Support**: Underthesea tokenization

### Architecture
- ✅ **Modular Design**: Clean separation of concerns (11 modules)
- ✅ **Docker Support**: One-command deployment
- ✅ **Production Ready**: Nginx proxy, health checks, auto-restart
- ✅ **Hot Reload**: Development mode with auto-reload

---

## 🚀 Quick Start

**Prerequisites:**
- Docker Desktop installed
- GOOGLE_API_KEY in `backend/.env`

**5-Minute Setup:**
```powershell
cd d:\KHDL\web
.\scripts\docker-manage.ps1 start
```

**Access:**
- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**For full installation guide (Docker + Non-Docker), see:** [**SETUP.md**](SETUP.md)

---

## 📂 Project Structure

```
web/
├── frontend/                   # Web UI
│   ├── index.html             # Main page
│   ├── app.js                 # API integration
│   └── styles.css             # Styling
│
├── backend/                    # FastAPI backend
│   ├── app.py                 # Main application (220 lines)
│   ├── config.py              # Configuration & constants
│   ├── models.py              # Pydantic models
│   ├── core/                  # Core business logic
│   │   ├── intent_detection.py    # 3-layer intent system
│   │   ├── query_expansion.py     # Query expansion rules
│   │   ├── search.py              # Hybrid search
│   │   ├── generation.py          # LLM answer generation
│   │   └── document_processor.py  # JSON parser
│   ├── utils/                 # Utility functions
│   │   ├── cache.py               # Cache management
│   │   └── tokenizer.py           # Vietnamese tokenization
│   ├── tests/                 # Test suite
│   ├── data/                  # Legal JSON documents (6 files)
│   ├── cache/                 # BM25 + FAISS cache
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Backend container config
│   └── .env                   # Environment variables
│
├── docs/                       # Documentation
│   ├── API.md                 # API reference
│   └── DOCKER.md              # Docker advanced guide
│
├── scripts/                    # Management scripts
│   ├── docker-manage.ps1      # Docker commands
│   └── migrate.ps1            # Project migration
│
├── docker-compose.yml         # Multi-container orchestration
├── nginx.conf                 # Nginx configuration
├── SETUP.md                   # Installation guide
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Search**: BM25Okapi + FAISS (CPU)
- **Embeddings**: SentenceTransformer (paraphrase-multilingual-MiniLM-L12-v2)
- **LLM**: Google Gemini AI (Flash + Flash Lite)
- **NLP**: Underthesea (Vietnamese tokenization)
- **Python**: 3.12

### Frontend
- **HTML5** + **CSS3** + **Vanilla JavaScript**
- **Responsive Design**: Mobile-friendly
- **Theme**: Dark/Light mode

### Infrastructure (Docker)
- **Backend Container**: Python 3.12 slim
- **Frontend Container**: Nginx Alpine
- **Orchestration**: Docker Compose
- **Persistence**: Docker volumes

---

## 📊 Performance

### Search Performance
- **BM25 Weight**: 40%
- **FAISS Weight**: 60%
- **Reranking**: Semantic similarity (cosine)
- **Top-K**: 8 results (16 candidates → rerank)

### Intent Detection (3-Layer)
| Layer | Method | Time | Cost | Coverage |
|-------|--------|------|------|----------|
| 1 | Rule-based | <1ms | $0 | ~30% |
| 2 | Keyword scoring | ~10ms | $0 | ~40% |
| 3 | LLM Lite | ~500ms | $0.0005 | ~30% |

**Total Savings**: 70% queries avoid LLM, 30% usage reduction

### Cache Performance
- **BM25 Index**: ~2MB (6 legal documents)
- **FAISS Index**: ~50MB (embeddings)
- **Load Time**: <1s (from cache)
- **Rebuild Time**: ~30s (on data change)

---

## 🎯 Supported Legal Domains

1. **Marriage Law** (Luật Hôn nhân)
2. **Labor Law** (Luật Lao động)
3. **Land Law** (Luật Đất đai)
4. **Contract Law** (Hợp đồng)
5. **Criminal Law** (Luật Hình sự)
6. **Civil Law** (Luật Dân sự)
7. **Bidding Law** (Luật Đấu thầu)
8. **Technology Transfer Law** (Chuyển giao công nghệ)

**Total Documents**: 6 legal documents
**Total Chunks**: ~3,000+ searchable segments

---

## 🔧 Configuration

### Environment Variables (`backend/.env`)
```env
GOOGLE_API_KEY=your_api_key_here
```

### Model Configuration (`config.py`)
```python
# Models
GEMINI_FULL_MODEL = "gemini-2.5-flash"        # Answer generation
GEMINI_LITE_MODEL = "gemini-2.5-flash-lite"  # Intent detection
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# Search weights
BM25_WEIGHT = 0.4
FAISS_WEIGHT = 0.6

# Intent detection thresholds
INTENT_KEYWORD_ACCEPT_THRESHOLD = 0.4  # Accept if score >= 0.4
INTENT_KEYWORD_REJECT_THRESHOLD = 0.15 # Reject if score < 0.15
```

---

## 📚 Documentation

| File | Purpose | When to Use |
|------|---------|-------------|
| [**README.md**](README.md) | Project overview & quick start | First-time visitors |
| [**SETUP.md**](SETUP.md) | Complete installation guide | Setting up the project |
| [**docs/API.md**](docs/API.md) | API endpoint reference | Developing integrations |
| [**docs/DOCKER.md**](docs/DOCKER.md) | Advanced Docker topics | Production deployment |

---

## 🐳 Docker Management

### Quick Commands
```powershell
# Start all services
.\scripts\docker-manage.ps1 start

# View logs (follow mode)
.\scripts\docker-manage.ps1 logs

# Check status + resource usage
.\scripts\docker-manage.ps1 status

# Restart services
.\scripts\docker-manage.ps1 restart

# Stop services
.\scripts\docker-manage.ps1 stop

# Clean everything (containers + volumes)
.\scripts\docker-manage.ps1 clean

# Open backend shell
.\scripts\docker-manage.ps1 shell

# Show all commands
.\scripts\docker-manage.ps1 help
```

---

## 🔍 API Endpoints

### Health Check
```bash
GET /
Response: {"status": "healthy", "models_loaded": true, "total_chunks": 3000}
```

### Ask Question
```bash
POST /ask
Body: {
  "question": "Quy định về độ tuổi kết hôn?",
  "use_advanced": true
}
Response: {
  "answer": "...",
  "sources": [...],
  "search_mode": "advanced"
}
```

### Statistics
```bash
GET /stats
Response: {
  "total_chunks": 3000,
  "laws": {...},
  "models": {...},
  "intent_cache_size": 150
}
```

**Interactive API Docs**: http://localhost:8000/docs (when running)

**See:** [**docs/API.md**](docs/API.md) for complete reference

---

## 🧪 Testing

### Manual Test (Docker)
```powershell
# Start services
.\docker-manage.ps1 start

# Test health
curl http://localhost:8000/

# Test API
curl -X POST http://localhost/api/ask `
  -H "Content-Type: application/json" `
  -d '{"question":"Điều kiện kết hôn?","use_advanced":true}'

# Open frontend
start http://localhost
```

### Unit Tests (Future)
```powershell
cd backend
pytest tests/
```

---

## 🚀 Deployment

### Docker Hub
```powershell
# Build production image
docker build -t your-username/legal-qa-backend:latest ./backend

# Push to Docker Hub
docker push your-username/legal-qa-backend:latest

# Pull on server
docker pull your-username/legal-qa-backend:latest
docker run -d -p 8000:8000 --env-file .env your-username/legal-qa-backend:latest
```

### Cloud Platforms
- **AWS**: ECS/Fargate with ALB
- **GCP**: Cloud Run or GKE
- **Azure**: Container Instances or AKS

---

## 🛡️ Security

### Implemented
- ✅ Environment variables (not hardcoded)
- ✅ .dockerignore (exclude sensitive files)
- ✅ Non-root user in containers
- ✅ Network isolation (Docker bridge)
- ✅ Health checks for auto-recovery

### Production Recommendations
- [ ] HTTPS with Let's Encrypt
- [ ] Rate limiting
- [ ] API authentication (OAuth2/JWT)
- [ ] Input validation & sanitization
- [ ] Security headers (CORS, CSP)
- [ ] Secrets management (Vault, AWS Secrets)

---

## 🐛 Troubleshooting

### Common Issues

**Port already in use**
```powershell
# Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Docker not starting**
1. Check Docker Desktop is running
2. Verify `.env` file exists with API key
3. Check logs: `.\docker-manage.ps1 logs`

**Cache not updating**
```powershell
# Force rebuild cache
docker-compose down -v
docker-compose up --build
```

**Memory issues**
- Increase Docker Desktop memory: Settings → Resources → Memory
- Minimum: 4GB, Recommended: 8GB

---

## 📈 Roadmap

### v2.1 (Next)
- [ ] Add unit tests (pytest)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Logging aggregation (ELK)
- [ ] Monitoring (Prometheus + Grafana)

### v3.0 (Future)
- [ ] User authentication
- [ ] Multi-user support
- [ ] Conversation history (PostgreSQL)
- [ ] Admin dashboard
- [ ] More legal documents (expand from 6 to 20+)

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Meanliss** - Initial work

---

## 🙏 Acknowledgments

- Google Gemini AI for LLM capabilities
- Sentence Transformers for multilingual embeddings
- Underthesea for Vietnamese NLP
- FastAPI for excellent documentation
- Docker for containerization

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Meanliss/law-law-law/issues)
- **Documentation**: See `docs/` folder
- **Quick Help**: Run `.\docker-manage.ps1 help`

---

**Made with ❤️ for Vietnamese Legal Tech**

*Last Updated: October 11, 2025*
*Version: 2.0.0 (Dockerized)*

