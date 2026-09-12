# Dependency train intervals

Train `aeco-0.8.1` has **0 direct-pin mismatches among 125 declarations**.
All 35 requirement-range checks and 22 publication-contract checks pass.
Every floor remains unchanged from 0.8.0, including the scenarios floor v0.8.0.

The floor is the first permitted public release. Declared fixtures remain
separate in [drift.json](drift.json) and never waive a direct mismatch.
The generic build kit is included in interval checks; OpenUSD inputs remain external.

## Train bounds

| Repository | Floor | Released |
|---|---|---|
| aeco-toolchain | v0.4.0 | v0.4.0 |
| usdaeco-core | v0.9.4 | v0.9.5 |
| usdaeco-axis | v0.1.4 | v0.1.5 |
| usdaeco-toolchain | v0.3.8 | v0.3.10 |
| usdaeco-buildup | v0.2.4 | v0.2.5 |
| usdaeco-wall | v0.2.4 | v0.2.5 |
| usdaeco-pipe | v0.2.4 | v0.2.5 |
| usdaeco-cctv | v0.5.5 | v0.5.6 |
| usdaeco-cctv-exec | v0.2.3 | v0.2.4 |
| usdaeco-sync | v0.5.4 | v0.5.5 |
| usdaeco-ifc | v0.2.2 | v0.2.3 |
| usdaeco-bonsai | v0.1.5 | v0.1.6 |
| usdaeco-revit | v0.1.4 | v0.1.5 |
| usdaeco-datacentre | v0.4.8 | v0.4.9 |
| usdaeco-board | v0.1.4 | v0.1.5 |
| usdaeco-scenarios | v0.8.0 | v0.8.1 |
| usdaeco-meta | Private, unpinned | — |
| usdaeco-plan | v0.1.3 | v0.1.4 |
| usdaeco-compliance | v0.1.2 | v0.1.3 |
| usdaeco-repeat | v0.2.0 | v0.2.1 |
| usdaeco-clash | v0.2.2 | v0.2.3 |
| usdaeco-solid | v0.1.4 | v0.1.5 |
| usdSolid | v0.1.4 | v0.1.6 |
| usdSolidOcct | v0.1.3 | v0.1.5 |

## Exact upstream mismatches

None. Both the single full gate and the separate fast profile report 125/125.
[Previous drift](drift-0.8.0.md) preserves the earlier 32 findings.
