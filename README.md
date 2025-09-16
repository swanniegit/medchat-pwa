# MedChat PWA - WhatsApp Clone for Medical Workers

A secure, real-time messaging PWA designed for medical allied workers.

## Architecture

- **Backend:** FastAPI + WebSockets + PostgreSQL
- **Frontend:** Vanilla JS PWA with real-time messaging
- **Deployment:** DigitalOcean ready

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
python -m http.server 3000
```

## Features

- ✅ Real-time messaging
- ✅ PWA with offline support
- ✅ Cross-platform (iOS, Android, Desktop)
- ✅ Push notifications
- ✅ Medical-grade security ready

## POC Status

Building core messaging functionality first.