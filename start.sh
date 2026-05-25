#!/bin/bash
set -e

echo ">>> Starting backend..."
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

echo ">>> Starting frontend..."
cd frontend
npm install
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Backend running at  http://localhost:8000"
echo "✅ Frontend running at http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers."

wait $BACKEND_PID $FRONTEND_PID
