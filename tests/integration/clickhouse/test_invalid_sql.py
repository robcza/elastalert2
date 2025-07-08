import pytest


@pytest.mark.clickhouse_integration
def test_invalid_sql(clickhouse_client):
    from elastalert.datastores.clickhouse import ClickHouseStore

    conf = {
        'ck_host': clickhouse_client.connection.host,
        'ck_port': clickhouse_client.connection.port,
        'ck_database': 'default',
    }

    store = ClickHouseStore(conf)
    with pytest.raises(Exception):
        store.search('SELECT non_existing FROM table')