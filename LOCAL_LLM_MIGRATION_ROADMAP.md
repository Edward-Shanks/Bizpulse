# Local LLM Migration Roadmap: Perplexity API → Ollama + Vector DB

## Executive Summary

This document outlines a comprehensive migration strategy from Perplexity API to a local LLM infrastructure using Ollama, integrated with a Vector Database for enhanced context retrieval. The goal is to eliminate token costs for 1000+ users while maintaining or improving response quality.

---

## Table of Contents

1. [Current Architecture Analysis](#current-architecture-analysis)
2. [Target Architecture](#target-architecture)
3. [Migration Phases](#migration-phases)
4. [Technical Implementation Details](#technical-implementation-details)
5. [Deployment Strategy](#deployment-strategy)
6. [Performance & Scalability](#performance--scalability)
7. [Cost Analysis](#cost-analysis)
8. [Risk Mitigation](#risk-mitigation)

---

## Current Architecture Analysis

### 1.1 Current System Structure

#### **AI Service Layer** (`backend/app/utils/ai_service.py`)
- **Current Implementation**: Perplexity API integration
- **Model**: `sonar-pro` (cloud-based)
- **API Endpoint**: `https://api.perplexity.ai/chat/completions`
- **Authentication**: Bearer token (PERPLEXITY_API_KEY)
- **Features**:
  - Async request handling with `asyncio.to_thread`
  - Retry logic with exponential backoff (3 attempts)
  - Custom system message support
  - Conversation history management
  - Error handling and timeout management (60s timeout)

#### **Insights Service** (`backend/app/services/insights_service.py`)
- **Function**: `query_perplexity()` called for AI responses
- **Context Building**: 
  - Comprehensive data context from MongoDB
  - System prompts with business rules
  - User prompts with data context
  - Conversation history
- **Response Processing**: 
  - Validation for refusal phrases
  - Pivot table generation
  - Dynamic recommendations

#### **Data Context Generation** (`backend/app/utils/data_context.py`)
- **Function**: `get_comprehensive_data_context()`
- **Data Sources**: MongoDB `business_data` collection
- **Output**: Formatted text context with:
  - Overall totals
  - Quarterly breakdowns
  - Yearly breakdowns
  - Brand/Business/Category/Channel/Customer performance
  - Multi-dimensional breakdowns

#### **Query Building** (`backend/app/utils/query_builder.py`)
- **Function**: `parse_query_from_natural_language()`
- **Capabilities**:
  - Natural language to MongoDB query conversion
  - Intent extraction (metric, operation, group_by)
  - Dimension extraction (Business, Brand, Category, etc.)
  - Filter building and merging

### 1.2 Current Data Flow

```
User Query
    ↓
Frontend (InsightModal/AIAssistant)
    ↓
Backend API Endpoint
    ↓
InsightsService.process_chat()
    ↓
Query Builder → MongoDB Query
    ↓
Data Context Generator → Formatted Context String
    ↓
AI Service (query_perplexity) → Perplexity API
    ↓
AI Response → Frontend
```

### 1.3 Current Limitations

1. **Token Costs**: 
   - Perplexity API charges per token (input + output)
   - With 1000+ users, costs scale linearly
   - Estimated cost: $0.001-0.01 per query (varies by model)

2. **API Rate Limits**: 
   - Perplexity has rate limits
   - May cause delays during peak usage

3. **Data Privacy**: 
   - Business data sent to external API
   - Potential compliance concerns

4. **Latency**: 
   - Network round-trip to Perplexity servers
   - Dependent on internet connectivity

5. **Context Window**: 
   - Limited by API model's context window
   - Large data contexts may be truncated

---

## Target Architecture

### 2.1 New System Structure

#### **Local LLM Service** (`backend/app/utils/llm_service.py`)
- **Implementation**: Ollama API client
- **Model Options**: 
  - `llama3.1:70b` (recommended for quality)
  - `llama3.1:8b` (faster, lower quality)
  - `mistral:7b` (balanced)
  - `qwen2.5:72b` (excellent for business analytics)
- **Features**:
  - Local inference (no external API calls)
  - Streaming responses
  - Custom system prompts
  - Conversation history management
  - Context window management

#### **Vector Database Service** (`backend/app/utils/vector_service.py`)
- **Implementation**: 
  - **Option 1**: ChromaDB (lightweight, Python-native)
  - **Option 2**: Qdrant (high performance, scalable)
  - **Option 3**: Weaviate (enterprise-grade)
- **Purpose**: 
  - Store embeddings of historical queries and responses
  - Store embeddings of data context summaries
  - Semantic search for similar queries
  - Context retrieval for better answers

#### **Embedding Service** (`backend/app/utils/embedding_service.py`)
- **Implementation**: 
  - **Option 1**: `ollama embeddings` (local, free)
  - **Option 2**: `sentence-transformers` (local, fast)
  - **Option 3**: `all-MiniLM-L6-v2` (lightweight, 80MB)
- **Purpose**: 
  - Generate embeddings for queries
  - Generate embeddings for data context
  - Generate embeddings for historical responses

#### **Enhanced Data Context** (`backend/app/utils/data_context.py`)
- **Enhancements**:
  - Context summarization for vector storage
  - Context chunking for large datasets
  - Metadata tagging (dimensions, metrics, time ranges)
  - Relevance scoring

### 2.2 New Data Flow

```
User Query
    ↓
Frontend (InsightModal/AIAssistant)
    ↓
Backend API Endpoint
    ↓
InsightsService.process_chat()
    ↓
Query Builder → MongoDB Query
    ↓
Data Context Generator → Formatted Context String
    ↓
Vector DB Search → Similar Historical Queries/Contexts
    ↓
Context Enrichment → Merge Current + Historical Context
    ↓
LLM Service (Ollama) → Local LLM Inference
    ↓
Response Processing → Store in Vector DB
    ↓
AI Response → Frontend
```

### 2.3 Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
│              InsightModal / AIAssistant                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend Server                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         InsightsService.process_chat()                │  │
│  └───────────────┬──────────────────────────────────────┘  │
│                  │                                          │
│  ┌───────────────▼───────────────┐                         │
│  │    Query Builder              │                         │
│  │  (Natural Language → MongoDB) │                         │
│  └───────────────┬───────────────┘                         │
│                  │                                          │
│  ┌───────────────▼───────────────┐                         │
│  │   Data Context Generator      │                         │
│  │  (MongoDB → Formatted Text)   │                         │
│  └───────────────┬───────────────┘                         │
│                  │                                          │
│  ┌───────────────▼───────────────┐                         │
│  │    Embedding Service          │                         │
│  │  (Text → Vector Embeddings)   │                         │
│  └───────────────┬───────────────┘                         │
│                  │                                          │
│  ┌───────────────▼───────────────┐                         │
│  │    Vector DB Service          │                         │
│  │  (Semantic Search & Storage)  │                         │
│  └───────────────┬───────────────┘                         │
│                  │                                          │
│  ┌───────────────▼───────────────┐                         │
│  │    LLM Service (Ollama)       │                         │
│  │  (Local Inference)             │                         │
│  └───────────────────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   MongoDB    │ │  Vector DB   │ │   Ollama     │
│ (Main Data)  │ │ (Embeddings) │ │ (Local LLM)  │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## Migration Phases

### Phase 1: Infrastructure Setup (Week 1-2)

#### **1.1 Ollama Installation & Configuration**

**Tasks:**
- [ ] Install Ollama on MacBook (512GB RAM system)
- [ ] Download recommended models:
  - `ollama pull llama3.1:70b` (primary model)
  - `ollama pull llama3.1:8b` (fallback for speed)
  - `ollama pull mistral:7b` (alternative)
- [ ] Configure Ollama server:
  - Set `OLLAMA_HOST` environment variable
  - Configure port (default: 11434)
  - Set `OLLAMA_NUM_PARALLEL` for concurrent requests
  - Configure `OLLAMA_MAX_LOADED_MODELS` for memory management
- [ ] Test Ollama API endpoints:
  - `/api/generate` (completion)
  - `/api/chat` (chat completion)
  - `/api/embeddings` (embeddings)
- [ ] Benchmark model performance:
  - Response time
  - Token generation speed
  - Memory usage
  - Concurrent request handling

**Configuration Example:**
```bash
# .env file
OLLAMA_HOST=0.0.0.0
OLLAMA_PORT=11434
OLLAMA_NUM_PARALLEL=4
OLLAMA_MAX_LOADED_MODELS=2
OLLAMA_MODEL=llama3.1:70b
```

#### **1.2 Vector Database Setup**

**Tasks:**
- [ ] Choose vector database (recommend ChromaDB for simplicity)
- [ ] Install ChromaDB:
  ```bash
  pip install chromadb
  ```
- [ ] Initialize ChromaDB server:
  - Create persistent storage directory
  - Configure collection for query embeddings
  - Configure collection for context embeddings
  - Configure collection for response embeddings
- [ ] Set up embedding model:
  - Install `sentence-transformers`
  - Load `all-MiniLM-L6-v2` model (or use Ollama embeddings)
- [ ] Create database schema:
  - Collection: `query_embeddings` (user queries)
  - Collection: `context_embeddings` (data context summaries)
  - Collection: `response_embeddings` (AI responses)
  - Metadata fields: timestamp, user_id, session_id, dimensions, metrics

**ChromaDB Setup:**
```python
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(anonymized_telemetry=False)
)

# Create collections
query_collection = client.create_collection(
    name="query_embeddings",
    metadata={"hnsw:space": "cosine"}
)

context_collection = client.create_collection(
    name="context_embeddings",
    metadata={"hnsw:space": "cosine"}
)
```

#### **1.3 Development Environment Setup**

**Tasks:**
- [ ] Create new virtual environment for testing
- [ ] Install dependencies:
  ```bash
  pip install ollama chromadb sentence-transformers
  ```
- [ ] Create configuration file for local LLM settings
- [ ] Set up environment variables
- [ ] Create test scripts for Ollama connectivity

---

### Phase 2: Core Service Implementation (Week 3-4)

#### **2.1 LLM Service Implementation**

**File**: `backend/app/utils/llm_service.py`

**Tasks:**
- [ ] Create `query_ollama()` function to replace `query_perplexity()`
- [ ] Implement async Ollama API client
- [ ] Add streaming support for real-time responses
- [ ] Implement conversation history management
- [ ] Add system prompt customization
- [ ] Implement context window management (chunking if needed)
- [ ] Add retry logic and error handling
- [ ] Implement response caching for identical queries
- [ ] Add response time logging
- [ ] Create fallback mechanism (switch to smaller model if 70b fails)

**Implementation Structure:**
```python
async def query_ollama(
    prompt: str,
    conversation_history: Optional[List[Dict]] = None,
    custom_system_message: Optional[str] = None,
    model: str = "llama3.1:70b",
    stream: bool = False,
    temperature: float = 0.7,
    max_tokens: int = 4000
) -> str:
    """
    Query local Ollama LLM for AI responses
    
    Args:
        prompt: User prompt/question
        conversation_history: Previous conversation messages
        custom_system_message: Optional custom system message
        model: Ollama model name
        stream: Whether to stream response
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens to generate
    """
    # Implementation here
```

#### **2.2 Embedding Service Implementation**

**File**: `backend/app/utils/embedding_service.py`

**Tasks:**
- [ ] Create `generate_embedding()` function
- [ ] Implement embedding generation using sentence-transformers
- [ ] Add batch embedding generation for efficiency
- [ ] Implement embedding caching
- [ ] Add embedding normalization
- [ ] Create embedding comparison utilities

**Implementation Structure:**
```python
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        # Implementation here
    
    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        # Implementation here
```

#### **2.3 Vector Database Service Implementation**

**File**: `backend/app/utils/vector_service.py`

**Tasks:**
- [ ] Create `VectorDBService` class
- [ ] Implement query embedding storage
- [ ] Implement context embedding storage
- [ ] Implement response embedding storage
- [ ] Add semantic search functionality
- [ ] Implement similarity search with metadata filtering
- [ ] Add embedding update/delete operations
- [ ] Implement collection management
- [ ] Add query result ranking and filtering

**Implementation Structure:**
```python
import chromadb
from chromadb.config import Settings

class VectorDBService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.query_collection = self.client.get_collection("query_embeddings")
        self.context_collection = self.client.get_collection("context_embeddings")
    
    async def store_query_embedding(
        self, 
        query: str, 
        embedding: List[float],
        metadata: Dict
    ):
        """Store query embedding with metadata"""
        # Implementation here
    
    async def search_similar_queries(
        self, 
        query_embedding: List[float],
        top_k: int = 5,
        metadata_filter: Optional[Dict] = None
    ) -> List[Dict]:
        """Search for similar queries"""
        # Implementation here
```

#### **2.4 Enhanced Data Context Service**

**File**: `backend/app/utils/data_context.py` (modifications)

**Tasks:**
- [ ] Add context summarization function
- [ ] Implement context chunking for large datasets
- [ ] Add metadata extraction (dimensions, metrics, time ranges)
- [ ] Create context relevance scoring
- [ ] Implement context versioning
- [ ] Add context compression for vector storage

---

### Phase 3: Integration & Testing (Week 5-6)

#### **3.1 Service Integration**

**Tasks:**
- [ ] Update `InsightsService` to use `query_ollama()` instead of `query_perplexity()`
- [ ] Integrate vector DB search before LLM query
- [ ] Implement context enrichment (merge current + historical)
- [ ] Add response storage in vector DB
- [ ] Update error handling for local LLM
- [ ] Implement fallback to Perplexity if Ollama fails (temporary)
- [ ] Add feature flag for gradual rollout

**Integration Example:**
```python
# In insights_service.py
async def process_chat(self, request: InsightsChatRequest):
    # ... existing query building and data context generation ...
    
    # NEW: Vector DB search for similar queries
    embedding_service = EmbeddingService()
    query_embedding = await embedding_service.generate_embedding(user_message)
    
    vector_service = VectorDBService()
    similar_queries = await vector_service.search_similar_queries(
        query_embedding,
        top_k=3,
        metadata_filter={"dimensions": detected_dimensions}
    )
    
    # Enrich context with similar query responses
    enriched_context = self._enrich_context_with_history(
        data_context,
        similar_queries
    )
    
    # Use Ollama instead of Perplexity
    ai_response = await query_ollama(
        user_prompt,
        conversation_history,
        custom_system_message=system_context
    )
    
    # Store response in vector DB
    await vector_service.store_response_embedding(
        user_message,
        ai_response,
        query_embedding,
        metadata
    )
```

#### **3.2 Testing & Validation**

**Tasks:**
- [ ] Unit tests for LLM service
- [ ] Unit tests for embedding service
- [ ] Unit tests for vector DB service
- [ ] Integration tests for end-to-end flow
- [ ] Performance tests (response time, throughput)
- [ ] Load tests (concurrent users)
- [ ] Quality tests (compare responses with Perplexity)
- [ ] A/B testing framework (Ollama vs Perplexity)

**Test Scenarios:**
1. Single user query
2. Concurrent queries (10, 50, 100 users)
3. Long conversation history
4. Large data context
5. Complex multi-dimensional queries
6. Error scenarios (Ollama down, vector DB down)

#### **3.3 Response Quality Validation**

**Tasks:**
- [ ] Create test question set (use existing TEST_QUESTIONS.md)
- [ ] Run same queries on both Perplexity and Ollama
- [ ] Compare response quality:
  - Accuracy
  - Completeness
  - Relevance
  - Clarity
- [ ] Measure response time
- [ ] Document quality differences
- [ ] Fine-tune prompts if needed

---

### Phase 4: Deployment Preparation (Week 7-8)

#### **4.1 Production Environment Setup**

**Tasks:**
- [ ] Set up production MacBook (512GB RAM)
- [ ] Install Ollama on production server
- [ ] Download production models
- [ ] Configure production Ollama settings:
  - Memory limits
  - Concurrent request limits
  - Model loading strategy
- [ ] Set up ChromaDB on production
- [ ] Configure persistent storage
- [ ] Set up backup strategy for vector DB
- [ ] Configure monitoring and logging

#### **4.2 Deployment Architecture**

**Tasks:**
- [ ] Design deployment architecture:
  - Option 1: Single server (MacBook) with all services
  - Option 2: Separate services (API server + LLM server)
  - Option 3: Containerized deployment (Docker)
- [ ] Set up reverse proxy (Nginx) for API routing
- [ ] Configure SSL/TLS certificates
- [ ] Set up domain and DNS
- [ ] Configure firewall rules
- [ ] Set up load balancing (if multiple instances)

#### **4.3 Monitoring & Observability**

**Tasks:**
- [ ] Set up logging:
  - LLM request/response logs
  - Vector DB operation logs
  - Performance metrics
  - Error tracking
- [ ] Implement metrics collection:
  - Response time
  - Token generation speed
  - Memory usage
  - Request throughput
  - Error rates
- [ ] Set up alerting:
  - Ollama service down
  - High response times
  - High error rates
  - Memory usage alerts

---

### Phase 5: Global Deployment Strategy (Week 9-10)

#### **5.1 Deployment Options**

**Option A: Direct MacBook Deployment (Recommended for Start)**
- **Setup**: 
  - MacBook as production server
  - Public IP or VPN access
  - Reverse proxy (Nginx) for routing
- **Pros**: 
  - Simple setup
  - No cloud costs
  - Full control
- **Cons**: 
  - Single point of failure
  - Limited scalability
  - Requires stable internet

**Option B: Cloud Deployment (Future Scalability)**
- **Setup**:
  - Deploy Ollama on cloud VM (AWS EC2, GCP, Azure)
  - Use managed vector DB (Pinecone, Weaviate Cloud)
  - Load balancer for multiple instances
- **Pros**:
  - Scalable
  - High availability
  - Global CDN support
- **Cons**:
  - Higher costs
  - More complex setup

**Option C: Hybrid Approach**
- **Setup**:
  - MacBook for LLM inference (local)
  - Cloud for API server and MongoDB
  - Vector DB on MacBook or cloud
- **Pros**:
  - Balance of cost and scalability
  - LLM runs locally (no token costs)
  - API can scale in cloud
- **Cons**:
  - Network latency between services
  - More complex architecture

#### **5.2 Recommended Deployment Architecture**

```
                    Internet
                       │
                       ▼
            ┌──────────────────────┐
            │   Cloudflare CDN     │
            │   (Optional)         │
            └──────────┬───────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │   Nginx Reverse      │
            │   Proxy (MacBook)    │
            │   Port 80/443        │
            └──────────┬───────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  FastAPI     │ │   Ollama     │ │  ChromaDB    │
│  Backend     │ │   LLM        │ │  Vector DB   │
│  Port 8000   │ │   Port 11434│ │  Port 8001   │
└──────┬───────┘ └──────────────┘ └──────────────┘
       │
       ▼
┌──────────────┐
│   MongoDB    │
│  (Cloud/     │
│   Local)     │
└──────────────┘
```

#### **5.3 Deployment Steps**

**Step 1: MacBook Server Setup**
```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Start Ollama service
ollama serve

# 3. Download models
ollama pull llama3.1:70b
ollama pull llama3.1:8b

# 4. Install Nginx
brew install nginx

# 5. Configure Nginx reverse proxy
# Edit /usr/local/etc/nginx/nginx.conf
```

**Step 2: Nginx Configuration**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ollama {
        proxy_pass http://localhost:11434;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Step 3: SSL/TLS Setup**
```bash
# Install Certbot
brew install certbot

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

**Step 4: Firewall Configuration**
```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH (if remote access needed)
sudo ufw allow 22/tcp
```

**Step 5: Service Management**
```bash
# Create systemd service for Ollama (if on Linux)
# For macOS, use launchd

# Create launchd plist for Ollama
# /Library/LaunchDaemons/com.ollama.server.plist
```

---

## Technical Implementation Details

### 5.1 LLM Service Implementation

**File**: `backend/app/utils/llm_service.py`

```python
"""
LLM Service utilities
Handles Ollama local LLM integration
"""
import os
import asyncio
import httpx
import logging
from typing import Optional, List, Dict, AsyncGenerator
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.default_model = os.getenv("OLLAMA_MODEL", "llama3.1:70b")
        self.fallback_model = os.getenv("OLLAMA_FALLBACK_MODEL", "llama3.1:8b")
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "120"))
        self.client = httpx.AsyncClient(timeout=self.timeout)
    
    async def query_ollama(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict]] = None,
        custom_system_message: Optional[str] = None,
        model: Optional[str] = None,
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        Query Ollama LLM for AI responses
        
        Args:
            prompt: User prompt/question
            conversation_history: Previous conversation messages
            custom_system_message: Optional custom system message
            model: Ollama model name (defaults to configured model)
            stream: Whether to stream response
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
        """
        model = model or self.default_model
        
        system_content = custom_system_message or (
            "You are Vector AI, a strategic business intelligence analyst for ThriveBrands. "
            "Analyze the provided business data and generate strategic marketing and business recommendations. "
            "All monetary values are in Euros (€). Be specific, data-driven, and actionable."
        )
        
        messages = [{"role": "system", "content": system_content}]
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            if stream:
                return await self._stream_response(payload)
            else:
                response = await self.client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result.get("message", {}).get("content", "")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Model not found, try fallback
                logger.warning(f"Model {model} not found, trying fallback {self.fallback_model}")
                payload["model"] = self.fallback_model
                response = await self.client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result.get("message", {}).get("content", "")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Ollama API error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error querying Ollama: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"LLM service error: {str(e)}"
            )
    
    async def _stream_response(self, payload: Dict) -> str:
        """Handle streaming response from Ollama"""
        full_response = ""
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    import json
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            content = data["message"]["content"]
                            full_response += content
                    except json.JSONDecodeError:
                        continue
        return full_response
    
    async def generate_embedding(self, text: str, model: str = "llama3.1:70b") -> List[float]:
        """Generate embedding using Ollama"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": model, "prompt": text}
            )
            response.raise_for_status()
            result = response.json()
            return result.get("embedding", [])
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

# Global instance
ollama_service = OllamaService()

async def query_ollama(
    prompt: str,
    conversation_history: Optional[List[Dict]] = None,
    custom_system_message: Optional[str] = None,
    model: Optional[str] = None,
    stream: bool = False
) -> str:
    """Query Ollama LLM (wrapper function for backward compatibility)"""
    return await ollama_service.query_ollama(
        prompt=prompt,
        conversation_history=conversation_history,
        custom_system_message=custom_system_message,
        model=model,
        stream=stream
    )
```

### 5.2 Embedding Service Implementation

**File**: `backend/app/utils/embedding_service.py`

```python
"""
Embedding Service utilities
Handles text embedding generation for vector search
"""
import logging
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service
        
        Args:
            model_name: Sentence transformer model name
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        logger.info(f"Embedding model loaded: {model_name}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text to embed
            
        Returns:
            List of float values representing the embedding
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * 384  # Default dimension for all-MiniLM-L6-v2
        
        try:
            embedding = self.model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing)
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embeddings
        """
        if not texts:
            return []
        
        # Filter empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return [[0.0] * 384] * len(texts)
        
        try:
            embeddings = self.model.encode(
                valid_texts,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score between 0 and 1
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

# Global instance
embedding_service = EmbeddingService()
```

### 5.3 Vector Database Service Implementation

**File**: `backend/app/utils/vector_service.py`

```python
"""
Vector Database Service utilities
Handles vector storage and semantic search using ChromaDB
"""
import logging
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class VectorDBService:
    def __init__(self, db_path: str = "./chroma_db"):
        """
        Initialize vector database service
        
        Args:
            db_path: Path to ChromaDB persistent storage
        """
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collections
        self.query_collection = self._get_or_create_collection("query_embeddings")
        self.context_collection = self._get_or_create_collection("context_embeddings")
        self.response_collection = self._get_or_create_collection("response_embeddings")
        
        logger.info("VectorDB service initialized")
    
    def _get_or_create_collection(self, name: str):
        """Get existing collection or create new one"""
        try:
            return self.client.get_collection(name)
        except:
            return self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
    
    async def store_query_embedding(
        self,
        query: str,
        embedding: List[float],
        metadata: Dict,
        query_id: Optional[str] = None
    ) -> str:
        """
        Store query embedding with metadata
        
        Args:
            query: Original query text
            embedding: Query embedding vector
            metadata: Additional metadata (dimensions, metrics, etc.)
            query_id: Optional custom ID
            
        Returns:
            Stored query ID
        """
        if not query_id:
            query_id = str(uuid.uuid4())
        
        metadata["timestamp"] = datetime.now().isoformat()
        metadata["type"] = "query"
        
        self.query_collection.add(
            ids=[query_id],
            embeddings=[embedding],
            documents=[query],
            metadatas=[metadata]
        )
        
        logger.info(f"Stored query embedding: {query_id}")
        return query_id
    
    async def store_context_embedding(
        self,
        context_summary: str,
        embedding: List[float],
        metadata: Dict,
        context_id: Optional[str] = None
    ) -> str:
        """
        Store context embedding with metadata
        
        Args:
            context_summary: Summarized context text
            embedding: Context embedding vector
            metadata: Additional metadata
            context_id: Optional custom ID
            
        Returns:
            Stored context ID
        """
        if not context_id:
            context_id = str(uuid.uuid4())
        
        metadata["timestamp"] = datetime.now().isoformat()
        metadata["type"] = "context"
        
        self.context_collection.add(
            ids=[context_id],
            embeddings=[embedding],
            documents=[context_summary],
            metadatas=[metadata]
        )
        
        logger.info(f"Stored context embedding: {context_id}")
        return context_id
    
    async def store_response_embedding(
        self,
        query: str,
        response: str,
        query_embedding: List[float],
        metadata: Dict,
        response_id: Optional[str] = None
    ) -> str:
        """
        Store response embedding with query-reference
        
        Args:
            query: Original query
            response: AI response
            query_embedding: Query embedding for linking
            metadata: Additional metadata
            response_id: Optional custom ID
            
        Returns:
            Stored response ID
        """
        if not response_id:
            response_id = str(uuid.uuid4())
        
        metadata["timestamp"] = datetime.now().isoformat()
        metadata["type"] = "response"
        metadata["query"] = query
        
        self.response_collection.add(
            ids=[response_id],
            embeddings=[query_embedding],  # Use query embedding for searchability
            documents=[response],
            metadatas=[metadata]
        )
        
        logger.info(f"Stored response embedding: {response_id}")
        return response_id
    
    async def search_similar_queries(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        metadata_filter: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar queries
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            metadata_filter: Optional metadata filter
            
        Returns:
            List of similar queries with metadata
        """
        try:
            results = self.query_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=metadata_filter
            )
            
            similar_queries = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    similar_queries.append({
                        "id": results["ids"][0][i],
                        "query": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if "distances" in results else None
                    })
            
            logger.info(f"Found {len(similar_queries)} similar queries")
            return similar_queries
        except Exception as e:
            logger.error(f"Error searching similar queries: {str(e)}")
            return []
    
    async def search_similar_contexts(
        self,
        query_embedding: List[float],
        top_k: int = 3,
        metadata_filter: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar contexts
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            metadata_filter: Optional metadata filter
            
        Returns:
            List of similar contexts with metadata
        """
        try:
            results = self.context_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=metadata_filter
            )
            
            similar_contexts = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    similar_contexts.append({
                        "id": results["ids"][0][i],
                        "context": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if "distances" in results else None
                    })
            
            logger.info(f"Found {len(similar_contexts)} similar contexts")
            return similar_contexts
        except Exception as e:
            logger.error(f"Error searching similar contexts: {str(e)}")
            return []
    
    async def get_response_for_query(
        self,
        query_embedding: List[float],
        top_k: int = 1
    ) -> Optional[Dict]:
        """
        Get stored response for similar query
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            Most similar response or None
        """
        try:
            results = self.response_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            if results["ids"] and len(results["ids"][0]) > 0:
                return {
                    "id": results["ids"][0][0],
                    "response": results["documents"][0][0],
                    "metadata": results["metadatas"][0][0],
                    "distance": results["distances"][0][0] if "distances" in results else None
                }
            return None
        except Exception as e:
            logger.error(f"Error getting response: {str(e)}")
            return None

# Global instance
vector_db_service = VectorDBService()
```

### 5.4 Updated Insights Service Integration

**File**: `backend/app/services/insights_service.py` (modifications)

```python
# Replace Perplexity import
from app.utils.llm_service import query_ollama
from app.utils.embedding_service import embedding_service
from app.utils.vector_service import vector_db_service

# In process_chat method, replace:
# ai_response = await query_perplexity(...)
# With:

# Generate embedding for current query
query_embedding = embedding_service.generate_embedding(user_message)

# Search for similar queries and contexts
similar_queries = await vector_db_service.search_similar_queries(
    query_embedding,
    top_k=3,
    metadata_filter={
        "dimensions": detected_dimensions,
        "metrics": detected_metric
    } if detected_dimensions else None
)

# Enrich context with similar query responses
enriched_context = data_context
if similar_queries:
    # Get responses for similar queries
    for similar_query in similar_queries:
        response = await vector_db_service.get_response_for_query(
            query_embedding,
            top_k=1
        )
        if response and response.get("distance", 1.0) < 0.3:  # Similarity threshold
            enriched_context += f"\n\nSimilar Query Context: {response['response']}"

# Query Ollama instead of Perplexity
ai_response = await query_ollama(
    user_prompt,
    conversation_history,
    custom_system_message=system_context
)

# Store query, context, and response in vector DB
await vector_db_service.store_query_embedding(
    user_message,
    query_embedding,
    {
        "dimensions": detected_dimensions,
        "metrics": detected_metric,
        "session_id": session_id
    }
)

# Store context summary
context_summary = self._summarize_context(data_context)
context_embedding = embedding_service.generate_embedding(context_summary)
await vector_db_service.store_context_embedding(
    context_summary,
    context_embedding,
    {
        "dimensions": detected_dimensions,
        "metrics": detected_metric,
        "query_id": query_id
    }
)

# Store response
await vector_db_service.store_response_embedding(
    user_message,
    ai_response,
    query_embedding,
    {
        "session_id": session_id,
        "query_id": query_id,
        "context_id": context_id
    }
)
```

---

## Performance & Scalability

### 6.1 Performance Benchmarks

**Expected Performance (512GB RAM MacBook):**

| Metric | Perplexity API | Ollama (llama3.1:70b) | Ollama (llama3.1:8b) |
|--------|---------------|----------------------|---------------------|
| Response Time | 2-5 seconds | 5-15 seconds | 2-5 seconds |
| Concurrent Requests | Limited by API | 4-8 (configurable) | 10-20 (configurable) |
| Token Generation | ~50 tokens/sec | ~20-30 tokens/sec | ~100 tokens/sec |
| Memory Usage | N/A | ~40-50GB | ~5-8GB |
| Cost per Query | $0.001-0.01 | $0 (electricity only) | $0 (electricity only) |

### 6.2 Scalability Strategies

**For 1000+ Users:**

1. **Request Queuing**:
   - Implement request queue for Ollama
   - Priority-based queuing (VIP users first)
   - Timeout handling for queued requests

2. **Model Loading Strategy**:
   - Keep primary model (70b) loaded in memory
   - Lazy load fallback model (8b) when needed
   - Model unloading for memory management

3. **Caching**:
   - Cache frequent queries and responses
   - Use vector DB for semantic caching
   - Redis for exact query caching

4. **Load Balancing** (Future):
   - Multiple Ollama instances
   - Round-robin or least-connections routing
   - Health checks and failover

5. **Response Streaming**:
   - Stream responses to users
   - Better perceived performance
   - Lower memory usage

---

## Cost Analysis

### 7.1 Current Costs (Perplexity API)

**Assumptions:**
- 1000 users
- 10 queries per user per day
- Average 2000 tokens per query (input + output)
- Perplexity cost: $0.001 per 1K tokens

**Daily Cost:**
- Total queries: 10,000
- Total tokens: 20,000,000
- Cost: $20,000/day = **$600,000/month**

### 7.2 New Costs (Local LLM)

**Hardware Costs:**
- MacBook (512GB RAM): Already owned
- Electricity: ~500W × 24h × $0.12/kWh = **$43/month**

**Software Costs:**
- Ollama: Free
- ChromaDB: Free
- Sentence-transformers: Free

**Total Monthly Cost: ~$43** (electricity only)

**Savings: $599,957/month** (99.99% reduction)

---

## Risk Mitigation

### 8.1 Technical Risks

**Risk 1: Model Quality**
- **Mitigation**: A/B testing, prompt engineering, fine-tuning
- **Fallback**: Keep Perplexity as backup option

**Risk 2: Performance Issues**
- **Mitigation**: Load testing, optimization, caching
- **Fallback**: Use smaller model (8b) for speed

**Risk 3: Single Point of Failure**
- **Mitigation**: Health monitoring, automated restarts
- **Fallback**: Cloud deployment option ready

**Risk 4: Memory Constraints**
- **Mitigation**: Model management, memory monitoring
- **Fallback**: Use smaller models or cloud deployment

### 8.2 Operational Risks

**Risk 1: Deployment Complexity**
- **Mitigation**: Phased rollout, comprehensive testing
- **Fallback**: Gradual migration with feature flags

**Risk 2: Maintenance Overhead**
- **Mitigation**: Automated monitoring, clear documentation
- **Fallback**: Managed service option (future)

---

## Migration Checklist

### Pre-Migration
- [ ] Backup current Perplexity integration code
- [ ] Document current API usage patterns
- [ ] Set up development environment
- [ ] Install Ollama and test locally
- [ ] Set up ChromaDB and test

### Phase 1: Infrastructure
- [ ] Install Ollama on MacBook
- [ ] Download required models
- [ ] Configure Ollama settings
- [ ] Set up ChromaDB
- [ ] Install embedding models
- [ ] Test all components

### Phase 2: Implementation
- [ ] Implement LLM service
- [ ] Implement embedding service
- [ ] Implement vector DB service
- [ ] Update insights service
- [ ] Add vector DB integration
- [ ] Update error handling

### Phase 3: Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] Performance tests
- [ ] Quality comparison tests
- [ ] Load tests
- [ ] A/B testing setup

### Phase 4: Deployment
- [ ] Production environment setup
- [ ] Nginx configuration
- [ ] SSL/TLS setup
- [ ] Monitoring setup
- [ ] Backup strategy
- [ ] Documentation

### Phase 5: Rollout
- [ ] Feature flag implementation
- [ ] Gradual user migration (10%, 50%, 100%)
- [ ] Monitor performance
- [ ] Collect feedback
- [ ] Optimize based on data
- [ ] Full migration

---

## Conclusion

This migration will:
1. **Eliminate token costs** (99.99% reduction)
2. **Improve data privacy** (no external API calls)
3. **Enable better customization** (local model control)
4. **Provide vector search** (semantic similarity)
5. **Scale cost-effectively** (no per-query costs)

**Timeline**: 10 weeks for complete migration
**Investment**: Development time + MacBook hardware (already owned)
**ROI**: $600K/month savings after migration

---

## Next Steps

1. **Review and approve** this roadmap
2. **Set up development environment** (Week 1)
3. **Begin Phase 1** (Infrastructure Setup)
4. **Weekly progress reviews**
5. **Adjust timeline** based on findings

---

## Support & Resources

- **Ollama Documentation**: https://ollama.com/docs
- **ChromaDB Documentation**: https://docs.trychroma.com
- **Sentence Transformers**: https://www.sbert.net
- **FastAPI Async**: https://fastapi.tiangolo.com/async/

---

**Document Version**: 1.0  
**Last Updated**: [Current Date]  
**Author**: AI Assistant  
**Status**: Draft - Pending Review

