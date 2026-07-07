"""Postgres connection pool + schema bootstrap for JD Creator storage."""

import json
import asyncpg
from . import jd_config

_pool: asyncpg.Pool = None


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
    """Create the connection pool and bootstrap the schema. Called on app startup."""
    global _pool
    if not jd_config.DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. JD Creator storage requires a Postgres "
            "connection string in .env (see .env.example)."
        )
    _pool = await asyncpg.create_pool(
        jd_config.DATABASE_URL, min_size=1, max_size=5, init=_init_connection
    )
    async with _pool.acquire() as conn:
        await conn.execute(_SCHEMA)


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
