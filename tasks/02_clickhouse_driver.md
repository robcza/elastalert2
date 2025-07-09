# Task 02: ClickHouse Driver

## Goal
Provide a production-ready **ClickHouse datastore implementation** using the official [`clickhouse-driver`](https://github.com/mymarilyn/clickhouse-driver) so that ElastAlert 2 can query ClickHouse tables transparently.

## Context (UPDATED)
* First production table: `passivedns.passivedns_v2`  
  `timestamp DateTime64(6, 'UTC')`, `client_id LowCardinality(String)`, `query_type LowCardinality(String)`, `rate_limited Bool`, …
* Primary key: `(client_id, toUnixTimestamp(timestamp))`.
* Rule YAML must remain unchanged apart from:
  ```yaml
  backend: clickhouse
  ck_host: 127.0.0.1  # etc.
  ```

## Deliverables
1. `ClickHouseStore` class in `elastalert/datastores/clickhouse.py` implementing `BaseDataStore`.
2. Connection helper using `clickhouse_driver.Client` with parameters from config; default `database = passivedns`.
3. SQL helper functions:
   * Build **event selection** query matching existing ES document semantics – must alias `timestamp → "@timestamp"` in result dicts.
   * Build **count** query for frequency & spike rule types.
4. Translation layer mapping ES-style `filter:` blocks (currently handled by `ElasticsearchFilter`) to ClickHouse `WHERE` clauses.

## Specification Details
* Column mapping constants:
  | Rule concept | ClickHouse column |
  |--------------|------------------|
  | timestamp    | `timestamp`      |
  | client_id    | `client_id`      |
  | QUERY_TYPE   | `query_type`     |
* `ClickHouseStore.search` **must return** `list[dict]` with keys identical to Elasticsearch hits: at minimum `"@timestamp"` holding the ISO-string of `timestamp`.
* **SQL templates** (placeholders rendered with `str.format`):
  ```sql
  -- Full row fetch (frequency rule)
  SELECT *
  FROM {ck_database}.{ck_table}
  WHERE client_id = %(client_id)s
    AND {additional_filters}
    AND timestamp >= %(start)s
    AND timestamp <  %(end)s
  ORDER BY timestamp;

  -- Aggregation count (frequency / spike)
  SELECT count() AS cnt
  FROM {ck_database}.{ck_table}
  WHERE client_id = %(client_id)s
    AND timestamp BETWEEN %(start)s AND %(end)s
    AND {additional_filters};
  ```
* `{additional_filters}` are rendered from rule´s `filter:` section:
  * `query_string` example `"query_type:A"` → `query_type = 'A'`.
  * Empty string filters are ignored.

## Code Checklist
- [ ] Add `clickhouse-driver` pin to `requirements.txt` & `requirements-dev.txt`.
- [ ] Implement safe connection pooling with retry/back-off.
- [ ] Implement `ClickHouseStore` methods: `search`, `count`, `iter_hits` (streaming cursor), `close`.
- [ ] Unit tests with `pytest` and Dockerised ClickHouse service.
- [ ] Update factory in backend abstraction to instantiate `ClickHouseStore` when `backend: clickhouse`.

## Test Plan
Described in **Task 06 – tests_clickhouse**.

## Exit Criteria
- ClickHouse connection established and functional in CI integration tests.
- `ruff`, `mypy` clean. Coverage ≥ 90 % on `elastalert/datastores/clickhouse*`.
- No regressions in Elasticsearch functionality.