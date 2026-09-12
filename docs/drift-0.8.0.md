# Dependency train intervals

Train `aeco-0.8.0` has **32 direct-pin mismatches** among 125 declarations.
All 35 requirement-range checks and 22 publication-contract checks pass.
This repository's active pins pass; every mismatch below belongs to a released dependency.

Each floor is the first public release named for that repository. A direct pin
below it remains drift even if an internal archive retains the old tag.
Declared fixtures are listed separately in [drift.json](drift.json); they never
satisfy direct requirements or waive a direct mismatch. The generic build kit
is included in the interval checks. OpenUSD inputs remain external.

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
| usdaeco-ifc | v0.2.2 | v0.2.2 |
| usdaeco-bonsai | v0.1.5 | v0.1.5 |
| usdaeco-revit | v0.1.4 | v0.1.4 |
| usdaeco-datacentre | v0.4.8 | v0.4.9 |
| usdaeco-board | v0.1.4 | v0.1.4 |
| usdaeco-scenarios | v0.8.0 | v0.8.0 |
| usdaeco-meta | Private, unpinned | — |
| usdaeco-plan | v0.1.3 | v0.1.4 |
| usdaeco-compliance | v0.1.2 | v0.1.3 |
| usdaeco-repeat | v0.2.0 | v0.2.1 |
| usdaeco-clash | v0.2.2 | v0.2.3 |
| usdaeco-solid | v0.1.4 | v0.1.5 |
| usdSolid | v0.1.4 | v0.1.5 |
| usdSolidOcct | v0.1.3 | v0.1.4 |

## Exact upstream mismatches

| Consumer | Dependency | Declared | Public floor | Released |
|---|---|---|---|---|
| usdaeco-board | usdaeco-scenarios | v0.6.0 | v0.8.0 | v0.8.0 |
| usdaeco-bonsai | usdaeco-core | v0.9.2 | v0.9.4 | v0.9.5 |
| usdaeco-bonsai | usdaeco-sync | v0.5.2 | v0.5.4 | v0.5.5 |
| usdaeco-bonsai | usdaeco-datacentre | v0.4.6 | v0.4.8 | v0.4.9 |
| usdaeco-bonsai | usdaeco-scenarios | v0.6.0 | v0.8.0 | v0.8.0 |
| usdaeco-bonsai | usdaeco-cctv | v0.5.2 | v0.5.5 | v0.5.6 |
| usdaeco-bonsai | usdaeco-buildup | v0.2.1 | v0.2.4 | v0.2.5 |
| usdaeco-bonsai | usdaeco-wall | v0.2.1 | v0.2.4 | v0.2.5 |
| usdaeco-bonsai | usdaeco-pipe | v0.2.1 | v0.2.4 | v0.2.5 |
| usdaeco-bonsai | usdaeco-ifc | v0.2.0 | v0.2.2 | v0.2.2 |
| usdaeco-bonsai | usdaeco-axis | v0.1.2 | v0.1.4 | v0.1.5 |
| usdaeco-ifc | usdaeco-core | v0.9.2 | v0.9.4 | v0.9.5 |
| usdaeco-ifc | usdaeco-sync | v0.5.2 | v0.5.4 | v0.5.5 |
| usdaeco-ifc | usdaeco-datacentre | v0.4.5 | v0.4.8 | v0.4.9 |
| usdaeco-ifc | usdaeco-scenarios | v0.6.0 | v0.8.0 | v0.8.0 |
| usdaeco-ifc | usdaeco-cctv | v0.5.2 | v0.5.5 | v0.5.6 |
| usdaeco-ifc | usdaeco-buildup | v0.2.1 | v0.2.4 | v0.2.5 |
| usdaeco-ifc | usdaeco-wall | v0.2.1 | v0.2.4 | v0.2.5 |
| usdaeco-ifc | usdaeco-pipe | v0.2.1 | v0.2.4 | v0.2.5 |
| usdaeco-ifc | usdaeco-axis | v0.1.2 | v0.1.4 | v0.1.5 |
| usdaeco-ifc | usdSolid | v0.1.0 | v0.1.4 | v0.1.5 |
| usdaeco-ifc | usdSolidOcct | v0.1.0 | v0.1.3 | v0.1.4 |
| usdaeco-revit | usdaeco-core | v0.9.2 | v0.9.4 | v0.9.5 |
| usdaeco-revit | usdaeco-sync | v0.5.2 | v0.5.4 | v0.5.5 |
| usdaeco-revit | usdaeco-datacentre | v0.4.6 | v0.4.8 | v0.4.9 |
| usdaeco-revit | usdaeco-scenarios | v0.6.0 | v0.8.0 | v0.8.0 |
| usdaeco-revit | usdaeco-cctv | v0.5.2 | v0.5.5 | v0.5.6 |
| usdaeco-revit | usdaeco-buildup | v0.2.1 | v0.2.4 | v0.2.5 |
| usdaeco-revit | usdaeco-wall | v0.2.1 | v0.2.4 | v0.2.5 |
| usdaeco-revit | usdaeco-pipe | v0.2.1 | v0.2.4 | v0.2.5 |
| usdaeco-revit | usdaeco-ifc | v0.2.0 | v0.2.2 | v0.2.2 |
| usdaeco-revit | usdaeco-axis | v0.1.2 | v0.1.4 | v0.1.5 |

All 32 failures are below-floor direct pins. No released manifest was rewritten,
and no direct input was reclassified as a fixture.
