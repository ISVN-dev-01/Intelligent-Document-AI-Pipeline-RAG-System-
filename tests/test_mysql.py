"""Opt-in: set TEST_MYSQL_DATABASE to an EMPTY dedicated test schema before running."""
import os

import pytest
from sqlalchemy import text

from database.connection import create_database


@pytest.mark.mysql
@pytest.mark.skipif(not os.getenv("TEST_MYSQL_DATABASE"), reason="No MySQL test database configured")
def test_mysql_schema(settings):
    settings.db_backend = "mysql"
    settings.mysql_database = os.environ["TEST_MYSQL_DATABASE"]
    engine, _ = create_database(settings)
    try:
        with engine.connect() as connection:
            for table in ("documents", "queries", "query_sources"):
                assert connection.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() >= 0
    finally:
        engine.dispose()
