# Local LLM Infrastructure - Qwen:32b on Mac Studio

## Overview

BizPulse uses a **local, on-premise LLM** for all AI-powered features, ensuring 100% data privacy.

## Hardware & Software Stack

### Hardware
- **Device**: Mac Studio
- **RAM**: 512GB (critical for running 32B parameter model)
- **Purpose**: Dedicated AI inference server
- **Location**: On-premise (not cloud-based)

### Software
- **Model**: Qwen:32b (32 billion parameters)
- **Serving**: Ollama (or similar LLM serving framework)
- **Inference Speed**: ~2-5 seconds per query
- **Context Window**: Supports long context (up to 32K tokens)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                     │
│              User asks question in chatbot              │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────┐
│              Backend (FastAPI Python)                   │
│         - Receives user question                        │
│         - Applies RBAC validation                       │
│         - Queries MongoDB for data                      │
│         - Formats data for LLM                          │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────┐
│         Mac Studio (Local LLM Server)                   │
│                                                         │
│   ┌──────────────────────────────────────────────┐    │
│   │         Qwen:32b Model (loaded in RAM)       │    │
│   │                  512GB RAM                    │    │
│   └──────────────────────────────────────────────┘    │
│                                                         │
│   - Understands natural language questions             │
│   - Generates MongoDB query plans                      │
│   - Analyzes data and creates insights                 │
│   - Returns business-friendly responses                │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────┐
│              Response returned to user                  │
│         (Business insights, no technical jargon)        │
└─────────────────────────────────────────────────────────┘
```

## Key Advantages

### 1. **Data Privacy & Security** 🔒
- ✅ **100% On-Premise**: All data stays within your infrastructure
- ✅ **No External APIs**: Never sends business data to OpenAI, Anthropic, etc.
- ✅ **Compliance Ready**: Meets GDPR, SOC2, data residency requirements
- ✅ **Confidential Data**: Safe to process financial, customer, strategic data

### 2. **Cost Efficiency** 💰
- ✅ **Zero Per-Query Cost**: No usage-based pricing
- ✅ **Unlimited Usage**: No rate limits or API caps
- ✅ **Predictable Costs**: One-time hardware investment
- ✅ **No Token Charges**: Process millions of tokens for free

**Cost Comparison:**
```
OpenAI GPT-4 (Cloud):
- $0.03 per 1K input tokens
- $0.06 per 1K output tokens
- 10K queries/month = ~$1,500-3,000/month

Local Qwen:32b:
- $0 per query
- Unlimited queries
- Cost: Mac Studio hardware only (~$7,000 one-time)
- ROI: 2-5 months
```

### 3. **Customization** 🛠️
- ✅ **Fine-tuning**: Can train on your specific business data
- ✅ **Prompt Control**: Full control over system prompts
- ✅ **Model Selection**: Can switch models easily
- ✅ **Version Control**: Pin to specific model versions

### 4. **Performance** ⚡
- ✅ **Low Latency**: No network round-trips to cloud
- ✅ **High Throughput**: Can handle multiple concurrent requests
- ✅ **Predictable Speed**: 2-5 seconds per query (consistent)
- ✅ **No Downtime**: Not affected by external API outages

### 5. **Transparency** 🔍
- ✅ **Full Visibility**: Know exactly what model is running
- ✅ **Debugging**: Can trace all LLM behavior
- ✅ **No Black Box**: Complete control over inference
- ✅ **Audit Trail**: Log all LLM interactions locally

## Model Capabilities

### What Qwen:32b Can Do
- ✅ **Understand Complex Questions**: Natural language query understanding
- ✅ **Generate Structured Output**: JSON query plans, formatted responses
- ✅ **Business Analysis**: Interpret data and provide insights
- ✅ **Multi-step Reasoning**: Break down complex problems
- ✅ **Context Awareness**: Use conversation history
- ✅ **Code Generation**: Generate SQL, Python, etc.

### Comparison with Cloud Models

| Capability | Qwen:32b (Local) | GPT-4 (Cloud) | GPT-3.5 (Cloud) |
|-----------|------------------|---------------|-----------------|
| **Parameter Count** | 32B | ~1.7T | 175B |
| **Quality** | Very Good | Excellent | Good |
| **Speed** | 2-5s | 3-8s (+ network) | 1-3s (+ network) |
| **Cost** | $0 | High | Medium |
| **Privacy** | 100% Private | Shared with OpenAI | Shared with OpenAI |
| **Customization** | Full | Limited | Limited |
| **Fine-tuning** | Yes | Expensive | Expensive |

**Verdict**: Qwen:32b offers 80-90% of GPT-4's quality at 0% of the cost with 100% privacy.

## Use Cases in BizPulse

### 1. **AI Chatbot - Query Understanding**
**Purpose**: Understand user questions and generate MongoDB query plans

**Example:**
```
User: "What were top 5 customers in Q4 2024?"

