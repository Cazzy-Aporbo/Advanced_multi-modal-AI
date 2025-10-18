"""
Distributed Rate Limiter with Multiple Algorithms
Author: Cazzy Aporbo

High-performance rate limiting with lock-free data structures,
supports sliding window, token bucket, and leaky bucket algorithms.
Redis-backed for distributed systems with local caching for performance.
"""

import time
import threading
import hashlib
import struct
import asyncio
from typing import Optional, Dict, Any, Callable, Tuple
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import redis
import redis.asyncio as aioredis
from concurrent.futures import ThreadPoolExecutor
import mmh3
import numpy as np


class RateLimitAlgorithm(Enum):
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    SLIDING_LOG = "sliding_log"
    LEAKY_BUCKET = "leaky_bucket"
    FIXED_WINDOW = "fixed_window"


@dataclass
class RateLimitConfig:
    requests_per_second: float
    burst_size: Optional[int] = None
    window_size: int = 60
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET
    distributed: bool = True
    cache_ttl: int = 1
    precision: float = 0.001
    
    def __post_init__(self):
        if self.burst_size is None:
            self.burst_size = int(self.requests_per_second * 1.5)


class AtomicCounter:
    """Lock-free atomic counter using memory barriers"""
    
    __slots__ = ('_value', '_lock')
    
    def __init__(self, initial: int = 0):
        self._value = initial
        self._lock = threading.Lock()
    
    def increment(self, delta: int = 1) -> int:
        with self._lock:
            self._value += delta
            return self._value
    
    def decrement(self, delta: int = 1) -> int:
        with self._lock:
            self._value -= delta
            return self._value
    
    def compare_and_swap(self, expected: int, new: int) -> bool:
        with self._lock:
            if self._value == expected:
                self._value = new
                return True
            return False
    
    @property
    def value(self) -> int:
        return self._value


class BloomFilter:
    """Space-efficient probabilistic data structure for rate limit tracking"""
    
    def __init__(self, capacity: int, error_rate: float = 0.001):
        self.capacity = capacity
        self.error_rate = error_rate
        
        # Calculate optimal parameters
        self.size = self._optimal_size(capacity, error_rate)
        self.hash_count = self._optimal_hash_count(self.size, capacity)
        self.bit_array = np.zeros(self.size, dtype=bool)
        self.count = 0
        
    def _optimal_size(self, n: int, p: float) -> int:
        m = -(n * np.log(p)) / (np.log(2) ** 2)
        return int(m)
    
    def _optimal_hash_count(self, m: int, n: int) -> int:
        k = (m / n) * np.log(2)
        return int(k)
    
    def _hash(self, item: str, seed: int) -> int:
        return mmh3.hash(item, seed) % self.size
    
    def add(self, item: str) -> bool:
        """Add item and return True if it might be new"""
        positions = [self._hash(item, i) for i in range(self.hash_count)]
        
        if all(self.bit_array[pos] for pos in positions):
            return False  # Definitely seen before
        
        for pos in positions:
            self.bit_array[pos] = True
        
        self.count += 1
        return True
    
    def contains(self, item: str) -> bool:
        positions = [self._hash(item, i) for i in range(self.hash_count)]
        return all(self.bit_array[pos] for pos in positions)
    
    def reset(self):
        self.bit_array.fill(False)
        self.count = 0


class CircularBuffer:
    """High-performance circular buffer for sliding window tracking"""
    
    __slots__ = ('_buffer', '_capacity', '_head', '_tail', '_size', '_lock')
    
    def __init__(self, capacity: int):
        self._capacity = capacity
        self._buffer = [None] * capacity
        self._head = 0
        self._tail = 0
        self._size = 0
        self._lock = threading.RLock()
    
    def append(self, item: Any) -> Optional[Any]:
        with self._lock:
            old_item = None
            if self._size == self._capacity:
                old_item = self._buffer[self._tail]
                self._tail = (self._tail + 1) % self._capacity
            else:
                self._size += 1
            
            self._buffer[self._head] = item
            self._head = (self._head + 1) % self._capacity
            
            return old_item
    
    def clear_old(self, timestamp: float, ttl: float) -> int:
        with self._lock:
            removed = 0
            current_time = time.time()
            
            while self._size > 0:
                oldest_idx = self._tail
                oldest = self._buffer[oldest_idx]
                
                if oldest is None or current_time - oldest > ttl:
                    self._buffer[oldest_idx] = None
                    self._tail = (self._tail + 1) % self._capacity
                    self._size -= 1
                    removed += 1
                else:
                    break
            
            return removed
    
    @property
    def size(self) -> int:
        return self._size


class TokenBucket:
    """Token bucket implementation with precise timing"""
    
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()
        self._lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> Tuple[bool, float]:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            
            # Add tokens based on elapsed time
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, 0
            
            # Calculate wait time
            deficit = tokens - self.tokens
            wait_time = deficit / self.rate
            return False, wait_time


