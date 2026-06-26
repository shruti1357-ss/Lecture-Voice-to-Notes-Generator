#!/bin/bash
# ============================================
# setup.sh - Deployment Setup Script
# Runs automatically on Streamlit Cloud
# ============================================

# Print colored output for better visibility
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "=========================================="
echo "  🔧 Lecture Voice-to-Notes Generator"
echo "  🚀 Deployment Setup Script"
echo "=========================================="
echo ""

# ============================================
# Step 1: Update System Packages
# ============================================
echo -e "${BLUE}📦 Step 1: Updating system packages...${NC}"
apt-get update
apt-get upgrade -y
echo -e "${GREEN}✅ System packages updated!${NC}"
echo ""

# ============================================
# Step 2: Install Required System Libraries
# ============================================
echo -e "${BLUE}📦 Step 2: Installing system libraries...${NC}"

# Install libraries needed for audio processing
apt-get install -y \
    portaudio19-dev \
    ffmpeg \
    gcc \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    libwebp-dev \
    libxml2-dev \
    libxslt1-dev \
    libssl-dev \
    libffi-dev

echo -e "${GREEN}✅ System libraries installed!${NC}"
echo ""

# ============================================
# Step 3: Upgrade pip and Python tools
# ============================================
echo -e "${BLUE}📦 Step 3: Upgrading pip and Python tools...${NC}"
pip install --upgrade pip setuptools wheel
echo -e "${GREEN}✅ pip upgraded!${NC}"
echo ""

# ============================================
# Step 4: Install Python Dependencies
# ============================================
echo -e "${BLUE}📦 Step 4: Installing Python packages...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✅ Python packages installed!${NC}"
echo ""

# ============================================
# Step 5: Download NLTK Data
# ============================================
echo -e "${BLUE}📦 Step 5: Downloading NLTK data...${NC}"
python -c "
import nltk
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
print('✅ NLTK data downloaded!')
"
echo -e "${GREEN}✅ NLTK data downloaded!${NC}"
echo ""

# ============================================
# Step 6: Create necessary directories
# ============================================
echo -e "${BLUE}📁 Step 6: Creating directories...${NC}"
mkdir -p assets
mkdir -p utils
mkdir -p pages
echo -e "${GREEN}✅ Directories created!${NC}"
echo ""

# ============================================
# Step 7: Set proper permissions
# ============================================
echo -e "${BLUE}🔐 Step 7: Setting permissions...${NC}"
chmod -R 755 .
chmod +x app.py
echo -e "${GREEN}✅ Permissions set!${NC}"
echo ""

# ============================================
# Step 8: Verify installation
# ============================================
echo -e "${BLUE}🔍 Step 8: Verifying installation...${NC}"
python -c "
import sys
import streamlit
import speech_recognition
import openai
import google.generativeai
import nltk
import textstat
print(f'✅ Python version: {sys.version}')
print(f'✅ Streamlit version: {streamlit.__version__}')
print('✅ All modules imported successfully!')
"
echo -e "${GREEN}✅ Verification complete!${NC}"
echo ""

# ============================================
# Completion message
# ============================================
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "📊 Summary:"
echo "  - System packages: ✅ Installed"
echo "  - Python packages: ✅ Installed"
echo "  - NLTK data: ✅ Downloaded"
echo "  - Permissions: ✅ Set"
echo ""
echo "🚀 Starting Streamlit app..."
echo ""