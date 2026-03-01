"""Redis caching helpers for cleaned DataFrames."""

import redis
import pandas as pd

from app.config import settings

_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

_TTL = 3600  # 1 hour


def _key(job_id: int) -> str:
    return f"cleaned_df:{job_id}"


def cache_dataframe(job_id: int, df: pd.DataFrame) -> None:
    """Serialise DataFrame to JSON and store in Redis."""
    _client.setex(_key(job_id), _TTL, df.to_json(orient="records", date_format="iso"))


def get_cached_dataframe(job_id: int) -> pd.DataFrame | None:
    """Return cached DataFrame or None if missing / expired."""
    raw = _client.get(_key(job_id))
    if raw is None:
        return None
    return pd.read_json(raw, orient="records")


def delete_cached_dataframe(job_id: int) -> None:
    """Remove a cached DataFrame."""
    _client.delete(_key(job_id))
