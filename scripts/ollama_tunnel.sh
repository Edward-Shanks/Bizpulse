#!/bin/bash

# SSH Tunnel Script for Ollama on Mac Studio
# This script creates an SSH tunnel to access Mac Studio Ollama from your laptop

MAC_STUDIO_IP="192.178.90.31"
MAC_STUDIO_USER="rivemain"
LOCAL_PORT="11434"
REMOTE_PORT="11434"

echo "🔗 Ollama SSH Tunnel Manager"
echo "=============================="

# Function to check if tunnel exists
check_tunnel() {
    if lsof -Pi :$LOCAL_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        PID=$(lsof -ti :$LOCAL_PORT)
        echo "✅ SSH tunnel is active (PID: $PID)"
        return 0
    else
        echo "❌ SSH tunnel is not active"
        return 1
    fi
}

# Function to create tunnel
create_tunnel() {
    if check_tunnel; then
        echo "Tunnel already exists. Use 'stop' to close it first."
        return 1
    fi
    
    echo "Creating SSH tunnel to Mac Studio..."
    echo "Connecting to $MAC_STUDIO_USER@$MAC_STUDIO_IP..."
    
    ssh -f -N -L $LOCAL_PORT:localhost:$REMOTE_PORT $MAC_STUDIO_USER@$MAC_STUDIO_IP
    
    if [ $? -eq 0 ]; then
        sleep 2
        if check_tunnel; then
            echo ""
            echo "✅ SSH tunnel created successfully!"
            echo "📍 Ollama accessible at: http://localhost:$LOCAL_PORT"
            echo "🔍 Test with: curl http://localhost:$LOCAL_PORT/api/tags"
            return 0
        else
            echo "❌ Tunnel creation may have failed. Check SSH connection."
            return 1
        fi
    else
        echo "❌ Failed to create SSH tunnel"
        echo "   Make sure you can SSH to $MAC_STUDIO_USER@$MAC_STUDIO_IP"
        return 1
    fi
}

# Function to stop tunnel
stop_tunnel() {
    if ! check_tunnel; then
        echo "No active tunnel to stop."
        return 1
    fi
    
    PID=$(lsof -ti :$LOCAL_PORT)
    echo "Stopping SSH tunnel (PID: $PID)..."
    kill $PID
    
    sleep 1
    if ! check_tunnel; then
        echo "✅ SSH tunnel stopped successfully"
        return 0
    else
        echo "❌ Failed to stop tunnel"
        return 1
    fi
}

# Function to test connection
test_connection() {
    echo "Testing Ollama connection..."
    
    if check_tunnel; then
        RESPONSE=$(curl -s http://localhost:$LOCAL_PORT/api/tags 2>&1)
        if [ $? -eq 0 ]; then
            echo "✅ Connection successful!"
            echo "Available models:"
            echo "$RESPONSE" | grep -o '"name":"[^"]*"' | sed 's/"name":"//;s/"//' | head -5
        else
            echo "❌ Connection failed"
            echo "Response: $RESPONSE"
        fi
    else
        echo "❌ SSH tunnel is not active. Create tunnel first."
    fi
}

# Main script logic
case "$1" in
    start)
        create_tunnel
        ;;
    stop)
        stop_tunnel
        ;;
    status)
        check_tunnel
        ;;
    test)
        test_connection
        ;;
    restart)
        stop_tunnel
        sleep 1
        create_tunnel
        ;;
    *)
        echo "Usage: $0 {start|stop|status|test|restart}"
        echo ""
        echo "Commands:"
        echo "  start   - Create SSH tunnel to Mac Studio"
        echo "  stop    - Stop SSH tunnel"
        echo "  status  - Check if tunnel is active"
        echo "  test    - Test Ollama connection"
        echo "  restart - Restart SSH tunnel"
        exit 1
        ;;
esac

