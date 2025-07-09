import datetime as _dt

import pytest

from elastalert.datastores import get_datastore
from elastalert.ruletypes import FrequencyRule

# Mark whole module as clickhouse specific
pytestmark = pytest.mark.clickhouse


CFG_BASE = {
    "backend": "clickhouse",
    "ck_host": "localhost",
    "ck_port": 9000,
    "ck_database": "passivedns",
    "ck_table": "passivedns_v2",
    "client_id": "C1",
}


@pytest.fixture(scope="module")
def ck_store():
    yield get_datastore(CFG_BASE)


def _query(store, start, end):
    result = store.search(rule_config={
        "client_id": "C1",
        "filter": [{"query_string": {"query": "query_type:A"}}],
        "start": start,
        "end": end,
    })
    return result["hits"]["hits"]


def test_frequency_positive(clickhouse_test_data, ck_store):
    now = _dt.datetime.utcnow().replace(tzinfo=_dt.timezone.utc)
    start = now - _dt.timedelta(minutes=15)
    events = _query(ck_store, start, now)

    rule_cfg = {
        "num_events": 100,
        "timeframe": _dt.timedelta(minutes=15),
        "timestamp_field": "@timestamp",
    }
    freq_rule = FrequencyRule(rule_cfg)
    freq_rule.add_data(events)
    assert len(freq_rule.matches) == 1, "Should alert when >= num_events"


def test_frequency_negative(clickhouse_test_data, ck_store):
    now = _dt.datetime.utcnow().replace(tzinfo=_dt.timezone.utc)
    # Window immediately before positive one
    end = now - _dt.timedelta(minutes=30)
    start = end - _dt.timedelta(minutes=15)
    events = _query(ck_store, start, end)

    rule_cfg = {
        "num_events": 100,
        "timeframe": _dt.timedelta(minutes=15),
        "timestamp_field": "@timestamp",
    }
    freq_rule = FrequencyRule(rule_cfg)
    freq_rule.add_data(events)
    assert len(freq_rule.matches) == 0, "Should NOT alert when below threshold"