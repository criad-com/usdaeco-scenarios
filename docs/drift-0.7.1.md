# Dependency train intervals

Train `aeco-0.7.0` has **0 direct-pin mismatches**, out of 121 checked declarations. All 35 requirement-range checks and 22 publication-contract checks pass.

Every direct pin must lie inside its dependency's inclusive floor–released interval and satisfy its declared requirement range. Revision assertions are checked against the declared tag. Every floor is unchanged from the preceding gate.

The 47 declared fixtures are inventoried separately in [drift.json](drift-0.7.1.json). Toolchain v0.3.7 declares core v0.8.4 as a flake fixture; solid v0.1.3 pins toolchain v0.3.7. Fixtures cannot satisfy direct requirements or waive direct mismatches.

## Train bounds

| Repository | Floor | Released |
|---|---|---|
| usdaeco-core | v0.9.2 | v0.9.3 |
| usdaeco-axis | v0.1.2 | v0.1.3 |
| usdaeco-toolchain | v0.3.5 | v0.3.7 |
| usdaeco-buildup | v0.2.1 | v0.2.2 |
| usdaeco-wall | v0.2.1 | v0.2.3 |
| usdaeco-pipe | v0.2.1 | v0.2.3 |
| usdaeco-cctv | v0.5.2 | v0.5.4 |
| usdaeco-cctv-exec | v0.2.1 | v0.2.2 |
| usdaeco-sync | v0.5.2 | v0.5.3 |
| usdaeco-ifc | v0.2.0 | v0.2.1 |
| usdaeco-bonsai | v0.1.2 | v0.1.4 |
| usdaeco-revit | v0.1.2 | v0.1.3 |
| usdaeco-datacentre | v0.4.5 | v0.4.6 |
| usdaeco-board | v0.1.2 | v0.1.3 |
| usdaeco-scenarios | v0.6.0 | v0.7.0 |
| usdaeco-meta | Unreleased | Unreleased |
| usdaeco-plan | v0.1.0 | v0.1.2 |
| usdaeco-compliance | v0.1.0 | v0.1.1 |
| usdaeco-repeat | v0.1.0 | v0.1.1 |
| usdaeco-clash | v0.2.0 | v0.2.1 |
| usdaeco-solid | v0.1.1 | v0.1.3 |
| usdSolid | v0.1.0 | v0.1.2 |
| usdSolidOcct | v0.1.0 | v0.1.1 |
