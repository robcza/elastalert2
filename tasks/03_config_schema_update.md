# Task 03: Config Schema Update

## Goal
Extend the ElastAlert 2 **configuration schema** so that ClickHouse back-end settings are first-class citizens with sensible defaults.

## Context (UNCHANGED except defaults)
The master configuration file already supports per-backend sections.  We now add:
```yaml
ck_database: passivedns   # default, overridable per-rule
ck_table:    passivedns_v2
```
These values complement existing `ck_host`, `ck_port`, `ck_username`, `ck_password` keys.

## Deliverables
1. Update `elastalert/config.py` schema validation (`voluptuous`) to include the two new keys with defaults above.
2. Document the new options in **docs/configuration.rst**.
3. Ensure `--schema` CLI JSON reflects the new properties.

## Code Checklist
- [ ] Add two `voluptuous.Schema` entries with `Default()` wrappers.
- [ ] Propagate defaults into runtime config object used by `ClickHouseStore`.
- [ ] Add unit tests in `tests/config_test.py` verifying default application when keys are omitted.

## Test Plan
* Run `pytest -k config_test` – new tests pass.
* Full test suite remains green.

## Exit Criteria
- Defaults correctly injected; no change to Elasticsearch workflows.
- Documentation builds without warnings.