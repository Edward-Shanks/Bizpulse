"""
AI Cache Service
Handles permission-aware, time-aware caching for AI chatbot queries
"""
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta, date
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
import logging
from typing import Callable, Awaitable
import json

from app.core.database import get_database
from app.database.clickhouse_client import ClickHouseClient
from app.services.ai.utils.permission_hash import generate_permissions_hash
from app.services.ai.utils.intent_hash import generate_intent_hash
from app.services.ai.utils.ttl_calculator import get_cache_ttl

logger = logging.getLogger(__name__)

# Response cache TTL (same question + same data = reuse explanation)
RESPONSE_CACHE_TTL_SECONDS = 86400  # 24 hours


class AICacheService:
    """
    AI Chatbot Cache Service
    
    Features:
    - Permission-aware caching (different users get different cache)
    - Time-aware caching (TTL based on query type)
    - Data version tracking (auto-invalidation when new data arrives)
    - MongoDB storage with compound indexes for fast lookup
    """
    
    def __init__(self):
        """Initialize cache service"""
        self.db: AsyncIOMotorDatabase = get_database()
        self.cache_collection: AsyncIOMotorCollection = self.db.ai_cache
        self.response_cache_collection: AsyncIOMotorCollection = self.db.ai_response_cache
        self.clickhouse_client = ClickHouseClient()
    
    def get_data_version(self, tenant_id: str) -> date:
        """
        Get latest data date from ClickHouse (for cache invalidation)
        
        When new data arrives, data_version changes → cache automatically invalidates
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            Latest date from ClickHouse sales_analytics table
        """
        try:
            query = f"""
                SELECT max(date)
                FROM bizpulse.sales_analytics
                WHERE tenant_id = '{tenant_id}'
            """
            result = self.clickhouse_client.execute(
                query,
                tenant_id=tenant_id,
                enforce_time_filter=False  # System query, no time filter needed
            )
            if result and len(result) > 0 and result[0][0]:
                return result[0][0]
            # Fallback: return today if no data
            return date.today()
        except Exception as e:
            logger.error(f"Failed to get data version: {e}")
            # Fallback: return today
            return date.today()
    
    async def get_cache(
        self,
        tenant_id: str,
        permissions_hash: str,
        intent_hash: str,
        data_version: date
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached result if exists and valid
        
        Args:
            tenant_id: Tenant identifier
            permissions_hash: Hash of user's RBAC permissions
            intent_hash: Hash of LLM intent
            data_version: Current data version (max date from ClickHouse)
        
        Returns:
            Cached result dict if found and valid, None otherwise
        """
        try:
            cache_doc = await self.cache_collection.find_one({
                "tenant_id": tenant_id,
                "permissions_hash": permissions_hash,
                "intent_hash": intent_hash,
                "data_version": data_version.isoformat(),  # Store as ISO string
                "expires_at": {"$gt": datetime.utcnow()}  # Not expired
            })
            
            if cache_doc:
                logger.info(f"Cache HIT: tenant={tenant_id}, intent_hash={intent_hash[:8]}...")
                return cache_doc.get("result")
            
            logger.debug(f"Cache MISS: tenant={tenant_id}, intent_hash={intent_hash[:8]}...")
            return None
        except Exception as e:
            logger.error(f"Cache lookup failed: {e}")
            return None
    
    async def store_cache(
        self,
        tenant_id: str,
        permissions_hash: str,
        intent_hash: str,
        data_version: date,
        result: Any,
        ttl_seconds: int
    ) -> None:
        """
        Store result in cache
        
        Args:
            tenant_id: Tenant identifier
            permissions_hash: Hash of user's RBAC permissions
            intent_hash: Hash of LLM intent
            data_version: Current data version (max date from ClickHouse)
            result: Result to cache (ClickHouse query result)
            ttl_seconds: Time-to-live in seconds
        """
        try:
            created_at = datetime.utcnow()
            expires_at = created_at + timedelta(seconds=ttl_seconds)
            
            safe_result = self._to_json_safe(result)
            cache_doc = {
                "tenant_id": tenant_id,
                "permissions_hash": permissions_hash,
                "intent_hash": intent_hash,
                "data_version": data_version.isoformat(),
                "result": safe_result,
                "created_at": created_at,
                "expires_at": expires_at
            }
            
            # Use upsert to replace if exists (same key)
            await self.cache_collection.replace_one(
                {
                    "tenant_id": tenant_id,
                    "permissions_hash": permissions_hash,
                    "intent_hash": intent_hash,
                    "data_version": data_version.isoformat()
                },
                cache_doc,
                upsert=True
            )
            
            logger.info(f"Cached result: tenant={tenant_id}, intent_hash={intent_hash[:8]}..., TTL={ttl_seconds}s")
        except Exception as e:
            logger.error(f"Cache store failed: {e}")
            # Don't raise - cache failure shouldn't break the request

    async def get_cached_response(
        self,
        tenant_id: str,
        permissions_hash: str,
        intent_hash: str,
        result_hash: str,
        question_hash: str,
    ) -> Optional[str]:
        """
        Get cached LLM explanation text for (question + intent + result).
        question_hash ensures different questions (e.g. "compare KOKA, Green Aware..." vs "compare Bonne Maman with other brands")
        do not share the same cached explanation when they produce the same intent/result.
        """
        try:
            doc = await self.response_cache_collection.find_one({
                "tenant_id": tenant_id,
                "permissions_hash": permissions_hash,
                "intent_hash": intent_hash,
                "result_hash": result_hash,
                "question_hash": question_hash,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            if doc:
                logger.info(f"Response cache HIT: tenant={tenant_id}, question_hash={question_hash[:8]}...")
                return doc.get("response_text")
            return None
        except Exception as e:
            logger.error(f"Response cache lookup failed: {e}")
            return None

    async def set_cached_response(
        self,
        tenant_id: str,
        permissions_hash: str,
        intent_hash: str,
        result_hash: str,
        question_hash: str,
        response_text: str,
        ttl_seconds: int = RESPONSE_CACHE_TTL_SECONDS
    ) -> None:
        """Store LLM explanation keyed by question + intent + result so answers match the asked question."""
        try:
            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=ttl_seconds)
            await self.response_cache_collection.replace_one(
                {
                    "tenant_id": tenant_id,
                    "permissions_hash": permissions_hash,
                    "intent_hash": intent_hash,
                    "result_hash": result_hash,
                    "question_hash": question_hash,
                },
                {
                    "tenant_id": tenant_id,
                    "permissions_hash": permissions_hash,
                    "intent_hash": intent_hash,
                    "result_hash": result_hash,
                    "question_hash": question_hash,
                    "response_text": response_text,
                    "created_at": now,
                    "expires_at": expires_at,
                },
                upsert=True
            )
            logger.info(f"Response cached: tenant={tenant_id}, question_hash={question_hash[:8]}..., TTL={ttl_seconds}s")
        except Exception as e:
            logger.error(f"Response cache store failed: {e}")

    def _to_json_safe(self, value: Any) -> Any:
        """
        Convert ClickHouse results (Decimal/date/datetime) to BSON/JSON safe values.
        """
        try:
            return json.loads(json.dumps(value, default=str))
        except Exception:
            # Fallback to raw value so request still succeeds even if cache write fails.
            return value
    
    async def get_or_set_cache(
        self,
        tenant_id: str,
        access: Dict[str, Any],
        intent: Dict[str, Any],
        query_function: Callable[[], Awaitable[Any]]
    ) -> Any:
        """
        Get cached result or execute query function and cache result
        
        This is the main cache method - use this in your chatbot endpoint.
        
        Args:
            tenant_id: Tenant identifier
            access: User's RBAC access dict (from MongoDB)
            intent: LLM intent dict
            query_function: Async function that returns result if cache miss
        
        Returns:
            Cached result or result from query_function
        """
        # Generate hashes
        permissions_hash = generate_permissions_hash(access)
        intent_hash = generate_intent_hash(intent)
        
        # Get current data version
        data_version = self.get_data_version(tenant_id)
        
        # Try cache lookup
        cached_result = await self.get_cache(
            tenant_id,
            permissions_hash,
            intent_hash,
            data_version
        )
        
        if cached_result is not None:
            return cached_result
        
        # Cache miss - execute query function
        logger.info("Cache MISS - executing query")
        result = await query_function()
        
        # Calculate TTL based on intent
        ttl_seconds = get_cache_ttl(intent)
        
        # Store in cache
        await self.store_cache(
            tenant_id,
            permissions_hash,
            intent_hash,
            data_version,
            result,
            ttl_seconds
        )
        
        return result
