"""Shared slowapi Limiter instance.

In multi-worker (Gunicorn > 1 worker) deployments, configure Redis via
`Limiter(storage_uri='redis://...')` — in-memory per-worker isn't shared and
rate limits will be per-worker not global.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
