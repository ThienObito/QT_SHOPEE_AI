#!/bin/bash

echo "================================="
echo "QT_SHOPEE STARTING..."
echo "================================="

# Kill process cũ nếu có

pkill -f "python app.py" 2>/dev/null

# Kill port 5001 nếu đang bị chiếm

fuser -k 5001/tcp 2>/dev/null

sleep 1

# Activate virtual env

source venv/bin/activate

# Start Flask

python app.py
