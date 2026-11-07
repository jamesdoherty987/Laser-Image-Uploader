# Laser Image Uploader

MVP web app: upload an image → AI-edit with natural language → prepare for laser engraving → send to CorelDRAW on a Windows PC via a small desktop connector.

Self-contained folder — copy it elsewhere when you want its own repo.

## Stack (matched to Student Padel Ireland)

| Layer | Choice |
|--------|--------|
| Frontend | React + Vite + TypeScript |
| Backend | FastAPI + SQLAlchemy (SQLite locally) |
| Storage | Local filesystem keys (ready to swap for object storage) |
| Desktop | Python background app + PyInstaller (Stages 5–6) |
| UI reference | `aceternity/` (file-upload / compare adapted to sharp B&W) |

## Architecture

```
Customer browser                FastAPI API                 Windows laptop
─────────────────               ───────────                 ──────────────
Upload / preview  ──HTTPS──►  jobs + file storage
AI edit chat      ──HTTPS──►  OpenAI Images API (key server-side only)
Accept → prepare  ──HTTPS──►  Pillow / OpenCV pipeline
Send to Corel     ──HTTPS──►  job status = ready  ◄── poll/pull ── desktop app
                                                          │
                                                          ▼
                                                     CorelDRAW (COM)
                                                          │
                                                          ▼
                                                   Teacher → GCC X252
```

- **No accounts / payments** in this MVP.
- API keys stay in backend `.env` only.
- Desktop installs get a unique pairing token before they can download jobs.
- CorelDRAW stays the final teacher-controlled step — we never drive the laser.

## Development stages

| Stage | Status | Scope |
|-------|--------|--------|
| **1** | **Done (this folder)** | Website + upload + preview |
| 2 | Next | OpenAI image edits + chat UI + successive edits |
| 3 | Pending | Laser preparation pipeline (Pillow/OpenCV) |
| 4 | Pending | Job queue polish + ready downloads |
| 5 | Pending | Windows desktop connector + auto-start |
| 6 | Pending | CorelDRAW COM import (claim only after real test) |
| 7 | Pending | End-to-end verification |

## Design

Clean black-and-white UI, sharp corners (`border-radius: 0`), Space Grotesk, minimal controls. Upload UX adapted from Aceternity `file-upload`; before/after compare reserved for Stage 2+.

## Quick start

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — Vite proxies `/api` and `/uploads` to the backend.

### Tests

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. pytest tests/ -v
```

## Project layout

```
Laser-Image-Uploader/
  aceternity/          # UI reference components (from parent repo)
  frontend/            # React + Vite + TypeScript
  backend/             # FastAPI API + local storage
  desktop/             # Windows CorelDRAW connector (Stages 5–6)
```

## Stage 1 API

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness |
| `POST` | `/api/images/upload` | Multipart image upload → job |
| `GET` | `/api/images/{id}` | Job + preview URLs |
| `GET` | `/api/images/{id}/status` | Status only |

Job statuses (full lifecycle): `uploaded` → `editing` → `edited` → `preparing` → `ready` → `downloading` → `imported` (or `failed`).

## Environment

See `backend/.env.example`. Stage 1 only needs defaults. Set `OPENAI_API_KEY` when starting Stage 2.
