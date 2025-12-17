#!/bin/bash
# Integrate ClientManager into PhazeVPN server

SERVER_FILE="phazevpn-server-production.py"

echo "🔧 Integrating ClientManager into server..."

# Check if file exists
if [ ! -f "$SERVER_FILE" ]; then
    echo "❌ Server file not found: $SERVER_FILE"
    exit 1
fi

# Add ClientManager import if not present
if ! grep -q "from client_manager import ClientManager" "$SERVER_FILE"; then
    echo "➕ Adding ClientManager import..."
    sed -i '/^from zero_knowledge import/a from client_manager import ClientManager' "$SERVER_FILE"
fi

# Initialize ClientManager in __init__
if ! grep -q "self.client_manager = ClientManager()" "$SERVER_FILE"; then
    echo "➕ Adding ClientManager initialization..."
    sed -i '/self\.zero_knowledge = ZeroKnowledgeServer/a \        self.client_manager = ClientManager()' "$SERVER_FILE"
fi

# Update _load_users to use ClientManager
if grep -q "def _load_users" "$SERVER_FILE"; then
    echo "📝 Server already has user loading system"
    echo "   Update server to use ClientManager for authentication"
else
    echo "⚠️  Server doesn't have _load_users method"
    echo "   ClientManager will be used directly"
fi

echo "✅ Integration complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Update server authentication to use ClientManager"
echo "   2. Replace self.users with self.client_manager.users"
echo "   3. Test user authentication"

