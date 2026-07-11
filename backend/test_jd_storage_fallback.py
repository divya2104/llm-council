"""Self-check for jd_storage.py's DB/local dispatch logic. Run directly: python -m backend.test_jd_storage_fallback"""

import asyncio
import shutil
import tempfile
from unittest.mock import patch

from . import jd_config, jd_storage


async def main():
    original_dir = jd_config.LOCAL_DRAFTS_DIR
    tmp_dir = tempfile.mkdtemp()
    jd_config.LOCAL_DRAFTS_DIR = tmp_dir
    try:
        with patch("backend.jd_db.is_db_available", return_value=False):
            await _check_full_round_trip_via_local_storage()
        print("OK: jd_storage dispatches to local storage end-to-end when DB is unavailable")
    finally:
        jd_config.LOCAL_DRAFTS_DIR = original_dir
        shutil.rmtree(tmp_dir, ignore_errors=True)


async def _check_full_round_trip_via_local_storage():
    draft = await jd_storage.create_jd_draft("test-id-1", "AMC")
    assert draft["jd_number"] == "JD-AMC-LOCAL-1", draft["jd_number"]

    loaded = await jd_storage.get_jd_draft("test-id-1")
    assert loaded["id"] == "test-id-1"

    updated = await jd_storage.update_jd_step("test-id-1", "purpose", {"text": "hello"})
    assert updated["purpose"]["text"] == "hello"

    drafts = await jd_storage.list_jd_drafts()
    assert any(d["id"] == "test-id-1" for d in drafts)

    sample = await jd_storage.get_sample_template("AMC")
    assert sample is None  # not cached in local mode

    deleted = await jd_storage.delete_jd_draft("test-id-1")
    assert deleted is True
    assert await jd_storage.get_jd_draft("test-id-1") is None


if __name__ == "__main__":
    asyncio.run(main())
