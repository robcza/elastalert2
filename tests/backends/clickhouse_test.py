import datetime

import pytest

from elastalert.backends.clickhouse import ClickHouseClient


class _FakeCHDriver:
    """Simple stand-in for clickhouse_driver.Client used during unit tests."""

    def __init__(self, rows):
        self._rows = rows

    # The real driver returns list[dict]
    def query_dict(self, sql):  # noqa: D401  # simple stub
        return self._rows

    def execute_iter(self, sql):
        yield [len(self._rows)]


class DummyClickHouseClient(ClickHouseClient):
    """ClickHouseClient variant that avoids real network connections."""

    def __init__(self, rows):
        # Bypass parent initialisation (which connects to DB)
        self.client = _FakeCHDriver(rows)
        self.table = "passivedns.passivedns_v2"

    # Expose helper publicly for testing
    def parse_query(self, query: str) -> str:  # pragma: no cover – convenience
        return self._parse_query_string(query)


@pytest.fixture()
def sample_rows():
    ts = datetime.datetime(2025, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    return [
        {"timestamp": ts, "client_id": "194", "query_type": "MX"},
        {"timestamp": ts, "client_id": "194", "query_type": "MX"},
        {"timestamp": ts, "client_id": "42", "query_type": "A"},
    ]


def _build_body():
    return {
        "query": {
            "bool": {
                "filter": {
                    "bool": {
                        "must": [
                            {"query_string": {"query": "client_id: 194 AND query_type: MX"}},
                            {
                                "range": {
                                    "timestamp": {
                                        "gt": "2024-12-31T23:00:00Z",
                                        "lte": "2025-01-01T01:00:00Z",
                                    }
                                }
                            },
                        ]
                    }
                }
            }
        },
        "sort": [{"timestamp": {"order": "asc"}}],
    }


def test_search_and_count(sample_rows):
    cli = DummyClickHouseClient(sample_rows)
    body = _build_body()

    # search
    result = cli.search(body=body)
    assert result["hits"]["total"]["value"] == len(sample_rows)
    assert len(result["hits"]["hits"]) == len(sample_rows)

    # count
    c = cli.count(body=body)
    assert c["count"] == len(sample_rows)


def test_query_string_translator():
    cli = DummyClickHouseClient([])
    translated = cli.parse_query("client_id: 42 AND NOT answer: (NXDOMAIN OR REFUSED)")
    # Ensure translation contains expected SQL snippets
    assert "client_id" in translated
    assert "NOT" in translated.upper()