import memcache
import json
import logging
import threading
from hashlib import sha256
from time import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('MemcachedCache')

class MemcachedCache:
    """
    A class to interact with Memcached for distributed caching.
    Caches frequently accessed data to reduce load on the database and improve system performance.
    """
    
    def __init__(self, servers):
        """
        Initialize Memcached client.
        :param servers: List of Memcached server addresses.
        """
        self.client = memcache.Client(servers, debug=0)
        logger.info("Memcached client initialized with servers: %s", servers)
    
    def set(self, key, value, ttl=3600):
        """
        Set a key-value pair in the cache with an optional time-to-live (TTL).
        :param key: Cache key.
        :param value: Value to store.
        :param ttl: Time-to-live in seconds (default is 1 hour).
        """
        serialized_value = json.dumps(value)
        result = self.client.set(key, serialized_value, time=ttl)
        if result:
            logger.info(f"Cache set for key: {key} with TTL: {ttl} seconds")
        else:
            logger.error(f"Failed to set cache for key: {key}")
    
    def get(self, key):
        """
        Retrieve a value from the cache by key.
        :param key: Cache key.
        :return: The cached value or None if the key doesn't exist.
        """
        value = self.client.get(key)
        if value:
            logger.info(f"Cache hit for key: {key}")
            return json.loads(value)
        logger.info(f"Cache miss for key: {key}")
        return None

    def delete(self, key):
        """
        Delete a key-value pair from the cache.
        :param key: Cache key.
        """
        result = self.client.delete(key)
        if result:
            logger.info(f"Cache deleted for key: {key}")
        else:
            logger.error(f"Failed to delete cache for key: {key}")

    def flush_all(self):
        """
        Clear all cached data.
        """
        result = self.client.flush_all()
        if result:
            logger.info("All cache data flushed")
        else:
            logger.error("Failed to flush cache")

# Memcached lock for atomic operations
class MemcachedLock:
    """
    A distributed lock using Memcached.
    Ensures that only one process/thread can modify a resource at a time.
    """

    def __init__(self, client, key, ttl=60):
        self.client = client
        self.key = f"lock_{key}"
        self.ttl = ttl
        self.acquired = False

    def acquire(self):
        """
        Try to acquire the lock.
        :return: True if the lock was acquired, False otherwise.
        """
        if self.client.add(self.key, "locked", self.ttl):
            self.acquired = True
            logger.info(f"Lock acquired for key: {self.key}")
            return True
        logger.warning(f"Failed to acquire lock for key: {self.key}")
        return False

    def release(self):
        """
        Release the lock.
        """
        if self.acquired:
            self.client.delete(self.key)
            self.acquired = False
            logger.info(f"Lock released for key: {self.key}")
        else:
            logger.warning(f"Cannot release lock, not acquired for key: {self.key}")

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


# Utility functions for caching common operations
def cache_result(cache, key_prefix, ttl=3600):
    """
    Decorator to cache the result of a function.
    :param cache: MemcachedCache instance.
    :param key_prefix: Prefix for the cache key.
    :param ttl: Time-to-live for the cache (default is 1 hour).
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}_{sha256(str(args).encode()).hexdigest()}"
            cached_value = cache.get(cache_key)
            if cached_value:
                return cached_value
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator


# Usage
if __name__ == "__main__":
    # Initialize the Memcached client
    memcached_servers = ["127.0.0.1:11211"]
    cache = MemcachedCache(memcached_servers)

    # Caching a function's result
    @cache_result(cache, "expensive_operation", ttl=600)
    def expensive_operation(param):
        logger.info(f"Performing expensive operation for param: {param}")
        return {"result": param * 2}

    # Perform an operation and cache the result
    result = expensive_operation(5)
    logger.info(f"Operation result: {result}")

    # Demonstrating distributed lock with Memcached
    with MemcachedLock(cache.client, "resource_key") as lock:
        if lock.acquired:
            logger.info("Processing critical section of code.")
        else:
            logger.info("Unable to acquire lock, operation skipped.")

    # Cache management operations
    cache.set("user_session_123", {"username": "Person1", "status": "online"})
    session_data = cache.get("user_session_123")
    logger.info(f"Retrieved session data: {session_data}")

    # Flush all cache
    cache.flush_all()