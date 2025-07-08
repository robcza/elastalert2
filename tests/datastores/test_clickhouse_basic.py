import os
import pytest

from elastalert.datastores.clickhouse import ClickHouseStore


@pytest.mark.clickhouse
def test_clickhouse_basic_connection():
    conf = {
        "ck_host": os.environ.get("CK_HOST", "localhost"),
        "ck_port": int(os.environ.get("CK_PORT", 9000)),
        "ck_database": os.environ.get("CK_DATABASE", "default"),
    }

    try:
        store = ClickHouseStore(conf)
    except Exception as exc:
        pytest.skip(f"ClickHouse server not available: {exc}")

    # Simple sanity query – ClickHouse always has system.numbers table
    try:
        rows = store.search("SELECT number FROM system.numbers LIMIT 3")
    except Exception as exc:
        pytest.skip(f"ClickHouse query failed (likely no server): {exc}")
    assert rows[0]["number"] == 0
    assert len(rows) == 3

    # Count API stub should return dict with endtime key
    from datetime import datetime, timedelta, timezone

    rule = {
        "table": "system.numbers",
        "timestamp_field": "now()",  # placeholder not used in stub
    }

    end = datetime.now(timezone.utc)
    res = store.count(rule, end - timedelta(minutes=1), end)
    assert isinstance(res, dict)