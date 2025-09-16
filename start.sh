#!/bin/bash

echo "🏥 Starting Nightingale-Chat POC..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed"
    exit 1
fi

echo "📦 Setting up Python virtual environment..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing backend dependencies..."
pip install --upgrade -r requirements.txt

echo "🚀 Starting backend server (FastAPI)..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "⏳ Waiting for backend to start..."
sleep 3

echo "🌐 Starting frontend server..."
cd ../frontend

# Check if SSL certificates exist for HTTPS frontend
if [ -f "../backend/cert.pem" ] && [ -f "../backend/key.pem" ]; then
    echo "🔒 Starting frontend with HTTPS"
    # Use Python HTTPS server (requires Python 3.7+)
    python3 -c "
import http.server
import ssl
import socketserver
import os

os.chdir('.')
handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(('', 3000), handler) as httpd:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('../backend/cert.pem', '../backend/key.pem')
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    print('🔒 HTTPS server running at https://localhost:3000')
    httpd.serve_forever()
" &
else
    echo "⚠️  Starting frontend with HTTP (run ./generate-ssl.sh for HTTPS)"
    python3 -m http.server 3000 &
fi
FRONTEND_PID=$!

echo "✅ Nightingale-Chat POC is running!"
echo ""
if [ -f "backend/cert.pem" ] && [ -f "backend/key.pem" ]; then
    echo "🔗 Access the app at: https://localhost:3000"
    echo "📡 Backend API at: https://localhost:8000"
    echo "🔒 Running with HTTPS/TLS encryption"
else
    echo "🔗 Access the app at: http://localhost:3000"
    echo "📡 Backend API at: http://localhost:8000"
    echo "⚠️  Running without HTTPS (run ./generate-ssl.sh for secure setup)"
fi
echo ""
echo "📱 Test with multiple browser tabs/windows"
echo "🏥 Perfect for medical teams!"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for interrupt
trap 'kill $BACKEND_PID $FRONTEND_PID; echo "🛑 Stopped Nightingale-Chat POC"; exit 0' INT
wait