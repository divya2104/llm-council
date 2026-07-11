"""Self-check for jd_local_storage.py. Run directly: python -m backend.test_jd_local_storage"""

import shutil
import tempfile

from . import jd_config, jd_local_storage


def main():
    original_dir = jd_config.LOCAL_DRAFTS_DIR
    tmp_dir = tempfile.mkdtemp()
    jd_config.LOCAL_DRAFTS_DIR = tmp_dir
    try:
        _check_next_jd_number_increments_per_lob()
        _check_write_load_round_trip()
        _check_list_draft_files()
        _check_delete_draft()
        print("OK: jd_local_storage create/get/save/list/delete round-trip correctly")
    finally:
        jd_config.LOCAL_DRAFTS_DIR = original_dir
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _check_next_jd_number_increments_per_lob():
    assert jd_local_storage.next_jd_number("AMC") == "JD-AMC-LOCAL-1"
    assert jd_local_storage.next_jd_number("AMC") == "JD-AMC-LOCAL-2"
    assert jd_local_storage.next_jd_number("NBFC") == "JD-NBFC-LOCAL-1"


def _check_write_load_round_trip():
    draft = {"id": "abc123", "lob": "AMC", "status": "draft"}
    jd_local_storage.write_draft(draft)
    loaded = jd_local_storage.load_draft("abc123")
    assert loaded == draft, f"expected {draft}, got {loaded}"
    assert jd_local_storage.load_draft("does-not-exist") is None


def _check_list_draft_files():
    jd_local_storage.write_draft({"id": "d1", "lob": "AMC", "status": "draft"})
    jd_local_storage.write_draft({"id": "d2", "lob": "NBFC", "status": "draft"})
    ids = {d["id"] for d in jd_local_storage.list_draft_files()}
    assert {"abc123", "d1", "d2"} <= ids, f"missing drafts, got {ids}"


def _check_delete_draft():
    jd_local_storage.write_draft({"id": "to-delete", "lob": "AMC", "status": "draft"})
    assert jd_local_storage.delete_draft("to-delete") is True
    assert jd_local_storage.load_draft("to-delete") is None
    assert jd_local_storage.delete_draft("to-delete") is False


if __name__ == "__main__":
    main()
