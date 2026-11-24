# Publication audit 08 — frozen v2 byte integrity (2026-11-24)

Retrieved the frozen CSV via the Git blob endpoint (the contents endpoint returned empty content). Blob SHA: `2462d7ab3d4a380a3fd0f25904a75dd2dba27b28`. Encoded the returned UTF-8 text without newline normalization (1686645 bytes), computed SHA-256 using a JavaScript implementation checked against the standard abc test vector, and obtained `c7eeb2ea5f62d3e01724137de30ea6cbe769ba66d936e4a437155def7410aebe`, matching the frozen sidecar. This closes the direct CSV digest check; it does not establish execution of the committed Python verifier or fresh scanner/bootstrap reproduction. No frozen inputs changed.

Remaining: execute full pipeline against frozen v2, inspect interval endpoints and preserve output archive.