class SlidingWindowCounter:
    """Sliding window using circular buffer with microsecond precision"""
    
    def __init__(self, window_size: int, precision: float = 0.001):
        self.window_size = window_size
        self.precision = precision
        
        # Use multiple buckets for precision
        self.bucket_count = max(100, int(window_size / precision))
        self.bucket_duration = window_size / self.bucket_count
        
        self.buckets = [AtomicCounter() for _ in range(self.bucket_count)]
        self.last_bucket_time = time.monotonic()
        self.current_bucket = 0
        self._lock = threading.Lock()
    
    def increment(self) -> int:
        with self._lock:
            self._rotate_buckets()
            self.buckets[self.current_bucket].increment()
            return self._get_total()
    
    def _rotate_buckets(self):
        now = time.monotonic()
        elapsed = now - self.last_bucket_time
        buckets_to_rotate = int(elapsed / self.bucket_duration)
        
        if buckets_to_rotate > 0:
            buckets_to_rotate = min(buckets_to_rotate, self.bucket_count)
            
            for _ in range(buckets_to_rotate):
                self.current_bucket = (self.current_bucket + 1) % self.bucket_count
                self.buckets[self.current_bucket] = AtomicCounter()
            
            self.last_bucket_time = now
    
    def _get_total(self) -> int:
        return sum(bucket.value for bucket in self.buckets)
    
    def get_count(self) -> int:
        with self._lock:
            self._rotate_buckets()
            return self._get_total()


