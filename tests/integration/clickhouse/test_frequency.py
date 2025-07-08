import datetime as _dt

import pytest

from elastalert.elastalert import ElastAlerter
from elastalert.util import dt_to_ts


@pytest.mark.clickhouse_integration
def test_frequency_rule(clickhouse_client):
    # insert 10 error rows within 5 minutes
    now = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0)
    rows = [(now + _dt.timedelta(seconds=i), 'error') for i in range(10)]
    clickhouse_client.execute("INSERT INTO logs (ts, level) VALUES", rows)

    conf = {
        'backend': 'clickhouse',
        'ck_host': clickhouse_client.connection.host,
        'ck_port': clickhouse_client.connection.port,
        'ck_database': 'default',
        'run_every': {'minutes': 1},
        'writeback_index': 'wb',
        'buffer_time': {'minutes': 1},
    }

    rule = {
        'name': 'freq_test',
        'type': 'frequency',
        'table': 'logs',
        'timestamp_field': 'ts',
        'num_events': 5,
        'timeframe': {'minutes': 5},
        'filter': [{"term": {"level": "error"}}],
    }

    args = type('obj', (), {'config': None, 'verbose': False, 'debug': True, 'pin_rules': True, 'rule': None, 'timeout': _dt.timedelta(seconds=0), 'es_debug': False, 'es_debug_trace': None})

    ea = ElastAlerter(args)
    ea.rules = []
    ea.rules.append(ea.init_rule(rule))
    ea.conf.update(conf)

    # Run rule covering the inserted window
    end = now + _dt.timedelta(minutes=5)
    matches = ea.run_rule(ea.rules[0], end)
    assert matches >= 1