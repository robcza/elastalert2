import os
import time
from contextlib import contextmanager

import pytest

try:
    from clickhouse_driver import Client
except ImportError:  # pragma: no cover
    Client = None  # type: ignore

CLICKHOUSE_HOST = os.environ.get("CK_HOST", "localhost")
CLICKHOUSE_PORT = int(os.environ.get("CK_PORT", 9000))


@contextmanager
def _maybe_clickhouse():
    """Yield Client if ClickHouse is reachable, else None."""
    if Client is None:
        yield None
        return
    try:
        cl = Client(host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT, database="default")
        # Ping
        cl.execute("SELECT 1")
        yield cl
    except Exception:
        yield None
    finally:
        try:
            cl.disconnect()
        except Exception:  # noqa: PIE786
            pass


@pytest.fixture(scope="session")
def clickhouse_client():
    with _maybe_clickhouse() as cli:
        if cli is None:
            pytest.skip("ClickHouse not available on host")
        # Ensure test table exists
        cli.execute(
            "CREATE TABLE IF NOT EXISTS logs (ts DateTime, level String) ENGINE=MergeTree() ORDER BY ts"
        )
        yield cli
        # Cleanup
        cli.execute("DROP TABLE IF EXISTS logs")