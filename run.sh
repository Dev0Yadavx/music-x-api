#!/data/data/com.termux/files/usr/bin/bash
cd ~/ytmusic-server

# Check if requests library is installed
python -c "import requests" 2>/dev/null || pip install requests

echo "[*] Starting YT Music Server on port 8000..."
python main.py > server.log 2>&1 &
SERVER_PID=$!

sleep 3

# Run automated tests
python test_endpoints.py

echo "[*] Server is running in background (PID: $SERVER_PID)"
echo "[*] Open in browser: http://127.0.0.1:8000"
echo "[*] To view logs: tail -f server.log"
echo "[*] To stop server: kill $SERVER_PID"
