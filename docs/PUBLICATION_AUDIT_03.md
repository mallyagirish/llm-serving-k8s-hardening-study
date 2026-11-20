# Publication audit 03 — executable frozen-reference integrity gate

**Date:** 2026-11-20

Added `scripts/verify_frozen_labels.py` as a **read-only, standard-library-only** validation command. It checks the actual v2 CSV byte SHA-256 against its committed sidecar, exact 2,940 row count, expected four-label totals, 105 × 28 complete unique bundle–rule keys, consistent per-bundle SHA-256/project mappings, and 10 upstream project clusters. It exits nonzero on a failed assertion.

Run from the repository root:

```bash
python scripts/verify_frozen_labels.py --repo-root .
```

This script was syntax-checked before commit, **but it has not been run against the complete frozen CSV in this audit session**. No PASS result is claimed. A passing result will establish integrity and internal matrix consistency, not correctness of every human label or reproducibility of the scanner/bootstrap outputs.

The next acceptance gate remains: run this script on a checkout, archive its JSON output and environment/revision, then execute corpus validation, pre-adjudication scanner evaluation and cluster bootstrap using pinned input versions. Do not overwrite or modify the frozen labels or metadata. See `docs/PUBLICATION_READINESS_PLAN.md` and `docs/PUBLICATION_AUDIT_02.md`.
