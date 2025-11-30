#!/bin/bash
# Setup security for whatsapp_sessions directory

echo "🔒 Setting up whatsapp_sessions security..."

# Create directory
mkdir -p ./whatsapp_sessions

# Set restrictive permissions (only owner can read/write/execute)
chmod 700 ./whatsapp_sessions

echo "✅ Security setup complete!"
echo "   Directory: ./whatsapp_sessions"
echo "   Permissions: 700 (owner only)"
echo ""
echo "⚠️  IMPORTANT: This directory contains WhatsApp sessions."
echo "   - Do NOT commit to Git"
echo "   - Do NOT include in backups"
echo "   - Sessions will persist until manually deleted"
