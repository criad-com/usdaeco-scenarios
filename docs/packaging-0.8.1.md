# Release packaging acceptance — 0.8.1

[family.json](../family.json) selects public train `aeco-0.8.1`.
Every active reference in [dependencies.json](../dependencies.json) and the
flake uses a release tag under `criad-com`. The public floors are unchanged
from 0.8.0; all 125 direct declarations lie inside their train intervals.
Historical fixtures retain their own declarations and never waive direct drift.

## Sources and execution scopes

The inventory contains 24 entries: 22 released dependencies, this candidate
and private, unpinned metadata. Twenty-one dependencies have Python acceptance
suites. The generic build kit has no semantic source card or Python gate;
its public floor is still checked. The index explicitly identifies the
candidate without claiming its release tag has been published.

The gate acquired tagged sources in a fresh root through the internal mirror,
then audited and built disposable copies. The source inventory records resolved
commits and trees. Public-only acquisition was not exercised. No stable sibling
checkout was modified, and no previous suite report was reused.

Seven consumer libraries build together and all eight core validators load
through UsdValidation. Suites use their declared toolchains and inputs;
consumer builds and scenarios lint use toolchain v0.3.10. Generation fixtures
remain separate from modern validation inputs and current-train consumers.
Core and axis declare a data-centre dependency while their published examples
use minimal sources. Their corrected suite environment retains declared source
discovery and clears data-centre ROOT/STAGE example overrides. Build-up retains
its explicitly selected data-centre example source.

The native suites used existing immutable runtimes matching usdSolid v0.1.6
and usdSolidOcct v0.1.5. Both passed build-revision, installed-metadata and
compiled-source checks. No dependency installation or native rebuild was made.
Blender/Bonsai scenarios executed; omitted native-template, executable CCTV
and live integration scenarios keep their explicit NOT RUN reasons.

## Full and fast profiles

The original [acceptance](acceptance.md) records one fresh full run and one
separate fast measurement. Full: **124 checks, 3 failed, 25 not run; 96 PASS;
1222.26 s**. Failed rows are core, axis and the 360-second budget.
The minimal-source environment correction
passes a regression and separate complete core and axis suites, **71/71** and
**54/54**, recorded in
[minimal-source-correction.json](minimal-source-correction.json). These focused
results do not replace the original full failures.

The fast profile passes its executed checks and time budget. It checks source
pins, committed inventories, relocated plugin-free stages and local regressions.
It omits full suites and fresh consumer reproductions, marking them NOT RUN;
fast success does not establish publication parity. The reviewer is reproducing
the corrected complete full run and will record its measured result at merge;
that result is not yet proven here.

The subsequent [release correction](release-correction.json) records fast
**53 checks, 0 failed, 23 not run; 79.96 s**, **139 passing pytest tests**, **29/0
lint**, **45/45 link roots** and **24 fresh index rows**. This run starts without
a hub checkout: index and drift share a temporary source fetched at the hub's
released tag, and no semantic suite is claimed for it. An initial correction
fast run exposed the drift checks' need for the same source; its failure is
retained in the receipt. No additional full or Nix run was made.

## Nix

Exactly one offline attempt was made:

```sh
nix flake check --offline --no-update-lock-file --option restrict-eval true --option allowed-uris '' --option substituters ''
```

The network-denied sandbox also denied access to the Nix daemon socket. The
attempt exited 1 in 0.11 seconds before input evaluation; Nix is not proven.
No retry or lockfile is committed. See the [receipt](nix-evidence.json).
The README describes the external registry and input-override workflow.

## Historical evidence

The [preceding full report](acceptance-0.8.0.json),
[fast report](acceptance-fast-0.8.0.json), [narrative](acceptance-0.8.0.md),
[drift](drift-0.8.0.md) and [packaging](packaging-0.8.0.md) preserve the earlier
measurements. Their embedded versions define their scope. The previous
build-up correction is now covered by its passing suite in this full run.
Historical evidence and CHANGELOG retain the retired repository vocabulary;
current documentation has no such references.
