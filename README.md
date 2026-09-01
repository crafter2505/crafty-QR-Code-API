# 🔲 Crafty QR Code API

A production-ready QR Code generation API with authentication, email verification, rate limiting, and multi-tier plans. Built with FastAPI, SQLite, and Resend for email delivery.

## ✨ Features

- ✅ **QR Code Generation** — Generate QR codes from any URL or text
- ✅ **API Key Authentication** — Secure endpoints with API keys
- ✅ **Email Verification** — Verify user emails before they can generate API keys
- ✅ **Multi-Tier Plans** — Free, Pro, and Enterprise plans with different rate limits
- ✅ **Rate Limiting** — Protect against abuse (5 requests/minute)
- ✅ **SQLite Database** — Lightweight, portable, no external database needed
- ✅ **Auto-Generated Docs** — Swagger UI at `/docs`
- ✅ **CORS Enabled** — Ready for frontend integration

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/crafter2505/crafty-QR-Code-API.git
cd crafty-QR-Code-API

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Resend API key
```

### Running the Server

```bash
py -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

---

## 📡 API Endpoints

### Public Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | API information |
| `GET` | `/health` | Health check |
| `POST` | `/register` | Register a new user |
| `GET` | `/verify` | Verify email address |

### Protected Endpoints (Requires API Key)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/generate` | Generate a QR code |

---

## 🔑 Authentication

All protected endpoints require an API key sent in the request header:

```http
X-API-Key: QR_Free_xxxxxxxxxxxxxxxxxxxx
```

### How to Get an API Key

1. **Register** — `POST /register` with your email and plan
2. **Verify** — Click the verification link sent to your email
3. **Get Key** — Your API key is returned in the registration response

---

## 📊 Plans & Rate Limits

| Plan | Daily Limit | Prefix |
| :--- | :--- | :--- |
| **Free** | 10 requests/day | `QR_Free_` |
| **Pro** | 1,000 requests/day | `QR_Pro_` |
| **Enterprise** | 10,000 requests/day | `QR_Ent_` |

---

## 📝 Example Usage

### Register a User

```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "plan": "Free"}'
```

### Generate a QR Code

```bash
curl -X GET "http://localhost:8000/generate?data=https://github.com&size=10" \
  -H "X-API-Key: QR_Free_xxxxxxxxxxxxxxxxxxxx"
```

### Using with Python

```python
import requests

response = requests.get(
    "http://localhost:8000/generate",
    params={"data": "https://github.com", "size": 10},
    headers={"X-API-Key": "QR_Free_xxxxxxxxxxxxxxxxxxxx"}
)

with open("qr_code.png", "wb") as f:
    f.write(response.content)
```
or use "http://localhost:8000/docs".
---

## 🛠️ Tech Stack

| Technology | Purpose |
| :--- | :--- |
| **FastAPI** | Web framework |
| **SQLite** | Database |
| **Resend** | Email delivery |
| **qrcode** | QR code generation |
| **slowapi** | Rate limiting |

---

## 📁 Project Structure

```
crafty-QR-Code-API/
├── app/
│   ├── auth.py          # API key authentication
│   ├── database.py      # SQLite operations
│   ├── main.py          # FastAPI app
│   └── models.py        # Pydantic schemas
├── requirements.txt
├── .env                 # Environment variables
└── README.md
```

---

## 🧪 Testing

### Swagger UI

Open `http://localhost:8000/docs` for interactive API documentation.

### Curl Examples

```bash
# Register
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "plan": "Free"}'

# Verify email (click the link in your inbox)

# Generate QR
curl -X GET "http://localhost:8000/generate?data=https://github.com&size=10" \
  -H "X-API-Key: QR_Free_xxxxxxxxxxxxxxxxxxxx"
```

---

## 🔒 Security

- API key authentication
- Email verification
- Rate limiting (5 requests/minute)
- Input validation (max 512 characters)
- SQLite with parameterized queries (SQL injection safe)

---

## 📄 License

MIT

---

## 🙏 Credits

Built by [crafter2505](https://github.com/crafter2505)

---
