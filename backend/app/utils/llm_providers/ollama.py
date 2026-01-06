"""
Ollama Provider (Local LLM on Mac Studio)
Supports remote Ollama instances via SSH tunnel or direct network access
Supports multiple Ollama instances for load balancing and parallel inference
"""
import os
import asyncio
import httpx
import logging
import threading
from typing import Optional, List, Dict, AsyncGenerator
from fastapi import HTTPException
from app.utils.llm_providers.base import LLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global variables for load balancing
_ollama_endpoints: List[str] = []
_endpoint_index: int = 0
_endpoint_lock = threading.Lock()

def _initialize_ollama_endpoints():
    """Initialize the list of Ollama endpoints for load balancing"""
    global _ollama_endpoints
    
    if settings.OLLAMA_ENDPOINTS and len(settings.OLLAMA_ENDPOINTS) > 0:
        _ollama_endpoints = settings.OLLAMA_ENDPOINTS.copy()
        logger.info(f"🔄 Load Balancer: Initialized with {len(_ollama_endpoints)} endpoints: {_ollama_endpoints}")
    else:
        # Fallback to single OLLAMA_BASE_URL
        _ollama_endpoints = [settings.OLLAMA_BASE_URL]
        logger.info(f"🔄 Load Balancer: Using single endpoint (OLLAMA_ENDPOINTS not configured): {settings.OLLAMA_BASE_URL}")

def get_ollama_endpoint() -> str:
    """
    Get the next Ollama endpoint using round-robin load balancing
    Thread-safe for concurrent requests
    """
    global _endpoint_index
    
    # Initialize if not done yet
    if not _ollama_endpoints:
        _initialize_ollama_endpoints()
    
    # Round-robin selection (thread-safe)
    with _endpoint_lock:
        endpoint = _ollama_endpoints[_endpoint_index]
        _endpoint_index = (_endpoint_index + 1) % len(_ollama_endpoints)
        return endpoint

