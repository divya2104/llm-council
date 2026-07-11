"""Self-check for jd_db.init_pool()'s fallback-on-failure behavior. Run directly: python -m backend.test_jd_db_fallback"""

import asyncio
from unittest.mock import patch

from . import jd_config, jd_db


class _FakeAcquireCtx:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def execute(self, *a, **kw):
        pass


class _FakePool:
    def acquire(self):
        return _FakeAcquireCtx()

    async def close(self):
        pass


async def _check_falls_back_on_connection_failure():
    jd_config.DATABASE_URL = "postgresql://fake"

    async def always_fails(*args, **kwargs):
        raise ConnectionResetError("simulated reset")

    with patch("backend.jd_db.asyncpg.create_pool", side_effect=always_fails):
        await jd_db.init_pool()  # must not raise

    assert jd_db.is_db_available() is False


async def _check_succeeds_when_connection_works():
    jd_config.DATABASE_URL = "postgresql://fake"

    async def succeeds(*args, **kwargs):
        return _FakePool()

    with patch("backend.jd_db.asyncpg.create_pool", side_effect=succeeds):
        await jd_db.init_pool()

    assert jd_db.is_db_available() is True
    await jd_db.close_pool()


async def _check_falls_back_when_url_unset():
    jd_config.DATABASE_URL = None
    await jd_db.init_pool()
    assert jd_db.is_db_available() is False


async def main():
    await _check_falls_back_on_connection_failure()
    await _check_succeeds_when_connection_works()
    await _check_falls_back_when_url_unset()
    print("OK: init_pool() falls back to local mode on any failure, succeeds when DB reachable")


if __name__ == "__main__":
    asyncio.run(main())
