#!/bin/bash
# Alfred installer — removes the macOS quarantine flag and installs to /Applications
# Run this after unzipping Alfred.app.zip:
#
#   unzip Alfred.app.zip
#   bash install.sh
#
# Why this is needed: macOS Gatekeeper blocks apps downloaded from the internet
# that are not signed with a paid Apple Developer ID certificate. This script
# removes that restriction for Alfred.

set -euo pipefail

APP_NAME="Alfred.app"
INSTALL_DIR="/Applications"

bold() { printf '\033[1m%s\033[0m\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
err()  { printf '  \033[31m✗\033[0m %s\n' "$*" >&2; exit 1; }
info() { printf '  \033[34m→\033[0m %s\n' "$*"; }

bold "Alfred Installer"
echo ""

# Find Alfred.app — look next to this script, then in current dir
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -d "${SCRIPT_DIR}/${APP_NAME}" ]; then
    APP_PATH="${SCRIPT_DIR}/${APP_NAME}"
elif [ -d "${PWD}/${APP_NAME}" ]; then
    APP_PATH="${PWD}/${APP_NAME}"
elif [ -d "${SCRIPT_DIR}/swift-alfred/${APP_NAME}" ]; then
    APP_PATH="${SCRIPT_DIR}/swift-alfred/${APP_NAME}"
else
    err "Cannot find ${APP_NAME}. Make sure install.sh is in the same folder as Alfred.app."
fi

info "Found: ${APP_PATH}"

# Remove quarantine flag (the cause of the "damaged" error)
info "Removing macOS quarantine flag..."
xattr -cr "$APP_PATH"
ok "Quarantine flag removed"

# Copy to /Applications
info "Copying to ${INSTALL_DIR}..."
if [ -d "${INSTALL_DIR}/${APP_NAME}" ]; then
    info "Existing Alfred.app found — replacing..."
    rm -rf "${INSTALL_DIR:?}/${APP_NAME}"
fi
cp -R "$APP_PATH" "${INSTALL_DIR}/${APP_NAME}"
ok "Alfred.app installed to ${INSTALL_DIR}"

# Clear quarantine on the installed copy too
xattr -cr "${INSTALL_DIR}/${APP_NAME}" 2>/dev/null || true

echo ""
bold "Done! Alfred is installed."
echo ""
echo "  Launch it:"
echo "    open ${INSTALL_DIR}/${APP_NAME}"
echo ""
echo "  Or double-click Alfred in your Applications folder."
echo ""
