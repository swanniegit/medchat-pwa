#!/bin/bash

echo "🔒 Generating SSL certificates for local HTTPS development..."

# Create backend directory if it doesn't exist
mkdir -p backend

# Generate private key
openssl genrsa -out backend/key.pem 2048

# Generate certificate signing request
openssl req -new -key backend/key.pem -out backend/cert.csr -subj "/C=US/ST=Development/L=Local/O=Nightingale-Chat/OU=Development/CN=localhost"

# Generate self-signed certificate valid for 1 year
openssl x509 -req -days 365 -in backend/cert.csr -signkey backend/key.pem -out backend/cert.pem

# Clean up CSR file
rm backend/cert.csr

echo "✅ SSL certificates generated!"
echo "📁 Files created:"
echo "   - backend/key.pem (private key)"
echo "   - backend/cert.pem (certificate)"
echo ""
echo "⚠️  Note: These are self-signed certificates for development only."
echo "🔒 Your browser will show a security warning - click 'Advanced' and 'Proceed to localhost'"
echo ""
echo "🚀 Now run: ./start.sh"
echo "🌐 Access via: https://localhost:3000"