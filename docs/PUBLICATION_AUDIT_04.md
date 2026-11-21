# Publication audit 04 — verifier contract tests (2026-11-21)

## Completed
Added `tests/test_verify_frozen_labels.py`, six standard-library regression tests for `scripts/verify_frozen_labels.py`. The tests construct **synthetic** 105 × 28 matrices with expected four-outcome totals in temporary directories; they never edit the actual frozen CSV or sidecar.

Test coverage:
1. Valid 2,940-row, 105-bundle, 28-rule, 10-project matrix passes.
2. Tampered CSV bytes fail the SHA-256 check.
3. Duplicate bundle–rule keys fail even when aggregate label counts and sidecar hash are updated.
4. Conflicting upstream-project assignment for a bundle fails.
5. Changed label totals fail even when sidecar SHA-256 is updated.
6. Missing required CSV column fails.

The six tests were run in a local isolated Python environment using:

```bash
python -m unittest discover -s tests -p 'test_verify_frozen_labels.py' -v
```

**Observed result: 6 tests run, 6 passed.** This tests the verifier's behavior, **not** the empirical study's actual data. The repository's full test suite and CI have not been run in this audit.

## Still blocking the reproducibility gate
- The full frozen v2 CSV was not available as bytes in the analysis environment; GitHub connector partial file reads yielded no CSV content, and direct GitHub cloning was unavailable due to DNS/network restrictions. Do not claim a verified CSV checksum or a successful 2,940-row study-data validation.
- Run the verifier against an actual checked-out repository, archive its output and Python version, then rerun scanner evaluation and cluster-bootstrap commands with pinned hashes.
- Independently compare resulting per-rule denominators and uncertainty intervals to manuscript tables.
- External-review provenance remains author-reported; no independent blinded annotation or human inter-rater statistic can be claimed.

## Recommended next execution

```bash
python -m unittest discover -s tests -p 'test_verify_frozen_labels.py' -v
python scripts/verify_frozen_labels.py --repo-root .
```

A passing verifier is necessary but not sufficient: it validates dataset integrity and internal structure, not substantive correctness of author labels or statistical claims.
