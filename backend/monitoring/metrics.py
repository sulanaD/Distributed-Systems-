"""
Prometheus metrics for banking system monitoring
"""
from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# Business metrics
transactions_total = Counter(
    'banking_transactions_total',
    'Total number of transactions',
    ['status']  # completed, failed
)

transaction_amount = Histogram(
    'banking_transaction_amount',
    'Transaction amounts',
    buckets=[10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000]
)

accounts_total = Gauge(
    'banking_accounts_total',
    'Total number of active accounts'
)

users_total = Gauge(
    'banking_users_total',
    'Total number of registered users'
)

# Database metrics
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation']  # select, insert, update, delete
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation']
)

db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections'
)

# Cache metrics
cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'result']  # operation: get/set/delete, result: hit/miss/success
)

cache_hit_ratio = Gauge(
    'cache_hit_ratio',
    'Cache hit ratio (0-1)'
)

# Kafka metrics
kafka_messages_produced_total = Counter(
    'kafka_messages_produced_total',
    'Total Kafka messages produced',
    ['topic', 'status']  # status: success/failure
)

kafka_producer_errors_total = Counter(
    'kafka_producer_errors_total',
    'Total Kafka producer errors',
    ['topic']
)

# Authentication metrics
auth_attempts_total = Counter(
    'auth_attempts_total',
    'Total authentication attempts',
    ['result']  # success, failure, invalid_token
)

active_sessions = Gauge(
    'auth_active_sessions',
    'Number of active user sessions'
)

# Error metrics
errors_total = Counter(
    'errors_total',
    'Total application errors',
    ['error_type', 'endpoint']
)

# System info
app_info = Info(
    'banking_app',
    'Banking application information'
)

# Initialize app info
app_info.info({
    'version': '2.0.0',
    'service': 'banking-api',
    'environment': 'production'
})

# Helper decorators
def track_time(metric_histogram):
    """Decorator to track execution time"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metric_histogram.observe(duration)
        return wrapper
    return decorator

def track_db_query(operation: str):
    """Decorator to track database queries"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            db_queries_total.labels(operation=operation).inc()
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                db_query_duration_seconds.labels(operation=operation).observe(duration)
        return wrapper
    return decorator

# Cache tracking helpers
_cache_hits = 0
_cache_misses = 0

def record_cache_hit():
    """Record a cache hit"""
    global _cache_hits
    _cache_hits += 1
    cache_operations_total.labels(operation='get', result='hit').inc()
    _update_cache_hit_ratio()

def record_cache_miss():
    """Record a cache miss"""
    global _cache_misses
    _cache_misses += 1
    cache_operations_total.labels(operation='get', result='miss').inc()
    _update_cache_hit_ratio()

def _update_cache_hit_ratio():
    """Update cache hit ratio gauge"""
    total = _cache_hits + _cache_misses
    if total > 0:
        ratio = _cache_hits / total
        cache_hit_ratio.set(ratio)
