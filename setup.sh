#!/bin/bash

echo "🔧 Running deployment setup..."

# Update package lists
apt-get update

# Install only essential packages
apt-get install -y \
    portaudio19-dev \
    ffmpeg \
    python3-dev

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install Python packages
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

echo "✅ Setup complete!"