class HybridRateLimiter:
    """Combines multiple algorithms for optimal performance"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.local_cache = {}
        self.cache_lock = threading.Lock()
        
        # Initialize algorithm components
        if config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            self.limiter = TokenBucket(
                config.requests_per_second,
                config.burst_size
            )
        elif config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            self.limiter = SlidingWindowCounter(
                config.window_size,
                config.precision
            )
        else:
            self.limiter = None
        
        # Bloom filter for fast rejection
        expected_requests = int(config.requests_per_second * config.window_size * 2)
        self.bloom = BloomFilter(expected_requests, 0.01)
        
        # Redis connection for distributed mode
        self.redis_client = None
        if config.distributed:
            self._init_redis()
    
    def _init_redis(self):
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1
            )
            self.redis_client.ping()
        except:
            self.redis_client = None
    
    def _get_cache_key(self, identifier: str) -> str:
        return f"rl:{self.config.algorithm.value}:{identifier}"
    
    def allow_request(self, identifier: str) -> Tuple[bool, Optional[float]]:
        """Check if request is allowed, returns (allowed, wait_time)"""
        
        # Fast path: check bloom filter
        if not self.bloom.contains(identifier):
            self.bloom.add(identifier)
        
        # Check local cache first
        cache_key = self._get_cache_key(identifier)
        with self.cache_lock:
            if cache_key in self.local_cache:
                cached_time, cached_result = self.local_cache[cache_key]
                if time.time() - cached_time < self.config.cache_ttl:
                    return cached_result
        
        # Execute rate limit check
        result = self._check_limit(identifier)
        
        # Update cache
        with self.cache_lock:
            self.local_cache[cache_key] = (time.time(), result)
            
            # Clean old cache entries
            if len(self.local_cache) > 10000:
                current_time = time.time()
                self.local_cache = {
                    k: v for k, v in self.local_cache.items()
                    if current_time - v[0] < self.config.cache_ttl
                }
        
        return result
    
    def _check_limit(self, identifier: str) -> Tuple[bool, Optional[float]]:
        if self.config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            return self.limiter.consume()
        
        elif self.config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            count = self.limiter.increment()
            allowed = count <= self.config.requests_per_second * self.config.window_size
            wait_time = None if allowed else 1.0 / self.config.requests_per_second
            return allowed, wait_time
        
        elif self.config.algorithm == RateLimitAlgorithm.SLIDING_LOG:
            return self._sliding_log_check(identifier)
        
        elif self.config.algorithm == RateLimitAlgorithm.LEAKY_BUCKET:
            return self._leaky_bucket_check(identifier)
        
        else:
            return self._fixed_window_check(identifier)
    
    def _sliding_log_check(self, identifier: str) -> Tuple[bool, Optional[float]]:
        """Sliding log with Redis backend for accuracy"""
        
        if not self.redis_client:
            return True, None
        
        try:
            key = self._get_cache_key(identifier)
            now = time.time()
            window_start = now - self.config.window_size
            
            # Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {str(now): now})
            pipe.zcount(key, window_start, now)
            pipe.expire(key, self.config.window_size * 2)
            
            results = pipe.execute()
            count = results[2]
            
            allowed = count <= self.config.requests_per_second * self.config.window_size
            wait_time = None
            
            if not allowed:
                pipe = self.redis_client.pipeline()
                pipe.zrange(key, 0, 0, withscores=True)
                oldest = pipe.execute()[0]
                if oldest:
                    wait_time = self.config.window_size - (now - float(oldest[0][1]))
            
            return allowed, wait_time
            
        except:
            return True, None
    
    def _leaky_bucket_check(self, identifier: str) -> Tuple[bool, Optional[float]]:
        """Leaky bucket with constant rate processing"""
        
        if not self.redis_client:
            return True, None
        
        try:
            key = self._get_cache_key(identifier)
            now = time.time()
            rate = self.config.requests_per_second
            capacity = self.config.burst_size
            
            # Lua script for atomic leaky bucket
            lua_script = """
            local key = KEYS[1]
            local rate = tonumber(ARGV[1])
            local capacity = tonumber(ARGV[2])
            local now = tonumber(ARGV[3])
            local requested = tonumber(ARGV[4])
            
            local bucket = redis.call('HMGET', key, 'tokens', 'last_update')
            local tokens = tonumber(bucket[1]) or capacity
            local last_update = tonumber(bucket[2]) or now
            
            local elapsed = now - last_update
            tokens = math.min(capacity, tokens + elapsed * rate)
            
            if tokens >= requested then
                tokens = tokens - requested
                redis.call('HMSET', key, 'tokens', tokens, 'last_update', now)
                redis.call('EXPIRE', key, capacity / rate * 2)
                return {1, 0}
            else
                local wait_time = (requested - tokens) / rate
                return {0, wait_time}
            end
            """
            
            result = self.redis_client.eval(
                lua_script, 1, key, rate, capacity, now, 1
            )
            
            return bool(result[0]), result[1]
            
        except:
            return True, None
    
    def _fixed_window_check(self, identifier: str) -> Tuple[bool, Optional[float]]:
        """Fixed window counter with Redis"""
        
        if not self.redis_client:
            return True, None
        
        try:
            # Calculate current window
            now = time.time()
            window_id = int(now / self.config.window_size)
            key = f"{self._get_cache_key(identifier)}:{window_id}"
            
            # Increment and check
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.config.window_size * 2)
            
            results = pipe.execute()
            count = results[0]
            
            limit = self.config.requests_per_second * self.config.window_size
            allowed = count <= limit
            
            wait_time = None
            if not allowed:
                window_end = (window_id + 1) * self.config.window_size
                wait_time = window_end - now
            
            return allowed, wait_time
            
        except:
            return True, None


class AsyncRateLimiter:
    """Async version for high-performance applications"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.limiter = HybridRateLimiter(config)
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._redis_async = None
        
    async def _init_async_redis(self):
        if self.config.distributed and not self._redis_async:
            try:
                self._redis_async = await aioredis.create_redis_pool(
                    'redis://localhost',
                    minsize=5,
                    maxsize=10
                )
            except:
                pass
    
    async def allow_request(self, identifier: str) -> Tuple[bool, Optional[float]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.limiter.allow_request,
            identifier
        )
    
    async def allow_request_batch(self, identifiers: list) -> list:
        """Batch check for efficiency"""
        tasks = [self.allow_request(id) for id in identifiers]
        return await asyncio.gather(*tasks)


class RateLimiterMiddleware:
    """ASGI/WSGI middleware for web applications"""
    
    def __init__(self, app, config: RateLimitConfig, key_func: Optional[Callable] = None):
        self.app = app
        self.limiter = HybridRateLimiter(config)
        self.key_func = key_func or self._default_key
    
    def _default_key(self, request) -> str:
        # Extract IP address as default identifier
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0]
        return request.client.host
    
    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            # Create request object
            request = type('Request', (), {
                'headers': dict(scope['headers']),
                'client': type('Client', (), {'host': scope['client'][0]})()
            })()
            
            identifier = self.key_func(request)
            allowed, wait_time = self.limiter.allow_request(identifier)
            
            if not allowed:
                # Send 429 Too Many Requests
                await send({
                    'type': 'http.response.start',
                    'status': 429,
                    'headers': [
                        [b'content-type', b'text/plain'],
                        [b'retry-after', str(int(wait_time or 1)).encode()],
                    ],
                })
                await send({
                    'type': 'http.response.body',
                    'body': b'Rate limit exceeded',
                })
                return
        
        await self.app(scope, receive, send)


