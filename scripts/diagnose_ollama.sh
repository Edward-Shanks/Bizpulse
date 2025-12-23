#!/bin/bash
echo "=========================================="
echo "Ollama Diagnostic Script"
echo "=========================================="
echo ""

echo "1. Checking Ollama processes:"
ps aux | grep ollama | grep -v grep
if [ $? -ne 0 ]; then
    echo "   ✅ No Ollama processes running"
else
    echo "   ⚠️  Ollama processes found (see above)"
fi
echo ""

echo "2. Checking port 11434:"
lsof -i :11434 2>/dev/null
if [ $? -ne 0 ]; then
    echo "   ⚠️  Nothing listening on port 11434"
else
    echo "   ✅ Port 11434 is in use"
fi
echo ""

echo "3. Testing API endpoint:"
curl -s -m 5 http://localhost:11434/api/tags > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ API is responding"
    echo "   Response:"
    curl -s http://localhost:11434/api/tags | head -10
else
    echo "   ❌ API is NOT responding"
    echo "   Trying verbose curl:"
    curl -v http://localhost:11434/api/tags 2>&1 | head -15
fi
echo ""

echo "4. Checking Ollama version:"
ollama --version 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ Ollama CLI is working"
else
    echo "   ❌ Ollama CLI not found"
fi
echo ""

echo "5. Checking models:"
ollama list 2>/dev/null | head -5
echo ""

echo "6. Testing direct model access:"
echo "   (This may take a moment...)"
timeout 10 ollama run qwen2.5:32b-instruct "say hello" 2>&1 | head -3
echo ""

echo "7. Checking environment variables:"
env | grep OLLAMA
if [ $? -ne 0 ]; then
    echo "   ℹ️  No OLLAMA environment variables set"
fi
echo ""

echo "8. Checking Launch Agents:"
ls ~/Library/LaunchAgents/ 2>/dev/null | grep -i ollama
if [ $? -ne 0 ]; then
    echo "   ✅ No Ollama Launch Agents found"
else
    echo "   ⚠️  Ollama Launch Agents found (may auto-start)"
fi
echo ""

echo "=========================================="
echo "Diagnostic Complete"
echo "=========================================="

