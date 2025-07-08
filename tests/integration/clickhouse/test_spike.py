import datetime as _dt
from random import randint

import pytest

from elastalert.elastalert import ElastAlerter


@pytest.mark.clickhouse_integration
def test_spike_rule(clickhouse_client):
    """Insert reference data + spike burst and ensure SpikeRule matches."""
    now = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0)

    # Reference window: 60 minutes, 1 event per minute
    ref_rows = [(now - _dt.timedelta(minutes=60) + _dt.timedelta(minutes=i), 'error') for i in range(60)]

    # Spike window: 10 minutes immediately after reference, 4 events per minute
    spike_start = now
    spike_rows = [
        (spike_start + _dt.timedelta(minutes=i), 'error')
        for i in range(10)
        for _ in range(4)
    ]

    clickhouse_client.execute("INSERT INTO logs (ts, level) VALUES", ref_rows + spike_rows)

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
        'name': 'spike_test',
        'type': 'spike',
        'table': 'logs',
        'timestamp_field': 'ts',
        'spike_height': 3,
        'spike_type': 'up',
        'timeframe': {'minutes': 10},
        'use_count_query': True,
        'filter': [{"term": {"level": "error"}}],
    }

    Args = type('Args', (), {})
    args = Args()
    args.config = None
    args.verbose = False
    args.debug = True  # prevent actual alerts
    args.pin_rules = True
    args.rule = None
    args.timeout = _dt.timedelta(seconds=0)
    args.es_debug = False
    args.es_debug_trace = None

    ea = ElastAlerter(args)
    ea.rules = []
    ea.conf.update(conf)
    ea.rules.append(ea.init_rule(rule))

    matches = ea.run_rule(ea.rules[0], spike_start + _dt.timedelta(minutes=10))
    assert matches >= 1, "SpikeRule should have matched the spike window"