#!/data/data/com.termux/files/usr/bin/bash

# Go to the directory where this script is located
cd "$(dirname "$0")"

echo "Pulling latest code..."
git pull

echo "Installing/updating requirements..."
pip install -r requirements.txt --quiet

echo "Starting slut bot..."
python slut_bot.py