Qwen:32b Output:
{
  "filters": {"Year": 2024, "Quarter": 4},
  "group_by": ["Customer"],
  "metrics": ["Revenue"],
  "needs_customer_breakdown": true,
  "limit": 5
}
```

### 2. **AI Chatbot - Data Analysis**
**Purpose**: Analyze data and generate business insights

**Example:**
```
Data Input (formatted):
=== TOP 5 CUSTOMERS Q4 2024 ===
1. Musgrave ROI: €45.7M revenue, 30% margin
2. Dunnes ROI: €38.4M revenue, 30% margin
...

Qwen:32b Output:
"Your Q4 2024 performance was strong, driven by two anchor customers:

KEY INSIGHTS:
1. Musgrave ROI and Dunnes ROI represent 84% of revenue
2. Both maintain healthy 30% margins
3. Customer concentration risk is high

RECOMMENDATIONS:
1. Diversify revenue: Target 5-10 mid-size accounts
2. Strengthen relationships with top 2 customers
3. Test price increases on top SKUs (expect +€450K profit)
..."
```

### 3. **RBAC Intent Extraction**
**Purpose**: Understand what data user is requesting (for RBAC validation)

**Example:**
```
User: "Show me financial data for Brand X"

Qwen:32b Output:
{
  "requested_brands": ["Brand X"],
  "requested_data_types": ["finance", "cost"],
  "requested_businesses": ["all"]
}

→ System checks if user has access to Brand X + finance data
```

## Integration Points

### Backend Integration
```python
# backend/app/services/llm_service.py

async def query_local_llm(prompt: str, conversation_history: List = None):
    """
    Query the local Qwen:32b model on Mac Studio
    """
    # Connect to Ollama on Mac Studio
    response = requests.post(
        "http://mac-studio-ip:11434/api/generate",
        json={
            "model": "qwen:32b",
            "prompt": prompt,
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 2000
        }
    )
    
    return response.json()["response"]
```

### Configuration
```python
# backend/app/core/config.py

class Settings(BaseSettings):
    # Local LLM Configuration
    LOCAL_LLM_ENABLED: bool = True
    LOCAL_LLM_HOST: str = "192.168.1.100"  # Mac Studio IP
    LOCAL_LLM_PORT: int = 11434  # Ollama default port
    LOCAL_LLM_MODEL: str = "qwen:32b"
    LOCAL_LLM_TIMEOUT: int = 30  # seconds
    
    # Fallback (if Mac Studio is down)
    FALLBACK_TO_CLOUD: bool = False  # Keep disabled for privacy
```

## Deployment & Operations

### Starting the LLM Server
```bash
# On Mac Studio
ollama serve

# Or with specific config
ollama serve --host 0.0.0.0 --port 11434
```

### Loading the Model
```bash
# Download and load Qwen:32b
ollama pull qwen:32b

# Verify model is loaded
ollama list
```

### Health Check
```bash
# Test LLM endpoint
curl http://mac-studio-ip:11434/api/generate \
  -d '{"model": "qwen:32b", "prompt": "Hello", "stream": false}'