class OllamaProvider(LLMProvider):
    """Ollama provider implementation for local LLM with load balancing support"""
    
    def __init__(self):
        # Initialize load balancer endpoints
        _initialize_ollama_endpoints()
        
        # Configuration from environment
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:32b-instruct")  # Use your existing model
        self.fallback_model = os.getenv("OLLAMA_FALLBACK_MODEL", "llama3:70b")
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "120"))
        # CRITICAL: Configure AsyncClient with limits for true parallelism
        # This allows multiple concurrent requests to Ollama
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            # Note: http2=True removed - requires 'h2' package: pip install httpx[http2]
            # HTTP/1.1 with connection pooling is sufficient for concurrency
        )
        self.is_remote = "localhost" not in self.base_url and "127.0.0.1" not in self.base_url
        
        logger.info(f"Ollama provider initialized: {self.base_url}, model: {self.model}")
        logger.info(f"Load balancer endpoints: {len(_ollama_endpoints)} configured")
    
    def get_provider_name(self) -> str:
        return "ollama"
    
    async def is_available(self) -> bool:
        """Check if Ollama service is available (checks first endpoint)"""
        target_url = get_ollama_endpoint()
        return await self._check_endpoint_availability(target_url)
    
    async def _check_endpoint_availability(self, url: str) -> bool:
        """Check if a specific Ollama endpoint is available"""
        try:
            response = await self.client.get(f"{url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed for {url}: {str(e)}")
            return False
    
    async def generate(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict]] = None,
        custom_system_message: Optional[str] = None,
        temperature: float = 0.2,  # Lower temperature for business responses
        max_tokens: int = 4000,
        **kwargs
    ) -> str:
        """Generate response using Ollama with load balancing"""
        # Get endpoint from load balancer
        target_url = get_ollama_endpoint()
        
        logger.info(f"🦙 OLLAMA: Starting generation request")
        logger.info(f"🦙 OLLAMA: Selected endpoint: {target_url}")
        logger.info(f"🦙 OLLAMA: Model: {self.model}")
        logger.info(f"🦙 OLLAMA: Temperature: {temperature}, Max Tokens: {max_tokens}")
        
        # Check availability on selected endpoint
        is_avail = await self._check_endpoint_availability(target_url)
        logger.info(f"🦙 OLLAMA: Service available: {is_avail}")
        
        if not is_avail:
            logger.error(f"🦙 OLLAMA: Service not available at {target_url}")
            raise HTTPException(
                status_code=503,
                detail=f"Ollama service not available at {target_url}"
            )
        
        # Build messages
        messages = []
        if custom_system_message:
            messages.append({"role": "system", "content": custom_system_message})
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.client.post(
                    f"{target_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                content = result.get("message", {}).get("content", "")
                
                if not content and attempt < max_retries - 1:
                    # Try fallback model
                    logger.warning(f"Empty response from {self.model}, trying fallback {self.fallback_model}")
                    payload["model"] = self.fallback_model
                    continue
                
                logger.info(f"Ollama response generated successfully (model: {payload['model']})")
                return content
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    # Model not found, try fallback
                    if payload["model"] != self.fallback_model:
                        logger.warning(f"Model {self.model} not found, trying fallback {self.fallback_model}")
                        payload["model"] = self.fallback_model
                        continue
                
                if attempt < max_retries - 1:
                    logger.warning(f"Ollama error on attempt {attempt + 1}: {str(e)}")
                    await asyncio.sleep(1)
                    continue
                else:
                    logger.error(f"Ollama failed after {max_retries} attempts: {str(e)}")
                    raise HTTPException(
                        status_code=e.response.status_code,
                        detail=f"Ollama API error: {str(e)}"
                    )
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Ollama error on attempt {attempt + 1}: {str(e)}")
                    await asyncio.sleep(1)
                    continue
                else:
                    logger.error(f"Ollama failed after {max_retries} attempts: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Ollama error: {str(e)}"
                    )
        
        raise HTTPException(
            status_code=500,
            detail="Ollama generation failed after all retries"
        )
    
    async def stream(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict]] = None,
        custom_system_message: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4000,
        think: bool = False,
        **kwargs
    ) -> AsyncGenerator[Dict[str, str], None]:
        """
        Stream response from Ollama with support for thinking field and load balancing
        
        Yields dictionaries with:
        - "type": "thinking" or "content"
        - "data": the actual text chunk
        """
        # Get endpoint from load balancer
        target_url = get_ollama_endpoint()
        
        logger.info(f"🦙 OLLAMA: Starting streaming request")
        logger.info(f"🦙 OLLAMA: Selected endpoint: {target_url}")
        logger.info(f"🦙 OLLAMA: Think mode: {think}")
        
        if not await self._check_endpoint_availability(target_url):
            raise HTTPException(
                status_code=503,
                detail=f"Ollama service not available at {target_url}"
            )
        
        messages = []
        if custom_system_message:
            messages.append({"role": "system", "content": custom_system_message})
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                # CRITICAL: Disable stop sequences that might cause early stopping
                "stop": [],  # Empty stop array to prevent early stopping
            }
        }
        
        # Add think parameter to options if supported (some models support it)
        # Note: Not all Ollama models support thinking, so we'll only add it if explicitly requested
        # and handle gracefully if the model doesn't support it
        if think:
            # Try adding think to options (some models support this)
            payload["options"]["think"] = True
        
        # Log payload for debugging
        logger.info(f"🦙 OLLAMA: Request payload - model: {payload['model']}, messages: {len(payload['messages'])}, max_tokens: {max_tokens}, think: {think}")
        if messages:
            logger.debug(f"🦙 OLLAMA: System message length: {len(messages[0]['content']) if messages[0].get('role') == 'system' else 0}")
            logger.debug(f"🦙 OLLAMA: Last user message: {messages[-1]['content'][:200] if messages[-1].get('role') == 'user' else 'N/A'}...")
        
        try:
            # CRITICAL: Track content properly
            # accumulated_from_ollama: The longest content we've seen from Ollama (source of truth)
            # sent_to_client: What we've already sent to the client (to extract deltas)
            accumulated_from_ollama = ""  # Track what Ollama sends (should always grow)
            sent_to_client = ""  # Track what we've sent (to extract deltas)
            previous_thinking = ""
            buffer = ""  # Buffer for incomplete JSON lines
            
            logger.info(f"🦙 OLLAMA: Starting stream to {target_url}/api/chat")
            
            async with self.client.stream(
                "POST",
                f"{target_url}/api/chat",
                json=payload,
                timeout=self.timeout
            ) as response:
                # Check for HTTP errors BEFORE processing
                if response.status_code != 200:
                    # Read error response
                    error_body = b""
                    async for chunk in response.aiter_bytes():
                        error_body += chunk
                    error_text = error_body.decode('utf-8', errors='ignore') if error_body else "Unknown error"
                    logger.error(f"🦙 OLLAMA: HTTP {response.status_code} error: {error_text}")
                    logger.error(f"🦙 OLLAMA: Request payload: model={payload.get('model')}, messages_count={len(payload.get('messages', []))}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Ollama API error ({response.status_code}): {error_text[:200]}"  # Limit error message length
                    )
                
                logger.info(f"🦙 OLLAMA: Stream connection established, status: {response.status_code}")
                
                # Use aiter_bytes for better streaming (no line buffering)
                async for chunk_bytes in response.aiter_bytes(chunk_size=1024):
                    if not chunk_bytes:
                        continue
                    
                    # Decode chunk and add to buffer
                    chunk_text = chunk_bytes.decode('utf-8', errors='ignore')
                    buffer += chunk_text
                    
                    # Process complete lines (Ollama sends one JSON object per line)
                    # CRITICAL: Handle both \n and \r\n line endings
                    lines_to_process = []
                    while '\n' in buffer or '\r\n' in buffer:
                        # Handle \r\n first (Windows line ending)
                        if '\r\n' in buffer:
                            line, buffer = buffer.split('\r\n', 1)
                        else:
                            line, buffer = buffer.split('\n', 1)
                        # Only process non-empty lines
                        if line.strip():
                            lines_to_process.append(line.strip())
                    
                    # Process each complete line
                    for line in lines_to_process:
                        try:
                            import json
                            data = json.loads(line)
                            
                            # CRITICAL: Ollama can send content in two formats:
                            # 1. Full accumulated content in message.content
                            # 2. Delta content in message.content (incremental)
                            # We need to handle both cases
                            
                            # Handle thinking field (for thinking-capable models)
                            if "message" in data:
                                message = data["message"]
                                
                                # Yield thinking chunks (Ollama returns incremental thinking)
                                if "thinking" in message and message["thinking"]:
                                    current_thinking = message["thinking"]
                                    # Only yield new thinking content (delta)
                                    if current_thinking != previous_thinking and len(current_thinking) > len(previous_thinking):
                                        new_thinking = current_thinking[len(previous_thinking):]
                                        if new_thinking:
                                            logger.debug(f"🦙 OLLAMA: Yielding thinking chunk ({len(new_thinking)} chars)")
                                            yield {
                                                "type": "thinking",
                                                "data": new_thinking
                                            }
                                            previous_thinking = current_thinking
                                
                                # Yield content chunks
                                # CRITICAL: Based on logs, Ollama appears to send FULL accumulated content in message.content
                                # However, we're seeing cases where current is shorter than previous, which suggests
                                # either: 1) Ollama is sending deltas, 2) Content is being reset, or 3) Multiple messages
                                if "content" in message and message["content"] is not None:
                                    current_content = message["content"]
                                    
                                    # Ensure content is a string
                                    if not isinstance(current_content, str):
                                        current_content = str(current_content) if current_content is not None else ""
                                    
                                    # Skip empty content
                                    if not current_content:
                                        continue
                                    
                                    # CRITICAL: Simplified content extraction
                                    # Ollama sends FULL accumulated content in message.content
                                    # Strategy: Only process if current is longer than what we've seen from Ollama
                                    if isinstance(current_content, str) and len(current_content) > 0:
                                        # Only process if this is new content (longer than what we've seen)
                                        if len(current_content) > len(accumulated_from_ollama):
                                            # Verify it starts with what we've seen (normal accumulation)
                                            if not accumulated_from_ollama or current_content.startswith(accumulated_from_ollama):
                                                # Extract delta to send to client
                                                new_delta = current_content[len(sent_to_client):]
                                                if new_delta:
                                                    yield {
                                                        "type": "content",
                                                        "data": new_delta
                                                    }
                                                    sent_to_client = current_content
                                                accumulated_from_ollama = current_content
                                            else:
                                                # Current doesn't start with accumulated - format issue
                                                logger.error(f"🦙 OLLAMA: Format error! Current doesn't extend accumulated")
                                                logger.error(f"🦙 OLLAMA: Accumulated: '{accumulated_from_ollama[:100]}...'")
                                                logger.error(f"🦙 OLLAMA: Current: '{current_content[:100]}...'")
                                                # Try recovery: find accumulated in current
                                                if accumulated_from_ollama in current_content:
                                                    idx = current_content.find(accumulated_from_ollama)
                                                    new_delta = current_content[idx + len(accumulated_from_ollama):]
                                                    if new_delta:
                                                        yield {
                                                            "type": "content",
                                                            "data": new_delta
                                                        }
                                                    sent_to_client = current_content
                                                    accumulated_from_ollama = current_content
                                                else:
                                                    # No recovery - yield everything
                                                    yield {
                                                        "type": "content",
                                                        "data": current_content
                                                    }
                                                    sent_to_client = current_content
                                                    accumulated_from_ollama = current_content
                                        elif current_content == accumulated_from_ollama:
                                            # Duplicate - skip
                                            continue
                                        else:
                                            # Shorter content - skip (shouldn't happen)
                                            logger.warning(f"🦙 OLLAMA: Skipping shorter content: {len(current_content)} < {len(accumulated_from_ollama)}")
                                            continue
                                
                                # Handle done flag
                                if data.get("done", False):
                                    # CRITICAL: Yield any remaining content that wasn't sent yet
                                    if "content" in message and message["content"]:
                                        final_content = message["content"]
                                        if not isinstance(final_content, str):
                                            final_content = str(final_content) if final_content is not None else ""
                                        
                                        # Update accumulated_from_ollama to the longest we've seen
                                        if len(final_content) > len(accumulated_from_ollama):
                                            accumulated_from_ollama = final_content
                                        
                                        # Check if there's any content we haven't sent to client
                                        if isinstance(final_content, str) and len(final_content) > len(sent_to_client):
                                            remaining_content = final_content[len(sent_to_client):]
                                            if remaining_content:
                                                logger.info(f"🦙 OLLAMA: Yielding final content chunk ({len(remaining_content)} chars)")
                                                yield {
                                                    "type": "content",
                                                    "data": remaining_content
                                                }
                                                sent_to_client = final_content
                                    
                                    # Log final state
                                    logger.info(f"🦙 OLLAMA: Stream complete")
                                    logger.info(f"🦙 OLLAMA: Content sent to client: {len(sent_to_client)} chars")
                                    logger.info(f"🦙 OLLAMA: Content from Ollama: {len(accumulated_from_ollama)} chars")
                                    
                                    # Verify we sent all content
                                    if len(accumulated_from_ollama) > len(sent_to_client):
                                        missing_content = accumulated_from_ollama[len(sent_to_client):]
                                        if missing_content:
                                            logger.warning(f"🦙 OLLAMA: Yielding missing final content ({len(missing_content)} chars)")
                                            yield {
                                                "type": "content",
                                                "data": missing_content
                                            }
                                            sent_to_client = accumulated_from_ollama
                                    
                                    yield {
                                        "type": "done",
                                        "data": ""
                                    }
                                    return  # Exit the generator
                        except json.JSONDecodeError:
                            # Incomplete JSON - put back in buffer for next iteration
                            buffer = line + '\n' + buffer
                            break  # Stop processing, wait for more data
                        except Exception as e:
                            logger.warning(f"🦙 OLLAMA: Error parsing chunk: {e}, line: {line[:100]}")
                            continue
        except Exception as e:
            logger.error(f"Ollama streaming error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Ollama streaming error: {str(e)}"
            )

