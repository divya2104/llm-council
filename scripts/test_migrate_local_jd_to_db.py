"""Self-check for migrate_local_jd_to_db.py's INSERT-arg construction.
Run directly: python scripts/test_migrate_local_jd_to_db.py
"""

import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_spec = importlib.util.spec_from_file_location(
    "migrate_local_jd_to_db",
    os.path.join(os.path.dirname(__file__), "migrate_local_jd_to_db.py"),
)
migrate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(migrate)


def main():
    draft = {
        "id": "abc123",
        "jd_number": "JD-AMC-LOCAL-1",
        "lob": "AMC",
        "status": "draft",
        "basics": {"poornata_position_title": "Fund Manager"},
        "sign_off": {"prepared_by_name": "Devanshi"},
        "linked_conversation_id": None,
        "created_at": "2026-07-12T10:00:00",
        "updated_at": "2026-07-12T11:00:00",
    }

    args = migrate._insert_args(draft, "JD-AMC-00042")

    assert args[0] == "abc123"
    assert args[1] == "JD-AMC-00042"
    assert args[2] == "AMC"
    assert args[3] == "draft"
    assert args[4] == "Fund Manager"
    assert args[5] == "Devanshi"
    assert args[6] is None
    assert args[9] == draft
    assert len(args) == 10

    print("OK: migration script builds INSERT args in the correct column order")


if __name__ == "__main__":
    main()
