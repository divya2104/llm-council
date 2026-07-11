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


class _FakeAcquireCtxFailingExecute:
    """Variant that raises on execute() to simulate schema bootstrap failure."""
    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def execute(self, *a, **kw):
        raise RuntimeError("simulated schema bootstrap failure")


class _FakePool:
    def acquire(self):
        return _FakeAcquireCtx()

    async def close(self):
        pass


class _FakePoolWithCloseTracking:
    """Variant that tracks whether close() was called."""
    def __init__(self):
        self.close_called = False

    def acquire(self):
        return _FakeAcquireCtxFailingExecute()

    async def close(self):
        self.close_called = True


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


async def _check_closes_pool_on_schema_bootstrap_failure():
    """Test the specific branch where create_pool() succeeds but schema bootstrap fails.

    This exercises the except block's cleanup path:
        if _pool is not None:
            await _pool.close()
    """
    jd_config.DATABASE_URL = "postgresql://fake"

    fake_pool = _FakePoolWithCloseTracking()

    async def returns_pool(*args, **kwargs):
        return fake_pool

    with patch("backend.jd_db.asyncpg.create_pool", side_effect=returns_pool):
        await jd_db.init_pool()  # must not raise despite schema bootstrap failure

    assert fake_pool.close_called is True, "Pool.close() was not called on schema failure"
    assert jd_db.is_db_available() is False, "is_db_available() should be False after schema failure"


async def main():
    await _check_falls_back_on_connection_failure()
    await _check_succeeds_when_connection_works()
    await _check_falls_back_when_url_unset()
    await _check_closes_pool_on_schema_bootstrap_failure()
    print("OK: init_pool() falls back to local mode on any failure, cleans up pool on schema bootstrap failure, succeeds when DB reachable")


if __name__ == "__main__":
    asyncio.run(main())
