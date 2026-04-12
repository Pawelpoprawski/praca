"""Rate limiter configuration using slowapi."""
import logging
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Allow disabling rate limiting in tests via RATELIMIT_ENABLED=false
_ratelimit_enabled = os.getenv("RATELIMIT_ENABLED", "true").lower() not in ("false", "0", "no")

# Redis storage if available, otherwise in-memory
_storage_uri = None
if settings.REDIS_URL:
    _storage_uri = settings.REDIS_URL
    logger.info("Rate limiter: using Redis storage")
else:
    logger.info("Rate limiter: using in-memory storage")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],
    storage_uri=_storage_uri,
)

# Override enabled state as a proper Python bool so it's never misinterpreted
# as truthy string by slowapi's starlette Config. This must be set after
# Limiter.__init__ which calls get_app_config() and overwrites it.
limiter.enabled = _ratelimit_enabled
