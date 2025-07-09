# Task 01: Backend Abstraction

## Goal
Establish a clean **datastore abstraction layer** that allows ElastAlert 2 to support multiple back-ends (Elasticsearch today, ClickHouse tomorrow) without impacting rule authors or existing runtime behaviour.

## Context
ElastAlert 2 is currently tightly coupled to Elasticsearch APIs.  Introducing ClickHouse requires a pluggable architecture so that:
* Existing Elasticsearch logic remains untouched and fully functional.
* New back-ends can be added by implementing a well-defined interface.

## Deliverables
1. A `datastores` Python package with:
   * `BaseDataStore` – abstract class defining the contract used by rule types (search, get_hits_count, etc.).
   * `ElasticSearchStore` – extracted from current logic and conforming to `BaseDataStore`.
   * **No ClickHouse implementation in this task** – only the abstraction.
2. Refactor core engine to depend on `BaseDataStore` instead of concrete ES helper.
3. Migration guide in docs explaining that nothing changes for rule authors.

## Code Checklist
- [ ] Create `elastalert/datastores/__init__.py` exporting concrete stores.
- [ ] Implement `BaseDataStore` with `@abc.abstractmethod` members: `search`, `count`, `iter_hits`, `get_event_timestamp_field`, `close`.
- [ ] Move existing ES helper code into `ElasticSearchStore` without functional change.
- [ ] Update rule loading to instantiate store based on `backend` config key.
- [ ] All linter (`ruff`) and static-type (`mypy`) checks pass.

## Test Plan
* **Unit:**
  * Adapt existing ES tests to run through `ElasticSearchStore` path.
  * Add mocks verifying that core engine calls only `BaseDataStore` API.
* **Integration:**
  * Run full existing `pytest` suite — no regressions allowed.

## Exit Criteria
- CI (`ruff`, `mypy`, `pytest`) green on all platforms.
- 100 % of existing Elasticsearch functionality retained (all tests still pass).
- Documentation updated with abstraction overview diagram.