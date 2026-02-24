English | [中文](./README.md)

# LangPod - Language Learning Platform

A WeChat Mini Program for language learning, featuring adaptive assessment, scenario-based dialogue practice, SRS vocabulary review, and personalized study plans.

## Features

- **Adaptive Proficiency Assessment** — IRT-based English level evaluation covering A1–C2
- **Scenario Dialogue Practice** — 10+ real-world scenarios (travel, business, academic, daily life) with multi-turn audio dialogues
- **SRS Vocabulary Management** — Spaced repetition system for optimal review scheduling
- **Learning Plans** — Personalized study paths generated from assessment results with streak tracking
- **Content Import/Export** — Import from text or URL, export study cards as images
- **TTS Audio** — Natural pronunciation via Edge TTS

## Architecture

```
miniprogram/          # WeChat Mini Program frontend (WXML/WXSS/TypeScript)
├── pages/            # 15 pages
├── components/       # 9 reusable components
├── services/         # API service layer
├── store/            # Global state management
└── custom-tab-bar/   # Custom bottom navigation

backend/              # FastAPI backend
├── app/
│   ├── domain/       # Domain models
│   ├── infra/        # Infrastructure (config/middleware/JWT/rate-limit)
│   ├── repositories/ # Data access layer (in-memory / CloudBase)
│   ├── routes/       # Route modules
│   ├── schemas/      # Request/response models
│   └── services/     # Business logic
└── tests/            # Test suite

data/                 # Seed data (questions/dialogues/scenarios)
```

## Getting Started

### Prerequisites

- Python 3.11+
- [WeChat DevTools](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
- FFmpeg (for audio processing)

### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start the server
uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs` once the server is running.

### Frontend

1. Open the `miniprogram/` directory in WeChat DevTools
2. Configure the backend URL in `app.js`
3. Build and run

### Docker

```bash
cd backend
docker build -t langpod-backend .
docker run -p 80:80 --env-file .env langpod-backend
```

## API Overview

| Module | Endpoint | Description |
|--------|----------|-------------|
| Auth | `POST /auth/me` | WeChat login, returns JWT |
| Content | `GET /content` | List learning content |
| Vocab | `POST /vocab` | Add word to vocabulary |
| Vocab | `GET /vocab/due` | Get words due for review |
| Assessment | `POST /api/assessment/start` | Start proficiency test |
| Scenarios | `POST /api/scenarios/start` | Start scenario practice |
| Plan | `GET /plan/stats` | Learning statistics |
| Import | `POST /import` | Import from text/URL |

Full API documentation is available at the `/docs` endpoint (Swagger UI).

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ENV` | Runtime environment | `dev` |
| `REPO_PROVIDER` | Data store (`memory` / `tcb`) | `memory` |
| `JWT_SECRET` | JWT signing secret | dev default |
| `WECHAT_AUTH_ENABLED` | Enable real WeChat auth | `false` |
| `STORAGE_PROVIDER` | File storage (`local` / `cos`) | `local` |

## Testing

```bash
cd backend
pytest
```

## Project Status

All MVP features are complete with 59+ tests passing.

### Production Checklist

- [ ] Set `REPO_PROVIDER=tcb` with CloudBase credentials
- [ ] Set a strong `JWT_SECRET` for production
- [ ] Configure server domain whitelist in WeChat admin console
- [ ] Enable WeChat authentication
- [ ] Deploy to WeChat CloudBase

## License

MIT
