"""Postgres connection pool + schema bootstrap for JD Creator storage."""

import json
import asyncpg
from . import jd_config

_pool: asyncpg.Pool = None
_db_available = False


async def _init_connection(conn):
    """Auto-encode/decode Python dicts <-> jsonb for every connection in the pool."""
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jd_drafts (
    id TEXT PRIMARY KEY,
    jd_number TEXT UNIQUE,
    lob TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    title TEXT,
    prepared_by_name TEXT,
    linked_conversation_id TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    data JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jd_drafts_status ON jd_drafts(status);
CREATE INDEX IF NOT EXISTS idx_jd_drafts_lob ON jd_drafts(lob);

CREATE TABLE IF NOT EXISTS jd_number_counters (
    lob TEXT PRIMARY KEY,
    last_value INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS jd_sample_templates (
    lob TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    content BYTEA NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
"""


async def init_pool():
    """Try to create the connection pool and bootstrap the schema. Called on app startup.

    Does NOT raise if Postgres is unreachable — sets is_db_available() to
    False instead, so the app boots in local-storage fallback mode (see
    jd_local_storage.py and JD_CREATOR_PHASE1_WINDOWS_SSL_DEBUG.md). Catches
    broadly (not just OSError) since the goal is "any connection problem ->
    fall back," whether that's a network block, bad credentials, or a typo
    in DATABASE_URL.
    """
    # ponytail: availability is decided once at startup, no background
    # reconnect loop. If Postgres comes back mid-session, restart the
    # process — add a periodic recheck only if that restart step becomes
    # a real pain point in practice.
    global _pool, _db_available
    if not jd_config.DATABASE_URL:
        print("[jd_db] DATABASE_URL not set — running in local-storage fallback mode.")
        _db_available = False
        return
    try:
        _pool = await asyncpg.create_pool(
            jd_config.DATABASE_URL, min_size=1, max_size=5, init=_init_connection, timeout=15
        )
        async with _pool.acquire() as conn:
            await conn.execute(_SCHEMA)
        _db_available = True
    except Exception as e:
        print(f"[jd_db] Could not connect to Postgres ({e!r}) — running in local-storage fallback mode.")
        _pool = None
        _db_available = False


def is_db_available() -> bool:
    return _db_available


async def close_pool():
    """Close the connection pool. Called on app shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("JD DB pool not initialized — did the app startup hook run?")
    return _pool
