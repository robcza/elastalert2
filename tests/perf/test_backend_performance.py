import os
import time
import datetime as _dt

import pytest

try:
    from clickhouse_driver import Client as CKClient
except ImportError:
    CKClient = None  # type: ignore

from elastalert.datastores.elastic import ElasticSearchStore
from elastalert.datastores.clickhouse import ClickHouseStore

PERF_ENV = os.environ.get("PERF_TESTS")

pytestmark = pytest.mark.skipif(not PERF_ENV, reason="perf tests disabled")


def _generate_ck_data(client, rows):
    client.execute("DROP TABLE IF EXISTS perf")
    client.execute("CREATE TABLE perf(ts DateTime, level String) ENGINE=MergeTree() ORDER BY ts")
    base = _dt.datetime(2021, 1, 1, tzinfo=_dt.timezone.utc)
    data = [(base + _dt.timedelta(seconds=i), 'info') for i in range(rows)]
    client.execute("INSERT INTO perf (ts, level) VALUES", data)


def test_frequency_throughput_clickhouse_vs_es(tmp_path):
    rows = 10000

    # ClickHouse
    ck_client = None
    ck_elapsed = None
    if CKClient is not None:
        try:
            ck_client = CKClient(host="localhost", port=9000)
            ck_client.execute("SELECT 1")
            _generate_ck_data(ck_client, rows)
            store = ClickHouseStore({'ck_host': 'localhost', 'ck_port': 9000})
            start = time.time()
            store.count({'table': 'perf'}, 0, 1)
            ck_elapsed = time.time() - start
        except Exception:
            ck_client = None

    # Elasticsearch mock (in-memory, just timing call overhead)
    start = time.time()
    es_store = ElasticSearchStore({'es_host': 'localhost', 'es_port': 9200})
    es_store.count({'index': 'perf'}, 0, 1)
    es_elapsed = time.time() - start

    if ck_elapsed is not None:
        print(f"ClickHouse count {rows} rows: {ck_elapsed:.4f}s | ES stub: {es_elapsed:.4f}s")