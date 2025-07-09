# Task 05: SQL Builders

## Goal
Create robust SQL generation utilities that translate ElastAlert rule filters into **ClickHouse-native** `SELECT` statements for both full-row retrieval and aggregation counts.

## Context (UPDATED)
Frequency & Spike rule types rely on two kinds of queries:
1. **Event selection** → return all rows in a time window
2. **Count aggregation** → return `cnt` for a time window

## Specification
### Event Selection Template (Frequency rule)
```sql
SELECT *
FROM {ck_database}.{ck_table}
WHERE client_id = %(client_id)s
  AND {additional_filters}
  AND timestamp >= %(start)s
  AND timestamp <  %(end)s
ORDER BY timestamp
```

### Count Template (Frequency / Spike)
```sql
SELECT count() AS cnt
FROM {ck_database}.{ck_table}
WHERE client_id = %(client_id)s
  AND timestamp BETWEEN %(start)s AND %(end)s
  AND {additional_filters}
```

`{additional_filters}` come from the YAML `filter:` section:
* `query_string: "query_type:A"` → `query_type = 'A'`
* Ignore empty filter strings.

### Helper API
* `build_where_clause(filters: list[dict]) -> tuple[str, dict]` returns SQL snippet and bound parameters.
* `render_sql(template: str, ctx: Mapping[str, Any]) -> str` simple `.format` helper.

## Deliverables
1. `elastalert/datastores/ck_sql.py` with builder helpers.
2. Unit tests covering:
   * Single and multiple query_string filters.
   * Edge cases: empty filters list, unsupported filter types (raise).

## Code Checklist
- [ ] 100 % coverage of translation logic.
- [ ] Strict mypy types.
- [ ] SQL is **parametrised** – no string concatenation of user values.

## Test Plan
Run `pytest -k sql_builders` – all green.

## Exit Criteria
- Builders generate correct SQL verified by execution in Docker ClickHouse (see Task 06 fixtures).
- Coverage ≥ 90 % on builder module.