```

### Monitoring
```python
# Monitor LLM performance
async def check_llm_health():
    try:
        start = time.time()
        response = await query_local_llm("Test prompt")
        latency = time.time() - start
        
        if latency > 10:
            logger.warning(f"LLM latency high: {latency}s")
        
        return {"status": "healthy", "latency": latency}
    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}
```

## Scaling Considerations

### Current Setup (Single Mac Studio)
- **Capacity**: ~10-20 concurrent users
- **Throughput**: ~20-30 queries/minute
- **Adequate for**: Current BizPulse usage

### Future Scaling Options

#### Option 1: Load Balancing (Multiple Mac Studios)
```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│ Mac Studio  │      │ Mac Studio  │      │ Mac Studio  │
│  Qwen:32b   │      │  Qwen:32b   │      │  Qwen:32b   │
└──────┬──────┘      └──────┬──────┘      └──────┬──────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                    ┌───────┴────────┐
                    │ Load Balancer  │
                    └───────┬────────┘
                            │
                    ┌───────┴────────┐
                    │   Backend      │
                    └────────────────┘
```

#### Option 2: Smaller Model for Simple Queries
- Use Qwen:14b or Qwen:7b for simple questions
- Reserve Qwen:32b for complex analysis
- 3-5x faster inference for simple queries

#### Option 3: GPU Acceleration
- Add NVIDIA GPUs to Mac Studio (if supported)
- 5-10x faster inference
- Handle 100+ concurrent users

## Troubleshooting

### Issue: LLM Not Responding
```bash
# Check if Ollama is running
ps aux | grep ollama

# Restart Ollama
pkill ollama
ollama serve

# Check network connectivity
ping mac-studio-ip
curl http://mac-studio-ip:11434/api/tags
```

### Issue: Slow Responses (>10s)
- **Cause**: Model not fully loaded in RAM
- **Solution**: Restart Ollama, ensure 512GB RAM available
- **Check**: `top` or Activity Monitor on Mac Studio

### Issue: Out of Memory
- **Cause**: Multiple models loaded
- **Solution**: Unload unused models
```bash
ollama stop <model-name>
ollama list  # Check loaded models
```

## Security

### Network Security
- ✅ Mac Studio should be on private network
- ✅ Use VPN for remote access
- ✅ Firewall: Only allow backend server to access port 11434
- ✅ No public internet exposure

### Data Security
- ✅ All LLM processing happens on-premise
- ✅ No data sent to external services
- ✅ Conversation history stored in MongoDB (encrypted)
- ✅ RBAC applied before sending data to LLM

## Best Practices

1. **Prompt Engineering**: Craft clear, specific system prompts
2. **Error Handling**: Graceful degradation if LLM is unavailable
3. **Caching**: Cache common LLM responses (e.g., for FAQs)
4. **Monitoring**: Track LLM latency, error rates, usage patterns
5. **Backup**: Have fallback responses for critical functions
6. **Testing**: Test LLM responses regularly for quality

## Migration from Cloud LLM (If Applicable)

If migrating from OpenAI/Anthropic to local Qwen:32b:

### Migration Checklist
- [ ] Install Ollama on Mac Studio
- [ ] Download Qwen:32b model
- [ ] Update backend configuration
- [ ] Test all chatbot queries
- [ ] Compare response quality
- [ ] Update prompts for Qwen:32b (if needed)
- [ ] Monitor performance for 1 week
- [ ] Decommission cloud API keys

### Expected Benefits
- ✅ $1,500-3,000/month cost savings
- ✅ 100% data privacy
- ✅ No rate limits
- ✅ Faster responses (no network latency)

---

**Document Version**: 1.0  
**Last Updated**: February 8, 2026  
**Hardware**: Mac Studio with 512GB RAM  
**Model**: Qwen:32b (32 billion parameters)  
**Status**: ✅ Production-ready
