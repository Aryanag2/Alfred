#!/bin/bash
# Alfred build script — embeds a standalone Python runtime inside Alfred.app
# so users need nothing pre-installed (no Python, no pip, no Homebrew).
#
# Usage:
#   ./build.sh           — full build (downloads Python if needed)
#   ./build.sh --clean   — wipe cached Python and rebuild from scratch
#
# Requirements (developer only, not shipped to users):
#   - Xcode command-line tools  (xcode-select --install)
#   - Swift / swift build
#   - Internet access for first run (downloads ~45 MB standalone Python)

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
PYTHON_VERSION="3.13.5"
PYTHON_BUILD_DATE="20250612"
PYTHON_ARCH="aarch64-apple-darwin"   # arm64 Mac (M1/M2/M3/M4)
# For Intel Macs use: x86_64-apple-darwin

STANDALONE_URL="https://github.com/indygreg/python-build-standalone/releases/download/${PYTHON_BUILD_DATE}/cpython-${PYTHON_VERSION}+${PYTHON_BUILD_DATE}-${PYTHON_ARCH}-install_only_stripped.tar.gz"

APP_BUNDLE="swift-alfred/Alfred.app"
RESOURCES="${APP_BUNDLE}/Contents/MacOS"
PYTHON_DEST="${APP_BUNDLE}/Contents/Resources/python"
CACHE_DIR=".cache/python-standalone"
REQUIREMENTS="cli/requirements.txt"
SCRIPT_SRC="cli/alfred.py"
ENV_SRC="cli/.env"

