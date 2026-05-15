#!/bin/sh

# Arrancar el Backend Python (FastAPI) en el puerto 8000
echo "🚀 Iniciando Backend Python en el puerto 8000..."
cd /app/backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &

# Arrancar el Frontend Next.js en el puerto 3000
echo "🌐 Iniciando Frontend Next.js en el puerto 3000..."
cd /app/frontend && node server.js
