#!/usr/bin/env python3
"""Agreement analysis for the independent second-annotator packet.

Compares a completed annotation sheet against the frozen author-validated
reference labels and reports percent agreement and Cohen's kappa:
overall (4-category), per rule, and on decided cells only
(PRESENT/ABSENT). Pure standard library.

Usage:
    python3 analyze_agreement.py ANNOTATOR_SHEET.csv \
        [--reference ../../results/labels/reference_labels_author_validated_v1.csv] \
        [--out-prefix agreement]

Rows are joined on (bundle_path, rule_id). Only rows where BOTH sides
have a non-empty label are scored; rows the annotator left blank are
reported as incomplete, never scored as disagreements.
"""
import argparse
import csv
import sys
from collections import Counter, defaultdict

LABELS = ["PRESENT", "ABSENT", "U", "NA"]
DECIDED = ["PRESENT", "ABSENT"]


def load(path):
    out = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            key = (row["bundle_path"], row["rule_id"])
            out[key] = row.get("label", "").strip()
    return out


def kappa(pairs, cats):
    n = len(pairs)
    if n == 0:
        return None
    agree = sum(1 for a, b in pairs if a == b)
    po = agree / n
    ca = Counter(a for a, _ in pairs)
    cb = Counter(b for _, b in pairs)
    pe = sum((ca[c] / n) * (cb[c] / n) for c in cats)
    k = (po - pe) / (1 - pe) if pe < 1 else 1.0
    return {"n": n, "agree": agree, "pct": round(100 * po, 1), "kappa": round(k, 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("--reference", required=True)
    ap.add_argument("--out-prefix", default="agreement")
    args = ap.parse_args()

    ann = load(args.sheet)
    ref = load(args.reference)

    keys = sorted(set(ann) & set(ref))
    missing = sorted(set(ref) - set(ann))
    blank = [k for k in keys if not ann[k]]
    pairs = [(ann[k], ref[k]) for k in keys if ann[k]]
    bad = [(k, ann[k]) for k in keys if ann[k] and ann[k] not in LABELS]
    if bad:
        print(f"ERROR: {len(bad)} annotator labels not in {LABELS}: {bad[:5]}", file=sys.stderr)
        return 1

    print(f"joined cells: {len(keys)}  scored: {len(pairs)}  annotator-blank: {len(blank)}  not-in-sheet: {len(missing)}")
    overall = kappa(pairs, LABELS)
    print(f"OVERALL 4-category: n={overall['n']} agreement={overall['pct']}% kappa={overall['kappa']}")
    dec = [(a, b) for a, b in pairs if a in DECIDED and b in DECIDED]
    kd = kappa(dec, DECIDED)
    if kd:
        print(f"DECIDED-only (PRESENT/ABSENT both sides): n={kd['n']} agreement={kd['pct']}% kappa={kd['kappa']}")
    ux = [(a, b) for a, b in pairs if (a in DECIDED) != (b in DECIDED)]
    print(f"decided-vs-undecided boundary crossings: {len(ux)}")

    by_rule = defaultdict(list)
    for (bp, rule), a, b in [(k, ann[k], ref[k]) for k in keys if ann[k]]:
        by_rule[rule].append((a, b))
    print("\nper-rule (4-category):")
    for rule in sorted(by_rule):
        s = kappa(by_rule[rule], LABELS)
        print(f"  {rule}: n={s['n']} agreement={s['pct']}% kappa={s['kappa']}")

    conf = Counter(pairs)
    print("\nconfusion (annotator -> reference):")
    for a in LABELS:
        print("  " + "  ".join(f"{a}->{b}:{conf.get((a, b), 0)}" for b in LABELS))

    with open(args.out_prefix + "_disagreements.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["bundle_path", "rule_id", "annotator_label", "reference_label"])
        for k in keys:
            if ann[k] and ann[k] != ref[k]:
                w.writerow([k[0], k[1], ann[k], ref[k]])
    print(f"\ndisagreements written to {args.out_prefix}_disagreements.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
