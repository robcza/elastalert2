# Task 07: Docs Update

## Goal
Update user and developer **documentation** to cover ClickHouse support with clear examples & migration guidelines.

## Context (UNCHANGED except snippets)
Docs live under `docs/source/`.  They must build cleanly via Sphinx with no warnings.

## Deliverables
1. Extend `configuration.rst` with new ClickHouse options and defaults.
2. Add section **Running against ClickHouse** in `running_elastalert.rst` containing:
   * Docker Compose snippet from Task 06.
   * Minimal rule YAML example (backend: clickhouse).
3. Provide **SQL snippets** illustrating what ElastAlert executes, e.g.:
   ```sql
   -- Frequency rule example
   SELECT count() AS cnt
   FROM passivedns.passivedns_v2
   WHERE client_id = 'C1'
     AND query_type = 'A'
     AND timestamp BETWEEN now() - INTERVAL 15 MINUTE AND now();
   ```
4. Update `advanced.rst` to document datastore abstraction and how to add new backends.
5. Add CHANGELOG entry under **Unreleased – Added**.

## Code Checklist
- [ ] All `.rst` files build without warnings (`make -C docs html`).
- [ ] README badges mention ClickHouse.
- [ ] Highlight that rule YAML is unchanged except backend/connection settings.

## Test Plan
`docs/Makefile` target `html` runs in CI; fails on warnings.

## Exit Criteria
- Documentation builds successfully in CI.
- Examples verified by executing against sample ClickHouse instance.