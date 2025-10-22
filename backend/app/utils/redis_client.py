import redis
from backend.app.config.settings import get_settings

settings = get_settings()


def get_redis_client():
    if settings.enable_redis_caching:
        return redis.from_url(settings.redis_url)
    return None


redis_client = get_redis_client()
