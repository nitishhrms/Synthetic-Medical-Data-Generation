"""
Shared Database Utilities for Microservices
Lightweight database connection management using asyncpg and Redis
"""
import os
import asyncpg
import redis.asyncio as redis
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Async PostgreSQL connection manager"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://clinical_user:clinical_pass@postgres:5432/clinical_trials"
        )

    async def connect(self, max_retries=5, retry_delay=2):
        """Initialize database connection pool with retry logic"""
        import asyncio

        for attempt in range(max_retries):
            try:
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=60,
                    timeout=30
                )
                logger.info("Database connection pool created successfully")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Failed to connect to database (attempt {attempt + 1}/{max_retries}): {e}")
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to connect to database after {max_retries} attempts: {e}")
                    logger.info("Service will continue without database connection")
                    # Don't raise - allow service to start without DB for health checks

    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    async def execute(self, query: str, *args):
        """Execute a query that doesn't return results"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        """Execute a query and fetch all results"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Execute a query and fetch one result"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """Execute a query and fetch a single value"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)


class CacheConnection:
    """Async Redis cache manager"""

    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.redis_host = os.getenv("REDIS_HOST", "redis")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.enabled = True

    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            await self.client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Running without cache.")
            self.enabled = False
            self.client = None

    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if not self.enabled or not self.client:
            return None
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: str, ttl: int = 300):
        """Set value in cache with TTL (default 5 minutes)"""
        if not self.enabled or not self.client:
            return False
        try:
            await self.client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    async def delete(self, key: str):
        """Delete key from cache"""
        if not self.enabled or not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False

    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        if not self.enabled or not self.client:
            return 0
        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete pattern error: {e}")
            return 0



    async def init_db(self):
        """Initialize database schema from SQL file"""
        if not self.pool:
            logger.warning("Cannot initialize DB: No connection pool")
            return

        try:
            # Get path to schema.sql (assumed to be in same directory as this file)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            schema_path = os.path.join(current_dir, "schema.sql")
            
            if os.path.exists(schema_path):
                with open(schema_path, "r") as f:
                    schema_sql = f.read()
                
                async with self.pool.acquire() as conn:
                    await conn.execute(schema_sql)
                logger.info("Database schema initialized successfully")
                
                # Also try to initialize medical images schema if it exists
                images_schema_path = os.path.join(current_dir, "medical_images_schema.sql")
                if os.path.exists(images_schema_path):
                    with open(images_schema_path, "r") as f:
                        images_schema_sql = f.read()
                    async with self.pool.acquire() as conn:
                        await conn.execute(images_schema_sql)
                    logger.info("Medical images schema initialized successfully")
            else:
                logger.warning(f"Schema file not found at {schema_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")


# Global instances
db = DatabaseConnection()
cache = CacheConnection()


async def startup_db():
    """Initialize database and cache connections"""
    await db.connect()
    await cache.connect()
    # await db.init_db()  # Temporarily disabled - tables should already exist


async def shutdown_db():
    """Shutdown event handler for FastAPI"""
    await db.disconnect()
    await cache.disconnect()

