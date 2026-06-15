#!/bin/bash
echo "================================="
echo "   QTDEAL.AI — Starting..."
echo "================================="

pkill -f "python app.py" 2>/dev/null
fuser -k 5001/tcp 2>/dev/null
sleep 1

source venv/bin/activate
python app.py
