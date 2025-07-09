import datetime as _dt

import pytest

from elastalert.datastores import get_datastore
from elastalert.ruletypes import SpikeRule

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


def _count(store, start, end):
    res = store.count(rule_config={
        "client_id": "C1",
        "filter": [{"query_string": {"query": "query_type:A"}}],
        "start": start,
        "end": end,
    })
    return res["count"]


def test_spike_alert(clickhouse_test_data, ck_store):
    now = _dt.datetime.utcnow().replace(tzinfo=_dt.timezone.utc)
    ref_start = now - _dt.timedelta(minutes=30)
    ref_end = now - _dt.timedelta(minutes=15)
    cur_start = ref_end
    cur_end = now

    # Build rule with count query
    rule_cfg = {
        "threshold_ref": 50,
        "spike_height": 5,
        "timeframe": _dt.timedelta(minutes=15),
        "spike_type": "up",
        "timestamp_field": "@timestamp",
        "use_count_query": True,
    }
    spike_rule = SpikeRule(rule_cfg)

    ref_cnt = _count(ck_store, ref_start, ref_end)
    spike_rule.add_count_data({ref_end: ref_cnt})
    cur_cnt = _count(ck_store, cur_start, cur_end)
    spike_rule.add_count_data({cur_end: cur_cnt})

    assert len(spike_rule.matches) == 1, "Should alert when spike conditions met"


def test_spike_no_alert(clickhouse_test_data, ck_store):
    now = _dt.datetime.utcnow().replace(tzinfo=_dt.timezone.utc)
    # Use windows both older and same counts
    ref_start = now - _dt.timedelta(minutes=45)
    ref_end = now - _dt.timedelta(minutes=30)
    cur_start = ref_end
    cur_end = now - _dt.timedelta(minutes=15)

    rule_cfg = {
        "threshold_ref": 50,
        "spike_height": 5,
        "timeframe": _dt.timedelta(minutes=15),
        "spike_type": "up",
        "timestamp_field": "@timestamp",
        "use_count_query": True,
    }
    spike_rule = SpikeRule(rule_cfg)

    ref_cnt = _count(ck_store, ref_start, ref_end)
    spike_rule.add_count_data({ref_end: ref_cnt})
    cur_cnt = _count(ck_store, cur_start, cur_end)
    spike_rule.add_count_data({cur_end: cur_cnt})

    assert len(spike_rule.matches) == 0, "Should NOT alert when conditions not met"