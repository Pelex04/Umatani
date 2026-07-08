"""
Shared rate limiter instance.

Must be a SINGLE instance imported everywhere — both by app.main (for
middleware/exception-handler wiring) and by route modules (for the
@limiter.limit decorator). Using separate Limiter() instances in
different files creates disjoint in-memory rate-limit state, silently
defeating the limit.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

settings = get_settings()

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT])
