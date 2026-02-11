#!/bin/bash
set -e

echo "Starting Alfred Dev Environment..."

# Check for .env
if [ ! -f "cli/.env" ]; then
    echo "Warning: cli/.env not found! Using defaults (localhost Ollama)."
fi

# Export env vars if .env exists
if [ -f "cli/.env" ]; then
    export $(grep -v '^#' cli/.env | xargs)
fi

# 1. Activate Python Venv
if [ -d "cli/venv" ]; then
    echo "Activating Python venv..."
    source cli/venv/bin/activate
else
    echo "Warning: cli/venv not found. Using system Python."
fi

# 2. Build CLI binary with PyInstaller
echo "Building alfred-cli binary..."
cd cli
pyinstaller --clean --noconfirm alfred-cli.spec
cd ..

# 3. Copy binary into the app bundle
APP_BIN="swift-alfred/Alfred.app/Contents/Resources/bin"
mkdir -p "$APP_BIN"
cp cli/dist/alfred-cli "$APP_BIN/alfred-cli"

# Copy .env into bundle if it exists
if [ -f "cli/.env" ]; then
    cp cli/.env "$APP_BIN/.env"
fi

echo "Binary copied to $APP_BIN"

# 4. Build Swift app
echo "Building Swift app..."
cd swift-alfred
swift build
cd ..

echo ""
echo "Done! To run: open swift-alfred/Alfred.app"
echo "Or run CLI directly: ./cli/dist/alfred-cli --help"
