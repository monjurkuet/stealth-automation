#!/bin/bash
# install_host.sh

# Target directory for Chrome Native Messaging Hosts
# Linux: ~/.config/google-chrome/NativeMessagingHosts/
# MacOS: ~/Library/Application Support/Google/Chrome/NativeMessagingHosts/

TARGET_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"

mkdir -p "$TARGET_DIR"

# Copy the manifest file
cp host/com.stealth.automation.json "$TARGET_DIR/"

echo "Installed Native Host manifest to $TARGET_DIR"
echo "IMPORTANT: You must edit $TARGET_DIR/com.stealth.automation.json"
echo "and replace <EXTENSION_ID_GOES_HERE> with your actual Chrome Extension ID."