# ── Helpers ───────────────────────────────────────────────────────────────────
bold() { printf '\033[1m%s\033[0m\n' "$*"; }
info() { printf '  \033[34m→\033[0m %s\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
err()  { printf '  \033[31m✗\033[0m %s\n' "$*" >&2; exit 1; }

# ── Flags ─────────────────────────────────────────────────────────────────────
CLEAN=false
for arg in "$@"; do
    [[ "$arg" == "--clean" ]] && CLEAN=true
done

if $CLEAN; then
    bold "Cleaning cached Python..."
    rm -rf "$CACHE_DIR"
    rm -rf "$PYTHON_DEST"
fi

# ── Step 0: sanity checks ─────────────────────────────────────────────────────
bold "Step 0 — Checking prerequisites..."
command -v swift >/dev/null 2>&1 || err "swift not found. Install Xcode command-line tools: xcode-select --install"
ok "swift found"

# ── Step 1: download standalone Python (cached) ───────────────────────────────
bold "Step 1 — Standalone Python ${PYTHON_VERSION}..."
if [ -d "${CACHE_DIR}/bin/python3" ] || [ -f "${CACHE_DIR}/bin/python3" ]; then
    ok "Using cached Python at ${CACHE_DIR}"
else
    info "Downloading from python-build-standalone..."
    mkdir -p "$CACHE_DIR"
    TARBALL="${CACHE_DIR}/python.tar.gz"
    curl -L --progress-bar "$STANDALONE_URL" -o "$TARBALL"
    info "Extracting..."
    tar xzf "$TARBALL" -C "$CACHE_DIR" --strip-components=1
    rm "$TARBALL"
    ok "Python ${PYTHON_VERSION} cached at ${CACHE_DIR}"
fi

# ── Step 2: embed Python into the .app bundle ─────────────────────────────────
bold "Step 2 — Embedding Python into Alfred.app..."
mkdir -p "${APP_BUNDLE}/Contents/Resources"
rm -rf "$PYTHON_DEST"
cp -R "$CACHE_DIR" "$PYTHON_DEST"
ok "Python runtime copied to ${PYTHON_DEST}"

# ── Step 3: create venv inside the bundle and install deps ────────────────────
bold "Step 3 — Installing Python dependencies..."
EMBEDDED_PYTHON="${PYTHON_DEST}/bin/python3"
VENV="${PYTHON_DEST}/venv"

info "Creating venv at ${VENV}..."
"$EMBEDDED_PYTHON" -m venv "$VENV"

info "Installing requirements from ${REQUIREMENTS}..."
"${VENV}/bin/pip" install --quiet --no-cache-dir -r "$REQUIREMENTS"
ok "Dependencies installed"

# ── Step 4: copy Alfred CLI into the bundle ───────────────────────────────────
bold "Step 4 — Copying Alfred CLI..."
cp "$SCRIPT_SRC" "${APP_BUNDLE}/Contents/Resources/alfred.py"
ok "alfred.py copied"

if [ -f "$ENV_SRC" ]; then
    cp "$ENV_SRC" "${APP_BUNDLE}/Contents/Resources/.env"
    ok ".env copied"
else
    info "No cli/.env found — skipping (app will use defaults)"
fi

# Copy agent prompt files
if [ -d "cli/agents" ]; then
    mkdir -p "${APP_BUNDLE}/Contents/Resources/agents"
    cp cli/agents/*.md "${APP_BUNDLE}/Contents/Resources/agents/"
    ok "Agent prompts copied ($(ls cli/agents/*.md 2>/dev/null | wc -l | tr -d ' ') files)"
else
    err "cli/agents/ directory not found — agent prompts are required"
fi

# ── Step 5: trim bundle size ──────────────────────────────────────────────────
bold "Step 5 — Trimming bundle..."
SITE_PKG="${VENV}/lib/python3.13/site-packages"

# Remove pip (not needed at runtime)
rm -rf "${VENV}/lib/python3.13/site-packages/pip"
rm -rf "${VENV}/lib/python3.13/site-packages/setuptools"

# Remove __pycache__ and .pyc files
find "$PYTHON_DEST" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find "$PYTHON_DEST" -name "*.pyc" -delete 2>/dev/null || true

# Remove test directories inside packages
find "$SITE_PKG" -type d -name tests -maxdepth 3 -exec rm -rf {} + 2>/dev/null || true
find "$SITE_PKG" -type d -name test -maxdepth 3 -exec rm -rf {} + 2>/dev/null || true

ok "Bundle trimmed"

# ── Step 6: build Swift app ───────────────────────────────────────────────────
bold "Step 6 — Building Swift app..."
(cd swift-alfred && swift build -c release 2>&1) || err "Swift build failed"
ok "Swift app built"

# ── Step 7: copy Swift binary into .app ──────────────────────────────────────
bold "Step 7 — Copying Swift binary into Alfred.app..."
mkdir -p "${APP_BUNDLE}/Contents/MacOS"
cp "swift-alfred/.build/release/Alfred" "${APP_BUNDLE}/Contents/MacOS/Alfred"
chmod +x "${APP_BUNDLE}/Contents/MacOS/Alfred"
ok "Swift binary placed at ${APP_BUNDLE}/Contents/MacOS/Alfred"

# ── Step 8: sign the app (ad-hoc) ────────────────────────────────────────────
# Ad-hoc signing (-s -) is free and requires no Apple Developer account.
# It prevents the "app is damaged" Gatekeeper error on the build machine.
# For distribution to other Macs, a full Developer ID signature is needed.
bold "Step 8 — Ad-hoc code signing..."
# Sign all bundled .dylib and .so files first (inside-out order required)
find "${APP_BUNDLE}" \( -name "*.so" -o -name "*.dylib" \) | while read -r f; do
    codesign --force --sign - "$f" 2>/dev/null || true
done
# Sign the main binary
codesign --force --sign - "${APP_BUNDLE}/Contents/MacOS/Alfred" 2>/dev/null || true
# Sign the whole bundle
codesign --force --deep --sign - "${APP_BUNDLE}" 2>/dev/null \
    && ok "App signed (ad-hoc)" \
    || info "codesign not available — skipping (run xcode-select --install)"

# Strip quarantine flag so macOS doesn't block the app on first launch
xattr -cr "${APP_BUNDLE}" 2>/dev/null || true
ok "Quarantine flag cleared"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
bold "Build complete!"
echo ""
echo "  App bundle: ${APP_BUNDLE}"
echo ""
echo "  To run:"
echo "    open ${APP_BUNDLE}"
echo ""
echo "  To distribute, drag Alfred.app to /Applications or zip it:"
echo "    zip -r Alfred.zip ${APP_BUNDLE}"
echo ""
echo "  Note: ad-hoc signing works on this machine. To distribute to other Macs"
echo "  without a Gatekeeper prompt, sign with a Developer ID certificate:"
echo "    codesign --force --deep --sign \"Developer ID Application: Name (TEAMID)\" ${APP_BUNDLE}"
echo "    xcrun notarytool submit Alfred.zip --apple-id you@example.com --wait"
echo ""
