from importlib import import_module

# Export ClickHouseClient to be importable via elastalert.backends
ClickHouseClient = import_module('.clickhouse', package=__name__).ClickHouseClient