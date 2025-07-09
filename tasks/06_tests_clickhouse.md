# Task 06: Tests – ClickHouse

## Goal
Add **integration & unit tests** ensuring that ElastAlert 2 operates correctly against ClickHouse for the *frequency* and *spike* rule types.

## Environment (UPDATED)
Docker Compose service snippet:
```yaml
services:
  clickhouse:
    image: clickhouse/clickhouse-server:23.4
    ports: ["9000:9000"]          # native protocol
    healthcheck:
      test: ["CMD-SHELL", "clickhouse-client --query 'SELECT 1'"]
      interval: 5s
      retries: 5
```
Pytest will launch this service via `docker-compose` fixture defined in `tests/conftest.py`.

## Fixtures
1. **DDL** – executed once per session:
   ```sql
   CREATE TABLE passivedns.passivedns_v2 (
       timestamp DateTime64(6, 'UTC'),
       client_id LowCardinality(String),
       query_type LowCardinality(String),
       rate_limited Bool  
       -- … other columns ...
   ) ENGINE = MergeTree
   PARTITION BY toYYYYMMDD(timestamp)
   PRIMARY KEY (client_id, toUnixTimestamp(timestamp));
   ```
2. **Data loading** – parameterised fixtures inserting synthetic rows:
   * **Frequency positive**: 200 rows for `client_id='C1'` & `query_type='A'` within last 15 min.
   * **Frequency negative**: 50 rows older than 15 min.
   * **Spike reference**: 100 rows (−30 min → −15 min).
   * **Spike current**: 600 rows (−15 min → now).

## Markers
`@pytest.mark.clickhouse` – used to skip tests when ClickHouse service not available locally.

## Assertions
| Rule | Condition | Expectation |
|------|-----------|-------------|
| Frequency | ≥ `num_events` (default 100) within 15 min | **Alert** |
| Frequency | < `num_events` | **No alert** |
| Spike | `cnt_current ≥ spike_height × cnt_reference` **and** `cnt_reference ≥ threshold_ref` | **Alert** |
| Spike | any pre-condition violated | **No alert** |

## Code Checklist
- [ ] Fixtures live in `tests/clickhouse_fixtures.py`.
- [ ] Tests reside in `tests/alerters/clickhouse_*.py`.
- [ ] Use `pytest-asyncio` if async queries are employed.
- [ ] Ensure test suite can be executed in CI within 2 minutes.

## Exit Criteria
- ElastAlert run once per scenario emits exactly one alert for positives, zero for negatives.
- Overall coverage target ≥ 90 % on `datastores/clickhouse*` and SQL builder modules.