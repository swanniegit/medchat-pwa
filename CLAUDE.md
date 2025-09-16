# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MedChat PWA is a WhatsApp clone for a closed group of 1000 medical workers. **Current focus: POC to get core chatting working locally first.** Built as a Progressive Web App with FastAPI backend and vanilla JavaScript frontend, with future DigitalOcean deployment planned.

## Architecture

- **Backend**: FastAPI server with WebSocket support for real-time messaging
  - Single file: `backend/main.py` - Contains FastAPI app, WebSocket connection manager, and all endpoints
  - Uses in-memory storage (perfect for POC/local development)
  - CORS enabled for all origins (development setup)

- **Frontend**: Vanilla JavaScript PWA
  - `frontend/app.js` - Main MedChat class handling WebSocket connections, UI interactions, and messaging
  - `frontend/index.html` - Single-page app with inline CSS styling
  - `frontend/sw.js` - Service worker for PWA functionality and offline support
  - `frontend/manifest.json` - PWA manifest for installation prompts

## Development Commands

### Quick Start
```bash
# For HTTP development (basic setup)
./start.sh

# For HTTPS development (secure setup)
./generate-ssl.sh    # Generate SSL certificates (one-time)
./start.sh           # Start with HTTPS/TLS
```

### Security Setup (Recommended)
```bash
# Generate self-signed SSL certificates for local HTTPS
./generate-ssl.sh

# This creates:
# - backend/cert.pem (SSL certificate)
# - backend/key.pem (private key)

# Then start with HTTPS
./start.sh
# Access at: https://localhost:3000
```

### Manual Backend Setup
```bash
cd backend
# Create virtual environment (first time only)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies (includes security packages)
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Manual Frontend Setup
```bash
cd frontend
python3 -m http.server 3000
```

## POC Development Focus

- **Core Chatting**: Real-time WebSocket messaging between multiple users
- **User Join/Leave**: Simple user presence tracking and notifications
- **Message History**: In-memory message storage (resets on server restart)
- **PWA Features**: Service worker, offline support, install prompts
- **Multi-tab Testing**: Test with multiple browser tabs/windows

## Key Development Notes

- **Real-time Communication**: Uses WebSocket connections (`/ws/{user_id}`) managed by `ConnectionManager` class
- **User Management**: Simple in-memory user tracking with join/leave notifications
- **PWA Features**: Includes service worker, manifest, and install prompts for native app-like experience
- **No Build Process**: Pure vanilla JavaScript - no bundling or compilation required
- **No Testing Framework**: Currently no test suite configured

## Security Implementation (Production-Ready)

### ✅ Implemented Security Features

**🔒 HTTPS/TLS Encryption:**
- Self-signed SSL certificates for local development
- Automatic HTTPS upgrade detection
- WebSocket Secure (WSS) for encrypted real-time communication

**🛡️ Input Validation & Sanitization:**
- Server-side input validation with regex patterns
- HTML/XSS sanitization using bleach library
- Client-side input validation and length limits
- Message content sanitization before broadcast

**🚨 Rate Limiting:**
- WebSocket connection rate limiting (5 connections/minute)
- Message rate limiting (20 messages/minute per user)
- API endpoint rate limiting
- Automatic rate limit violation handling

**🔐 Security Headers:**
- Content Security Policy (CSP)
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Strict-Transport-Security
- X-XSS-Protection
- Referrer-Policy

**📝 Secure Coding Practices:**
- Password hashing with PBKDF2 + salt
- User ID format validation
- JSON parsing error handling
- CORS restrictions to localhost only
- SQL injection prevention (no direct SQL usage)

### 🔄 Additional Security for Production

**Still Needed:**
- **Authentication**: JWT token-based user authentication
- **Authorization**: Role-based access control (RBAC)
- **Session Management**: Secure session handling with Redis
- **Data Encryption**: Database field encryption for sensitive data
- **Audit Logging**: Comprehensive security event logging
- **File Upload Security**: Virus scanning and file type validation
- **HIPAA Compliance**: Medical data protection standards

## Future Production Requirements (1000 Users)

- **Database**: PostgreSQL with encrypted sensitive fields
- **WebSocket Scaling**: Redis pub/sub for multi-instance communication
- **Authentication**: JWT-based user management with MFA
- **File Sharing**: Secure media upload with virus scanning
- **Monitoring**: Security event logging and alerting
- **Backup**: Encrypted database backups
- **DigitalOcean Deployment**: App Platform + managed services with security groups

## API Endpoints

- `GET /` - Health check endpoint
- `GET /health` - Returns active user count
- `GET /users/online` - Lists currently connected users
- `WebSocket /ws/{user_id}` - Real-time messaging connection

## Message Format

WebSocket messages use JSON format with server-side metadata injection (timestamp, message_id).

## Deployment Architecture (DigitalOcean)

Current POC setup is single-instance development. For 1000-user production:

1. **App Platform**: Deploy FastAPI backend with auto-scaling
2. **Managed PostgreSQL**: Database cluster for message/user persistence
3. **Managed Redis**: WebSocket session management and pub/sub
4. **Spaces**: Object storage for file uploads/media
5. **Load Balancer**: Distribute traffic across FastAPI instances
6. **Monitoring**: Built-in DigitalOcean monitoring for performance tracking