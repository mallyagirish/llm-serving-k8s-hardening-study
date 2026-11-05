# Corpus Eligibility Screening Guide

## Purpose

The pinned corpus contains 202 bundle entries, but not every entry is necessarily an LLM inference workload. The primary research denominator must not include generic ML examples, operators, GPU schedulers, or unrelated KServe samples merely because they are in a serving-related repository.

This guide and `corpus/eligibility_review.csv` establish a human-reviewed eligibility screen before prevalence analysis.

## Screening strata

- **primary_candidate:** likely to contain an LLM inference workload, engine, or gateway. Inspect actual resources and source context before inclusion.
- **supporting_platform_candidate:** operator, scheduler, gateway infrastructure, or GPU-sharing examples. Keep separate from primary workload prevalence unless a specific rule is explicitly about platform infrastructure.
- **non_llm_or_unclear:** no strong LLM-serving identity is evident from path/source metadata. Exclude from primary prevalence unless a reviewer documents positive evidence.
- **exclude_pending:** currently listed in `corpus/parse_exceptions.json`; not standalone parseable YAML.

These are automated preliminary triage suggestions, not final labels or findings.

## Final decisions

For every row, a reviewer should set:
- `include_primary`: direct LLM inference serving configuration;
- `include_supporting`: platform component or infrastructure relevant only to a secondary analysis;
- `exclude_non_llm`: generic ML or unrelated example;
- `exclude_unparseable`: invalid YAML or unrendered template fragment;
- `uncertain`: insufficient context; resolve before primary analysis.

Record a concise reason and reviewer initials. A second reviewer should independently inspect borderline cases and all primary-candidate decisions before the dataset is frozen.

## Resource-level checks

A bundle may contain multiple resources. Reviewers should identify the actual serving workload, not infer that every Deployment/Pod in a chart is an inference container. Distinguish:
- inference servers and their model-loading initContainers;
- gateways/proxies and auth components;
- operators/controllers;
- GPU schedulers/device plugins;
- examples that merely allocate a GPU but do not serve an LLM.

The same bundle can contain both in-scope and out-of-scope resources. Where practical, record resource-level eligibility in a separate annotation table rather than including or excluding an entire bundle indiscriminately.

## Denominators and reporting

Report the flow from 202 locked bundles to parseable bundles, screened bundles, eligible resources/workloads, and rule-applicable units. Do not describe the 202 bundle corpus as 202 deployments. Treat repeated chart versions and overlays as clustered observations, not independent projects.

No prevalence estimate should be produced until final decisions are reviewed, duplicates are identified, and the primary unit of analysis is frozen.
