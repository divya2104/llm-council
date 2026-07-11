"""One-off migration: push locally-saved JD drafts (created while Postgres was
unreachable) into the real database, assigning each a proper jd_number.

Run manually once IT confirms the Postgres connection is fixed:
    uv run python scripts/migrate_local_jd_to_db.py

Safe to run more than once — migrated drafts are removed from the local
fallback directory as they're migrated, so a second run just finds nothing
left to do.
"""

import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import jd_db, jd_local_storage, jd_storage


def _insert_args(draft: dict, new_number: str) -> tuple:
    """Build the positional args for the jd_drafts INSERT, in column order."""
    return (
        draft["id"], new_number, draft["lob"], draft["status"],
        jd_storage._draft_title(draft),
        draft.get("sign_off", {}).get("prepared_by_name", ""),
        draft.get("linked_conversation_id"),
        datetime.fromisoformat(draft["created_at"]),
        datetime.fromisoformat(draft["updated_at"]),
        draft,
    )


async def main():
    await jd_db.init_pool()
    if not jd_db.is_db_available():
        print("Still can't reach Postgres — nothing migrated. Fix the connection first.")
        return

    local_drafts = jd_local_storage.list_draft_files()
    if not local_drafts:
        print("No locally-saved drafts to migrate.")
        return

    pool = jd_db.get_pool()
    for draft in local_drafts:
        old_number = draft.get("jd_number")
        new_number = await jd_storage._next_jd_number(draft["lob"])

        await pool.execute(
            """
            INSERT INTO jd_drafts
                (id, jd_number, lob, status, title, prepared_by_name,
                 linked_conversation_id, created_at, updated_at, data)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            *_insert_args(draft, new_number),
        )
        jd_local_storage.delete_draft(draft["id"])
        print(f"Migrated {old_number} -> {new_number} ({draft['id']})")

    print(f"Done. Migrated {len(local_drafts)} draft(s).")


if __name__ == "__main__":
    asyncio.run(main())
