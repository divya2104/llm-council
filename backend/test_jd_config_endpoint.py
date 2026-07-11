"""Self-check that /api/jd/config exposes db_available. Run directly: python -m backend.test_jd_config_endpoint"""

import asyncio
from unittest.mock import patch

from . import jd


async def main():
    with patch("backend.jd.jd_db.is_db_available", return_value=False):
        config = await jd.get_jd_config()
    assert config["db_available"] is False

    with patch("backend.jd.jd_db.is_db_available", return_value=True):
        config = await jd.get_jd_config()
    assert config["db_available"] is True

    print("OK: /api/jd/config exposes db_available correctly")


if __name__ == "__main__":
    asyncio.run(main())
