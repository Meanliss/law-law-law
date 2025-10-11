# 📡 API Reference

REST API documentation for Legal Q&A Backend.

**Base URL**: `http://localhost:8000`

**Version**: 2.0.0

---

## 🔐 Authentication

Currently no authentication required (development mode).

**Production**: Will require API key or OAuth2.

---

## 📋 Endpoints

### Health Check

Check if the API is running and models are loaded.

```http
GET /
```

**Response** `200 OK`:
```json
{
  "status": "healthy",
  "models_loaded": true,
  "total_chunks": 3142
}
```

**Example**:
```bash
curl http://localhost:8000/
```

---

### Ask Question

Submit a legal question and get AI-generated answer with sources.

```http
POST /ask
Content-Type: application/json
```

**Request Body**:
```json
{
  "question": "Quy định về độ tuổi kết hôn?",
  "use_advanced": true
}
```

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | string | ✅ Yes | Legal question in Vietnamese |
| `use_advanced` | boolean | ❌ No | Use advanced search (default: true) |

**Response** `200 OK`:
```json
{
  "answer": "Theo quy định tại Luật Hôn nhân và Gia đình...",
  "sources": [
    {
      "source": "Luật Hôn nhân và Gia đình, Điều 8, Khoản 1",
      "content": "Nam từ đủ 20 tuổi trở lên, nữ từ đủ 18 tuổi..."
    }
  ],
  "search_mode": "advanced"
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | AI-generated answer |
| `sources` | array | List of legal document sources |
| `search_mode` | string | "advanced" or "simple" |

**Error Responses**:

`503 Service Unavailable`:
```json
{
  "detail": "System not ready"
}
```

`422 Unprocessable Entity`:
```json
{
  "detail": [
    {
      "loc": ["body", "question"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Điều kiện kết hôn?",
    "use_advanced": true
  }'
```

**JavaScript**:
```javascript
const response = await fetch('http://localhost:8000/ask', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    question: 'Điều kiện kết hôn?',
    use_advanced: true
  })
});

const data = await response.json();
console.log(data.answer);
```

**Python**:
```python
import requests

response = requests.post(
    'http://localhost:8000/ask',
    json={
        'question': 'Điều kiện kết hôn?',
        'use_advanced': True
    }
)

data = response.json()
print(data['answer'])
```

---

### Get Statistics

Get system statistics and cache information.

```http
GET /stats
```

**Response** `200 OK`:
```json
{
  "total_chunks": 3142,
  "laws": {
    "Luật Hôn nhân và Gia đình": 245,
    "Luật Lao động": 512,
    "Luật Đất đai": 398,
    "...": "..."
  },
  "models": {
    "embedder": "paraphrase-multilingual-MiniLM-L12-v2",
    "llm_full": "gemini-2.5-flash (answer generation)",
    "llm_lite": "gemini-2.5-flash-lite (intent detection, decomposition)"
  },
  "intent_cache_size": 147
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `total_chunks` | integer | Total searchable chunks |
| `laws` | object | Chunk count per legal document |
| `models` | object | Model information |
| `intent_cache_size` | integer | Number of cached intent results |

**Example**:
```bash
curl http://localhost:8000/stats
```

---

## 🎯 Search Modes

### Advanced Mode (`use_advanced: true`)

**Features**:
- ✅ Intent detection (filters non-legal queries)
- ✅ Query expansion (adds related aspects)
- ✅ Query decomposition (breaks complex questions)
- ✅ Hybrid search (BM25 + FAISS)
- ✅ Semantic reranking

**Best for**:
- Complex legal questions
- Questions requiring multiple aspects
- Formal legal queries

**Performance**: ~2-5 seconds

### Simple Mode (`use_advanced: false`)

**Features**:
- ✅ Direct hybrid search (BM25 + FAISS)
- ❌ No intent filtering
- ❌ No query expansion
- ❌ No decomposition

**Best for**:
- Simple queries
- Known legal terms
- Quick lookups

**Performance**: ~1-2 seconds

---

## 🔍 Query Examples

### Marriage Law
```json
{
  "question": "Quy định về độ tuổi kết hôn?",
  "use_advanced": true
}
```

### Labor Law
```json
{
  "question": "Quyền lợi của người lao động khi bị sa thải?",
  "use_advanced": true
}
```

### Land Law
```json
{
  "question": "Điều kiện chuyển nhượng quyền sử dụng đất?",
  "use_advanced": true
}
```

### Contract Law
```json
{
  "question": "Hợp đồng vô hiệu trong trường hợp nào?",
  "use_advanced": true
}
```

---

## 📊 Response Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 422 | Unprocessable Entity | Invalid request body |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | System not ready |

---

## ⚡ Rate Limiting

**Current**: No rate limiting (development)

**Production**: Will implement:
- 60 requests/minute per IP
- 1000 requests/hour per IP

---

## 🔧 CORS

**Current**: Allow all origins (`*`)

**Headers**:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

**Production**: Will restrict to specific domains.

---

## 📝 Request/Response Content Type

All requests and responses use:
```
Content-Type: application/json; charset=utf-8
```

---

## 🐛 Error Handling

### Standard Error Format

```json
{
  "detail": "Error message here"
}
```

### Validation Errors

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "error message",
      "type": "error_type"
    }
  ]
}
```

---

## 🧪 Testing

### Interactive API Docs

**Swagger UI**: http://localhost:8000/docs

**ReDoc**: http://localhost:8000/redoc

### Example Test Script

```python
import requests

BASE_URL = "http://localhost:8000"

# Test health check
response = requests.get(f"{BASE_URL}/")
assert response.status_code == 200
assert response.json()["status"] == "healthy"

# Test ask endpoint
response = requests.post(
    f"{BASE_URL}/ask",
    json={
        "question": "Điều kiện kết hôn?",
        "use_advanced": True
    }
)
assert response.status_code == 200
assert "answer" in response.json()

# Test stats
response = requests.get(f"{BASE_URL}/stats")
assert response.status_code == 200
assert "total_chunks" in response.json()

print("✅ All tests passed!")
```

---

## 📚 Additional Resources

- **OpenAPI Spec**: http://localhost:8000/openapi.json
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Pydantic Models**: See `backend/models.py`

---

**Version**: 2.0.0  
**Last Updated**: October 11, 2025
