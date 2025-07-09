# Task 99: CI Validation

## Goal
Ensure that the **continuous-integration workflow** validates code quality, type-safety, tests, coverage, and documentation for **both** Elasticsearch and ClickHouse backends.

## CI Stages (UNCHANGED)
1. **Lint & Type Check**  
   * `ruff` for style / import sorting  
   * `mypy` strict optional
2. **Test Matrix**  
   * `pytest` with markers:
     * default – Elasticsearch only
     * `clickhouse` – spins up ClickHouse service and runs additional tests (Task 06)
   * Coverage collected via `pytest-cov` – threshold ≥ 90 % on new modules.
3. **Docs Build**  
   * `make -C docs html` – warnings treated as errors.

## Implementation Details
* GitHub Actions workflow file `.github/workflows/ci.yml` updated to include ClickHouse service (ports 9000/8123 if HTTP used).
* Matrix includes python 3.9–3.12.

## Exit Criteria
- All CI jobs green.
- Coverage and docs targets met.
- No regressions in Elasticsearch-only pipeline duration (< 5 min).