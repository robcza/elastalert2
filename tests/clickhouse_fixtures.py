import datetime as _dt
import os
from typing import Iterator, List, Tuple

import pytest

try:
    from clickhouse_driver import Client  # type: ignore
except ImportError as exc:  # pragma: no cover
    pytest.skip("clickhouse-driver not installed", allow_module_level=True)


CK_HOST = os.getenv("CK_HOST", "localhost")
CK_PORT = int(os.getenv("CK_PORT", "9000"))
CK_DATABASE = os.getenv("CK_DATABASE", "passivedns")
CK_TABLE = os.getenv("CK_TABLE", "passivedns_v2")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _client_available() -> Client | None:
    try:
        cl = Client(host=CK_HOST, port=CK_PORT, settings={"use_numpy": False})
        cl.execute("SELECT 1")
        return cl
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def ck_client() -> Iterator[Client]:
    """Return live ClickHouse client or skip the session."""
    client = _client_available()
    if client is None:
        pytest.skip("ClickHouse service not available on localhost:9000", allow_module_level=True)
    yield client
    client.disconnect()


@pytest.fixture(scope="session", autouse=True)
def clickhouse_schema(ck_client: Client):
    """Create database and table schema used by tests."""
    ck_client.execute(f"CREATE DATABASE IF NOT EXISTS {CK_DATABASE}")
    ck_client.execute(f"DROP TABLE IF EXISTS {CK_DATABASE}.{CK_TABLE}")
    ck_client.execute(
        f"""
        CREATE TABLE {CK_DATABASE}.{CK_TABLE} (
            timestamp    DateTime64(6, 'UTC'),
            client_id    LowCardinality(String),
            query_type   LowCardinality(String),
            rate_limited Bool
        ) ENGINE = MergeTree
        PARTITION BY toYYYYMMDD(timestamp)
        ORDER BY (client_id, toUnixTimestamp(timestamp))
        """
    )


@pytest.fixture(scope="session")
def clickhouse_test_data(ck_client: Client, clickhouse_schema):
    """Insert synthetic rows for frequency and spike rule scenarios."""
    now = _dt.datetime.utcnow().replace(tzinfo=_dt.timezone.utc)
    rows: List[Tuple] = []

    # ------------------ Frequency Scenario ------------------
    # Positive case: 200 rows within last 15 min
    for i in range(200):
        ts = now - _dt.timedelta(minutes=14, seconds=59 - i)
        rows.append((ts, "C1", "A", 0))
    # Negative case: 50 rows in older window (older than 15 min)
    for i in range(50):
        ts = now - _dt.timedelta(minutes=16, seconds=i)
        rows.append((ts, "C1", "A", 0))

    # ------------------ Spike Scenario ------------------
    # Reference window: -30 min to -15 min => 100 rows
    ref_start = now - _dt.timedelta(minutes=30)
    for i in range(100):
        ts = ref_start + _dt.timedelta(seconds=i)
        rows.append((ts, "C1", "A", 0))
    # Current window: -15 min to now => 600 rows
    cur_start = now - _dt.timedelta(minutes=15)
    for i in range(600):
        ts = cur_start + _dt.timedelta(seconds=i)
        rows.append((ts, "C1", "A", 0))

    ck_client.execute(
        f"INSERT INTO {CK_DATABASE}.{CK_TABLE} (timestamp, client_id, query_type, rate_limited) VALUES",
        rows,
    )

    yield

    # Cleanup after session (optional)
    ck_client.execute(f"DROP TABLE IF EXISTS {CK_DATABASE}.{CK_TABLE}")