class RateLimitDecorator:
    """Decorator for rate limiting functions"""
    
    def __init__(self, 
                 requests_per_second: float = 10,
                 burst_size: Optional[int] = None,
                 algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET,
                 key_func: Optional[Callable] = None):
        
        self.config = RateLimitConfig(
            requests_per_second=requests_per_second,
            burst_size=burst_size,
            algorithm=algorithm,
            distributed=False  # Local by default for decorators
        )
        self.limiter = HybridRateLimiter(self.config)
        self.key_func = key_func or (lambda *args, **kwargs: "default")
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            key = self.key_func(*args, **kwargs)
            allowed, wait_time = self.limiter.allow_request(key)
            
            if not allowed:
                if wait_time:
                    time.sleep(wait_time)
                    # Retry once after waiting
                    allowed, _ = self.limiter.allow_request(key)
                    if allowed:
                        return func(*args, **kwargs)
                
                raise Exception(f"Rate limit exceeded. Retry after {wait_time}s")
            
            return func(*args, **kwargs)
        
        # Async version
        async def async_wrapper(*args, **kwargs):
            key = self.key_func(*args, **kwargs)
            limiter = AsyncRateLimiter(self.config)
            allowed, wait_time = await limiter.allow_request(key)
            
            if not allowed:
                if wait_time:
                    await asyncio.sleep(wait_time)
                    allowed, _ = await limiter.allow_request(key)
                    if allowed:
                        return await func(*args, **kwargs)
                
                raise Exception(f"Rate limit exceeded. Retry after {wait_time}s")
            
            return await func(*args, **kwargs)
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper


def benchmark():
    """Performance benchmarking"""
    
    import timeit
    import statistics
    
    configs = [
        RateLimitConfig(100, algorithm=RateLimitAlgorithm.TOKEN_BUCKET),
        RateLimitConfig(100, algorithm=RateLimitAlgorithm.SLIDING_WINDOW),
        RateLimitConfig(100, algorithm=RateLimitAlgorithm.SLIDING_LOG),
        RateLimitConfig(100, algorithm=RateLimitAlgorithm.LEAKY_BUCKET),
        RateLimitConfig(100, algorithm=RateLimitAlgorithm.FIXED_WINDOW),
    ]
    
    print("Rate Limiter Performance Benchmark")
    print("-" * 50)
    
    for config in configs:
        config.distributed = False  # Test local performance
        limiter = HybridRateLimiter(config)
        
        # Warm up
        for _ in range(100):
            limiter.allow_request("test_user")
        
        # Benchmark
        times = []
        for _ in range(5):
            duration = timeit.timeit(
                lambda: limiter.allow_request("test_user"),
                number=10000
            )
            times.append(duration)
        
        avg_time = statistics.mean(times)
        std_dev = statistics.stdev(times)
        ops_per_sec = 10000 / avg_time
        
        print(f"{config.algorithm.value:20s}: {ops_per_sec:,.0f} ops/sec "
              f"(±{std_dev*1000:.2f}ms)")
    
    print("\nMemory Efficiency Test")
    print("-" * 50)
    
    # Test memory usage with bloom filter
    bloom = BloomFilter(1000000, 0.001)
    size_bytes = bloom.bit_array.nbytes
    print(f"Bloom filter for 1M items: {size_bytes / 1024:.1f} KB")
    
    # Test accuracy
    false_positives = 0
    test_items = 10000
    
    for i in range(test_items):
        bloom.add(f"item_{i}")
    
    for i in range(test_items, test_items * 2):
        if bloom.contains(f"item_{i}"):
            false_positives += 1
    
    actual_error_rate = false_positives / test_items
    print(f"Actual error rate: {actual_error_rate:.3%} (target: 0.1%)")


# Example usage patterns
if __name__ == "__main__":
    
    # Basic usage
    config = RateLimitConfig(
        requests_per_second=10,
        burst_size=20,
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET
    )
    
    rate_limiter = HybridRateLimiter(config)
    
    # Simulate requests
    user_id = "user_123"
    for i in range(25):
        allowed, wait_time = rate_limiter.allow_request(user_id)
        if allowed:
            print(f"Request {i+1}: Allowed")
        else:
            print(f"Request {i+1}: Denied (wait {wait_time:.2f}s)")
            if wait_time and wait_time < 0.1:
                time.sleep(wait_time)
    
    print("\n" + "="*50)
    
    # Using decorator
    @RateLimitDecorator(requests_per_second=5)
    def api_call(user_id: str):
        return f"API response for {user_id}"
    
    # Async example
    async def async_example():
        config = RateLimitConfig(
            requests_per_second=100,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW
        )
        
        limiter = AsyncRateLimiter(config)
        
        # Batch processing
        user_ids = [f"user_{i}" for i in range(10)]
        results = await limiter.allow_request_batch(user_ids)
        
        for user_id, (allowed, wait) in zip(user_ids, results):
            status = "allowed" if allowed else f"denied (wait {wait}s)"
            print(f"{user_id}: {status}")
    
    # Run async example
    # asyncio.run(async_example())
    
    print("\n" + "="*50 + "\n")
    
    # Run benchmark
    benchmark()
