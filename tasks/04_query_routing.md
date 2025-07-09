# Task 04: Query Routing

## Goal
Implement **transparent query routing** so that ElastAlert core asks the correct datastore (Elasticsearch or ClickHouse) based solely on the `backend` key present in rule YAML or global config.

## Context (UNCHANGED)
With the abstraction from Task 01 we now simply need to plug in the correct store instance at rule evaluation time.

## Deliverables
1. Factory function `get_datastore(config)` that returns an instance of `ElasticSearchStore` or `ClickHouseStore`.
2. Modify rule loader to call this factory.
3. Verbal logging indicating which backend is in use for each rule.

## Code Checklist
- [ ] Implement factory with sensible error handling for unsupported backends.
- [ ] Ensure lifecycle management (`close`) is called on shutdown.
- [ ] Add unit tests using `pytest.mark.parametrize('backend', ['elasticsearch', 'clickhouse'])`.

## Test Plan
* Verify that rules with `backend: clickhouse` receive a ClickHouseStore.
* Existing tests for Elasticsearch remain untouched.

## Exit Criteria
- Routing works; CI green.
- Code-cov on factory ≥ 95 %.