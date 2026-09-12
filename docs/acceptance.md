# Family 0.8.1 acceptance

Full: **124 checks, 3 failed, 25 not run; 96 PASS; 1222.26 s**. Fast: **53 checks, 0 failed, 23 not run; 30 PASS; 79.37 s**.
Drift is **0/125**. The full run passes **19/21 repository suites**; core and
axis pass separate corrected rechecks: **71/71** and **54/54**. The reviewer
is reproducing the corrected complete full run and will record its result at
merge; complete corrected acceptance is not yet proven here.

[Full report](acceptance.json), [fast report](acceptance-fast.json),
[source inventory](release-inventory.json), [drift](drift.md) and
[final verification](final-verification.json) retain their measured scopes.

The subsequent [release correction](release-correction.json) passes fast
**53 checks, 0 failed, 23 not run; 30 PASS; 79.96 s**. It measures **139 pytest
tests**, **29/0 lint**, **45/45 link roots**, **24 fresh index rows** and **0/125
drift** with no pre-existing hub checkout. After the documentation update, the
link check passes **45/45 roots** and the sweep finds **0 violations in 132 files**.
The table below preserves the original full and fast evidence.

## Acceptance

| Requirement | Measured result | Status |
|---|---|---|
| Public train | 24 entries; 22 tagged dependencies, current candidate and private metadata | PASS |
| Current source pins | 21/21 exact sources | PASS |
| Drift | 0/125 mismatches; all 24 floors unchanged | PASS |
| Requirement ranges | 35/35 | PASS |
| Publication contracts | 22/22 | PASS |
| Family index | 24 fresh rows; candidate explicitly identified | PASS |
| Walkthrough | 5 released findings files and 5 recorded renders | PASS |
| Executable repository suites | 19/21 suites in full; 1489 checks, 7 failed, 28 NOT RUN | FAIL |
| Corrected core and axis suites | 71/71 and 54/54 in separate focused checks; original full failures retained | PASS |
| Documentation links | 45/45 roots; 4/4 kit roots; both full and fast checks | PASS |
| Local structure | 29 checks, 0 failed | PASS |
| Final sanitization | 131 text/stage files, 0 violations | PASS |
| Current documentation naming | 13 Markdown files, 0 retired-name mentions | PASS |
| git diff --check | Clean | PASS |
| Local pytest | 135 passed in 13.63s | PASS |
| one plugin path | 7/7 libraries | PASS |
| core validator registry | 8/8 loaded through UsdValidation | PASS |
| bonsai scenarios | 21/21; native Bonsai entry point | PASS |
| Full wall-clock | 1222.25s / 360s; full profile; 4 suite processes; source isolation, builds, suites and consumers included | FAIL |
| Fast wall-clock | 79.37s / 360s; fast profile; 4 suite processes; source isolation, builds, suites and consumers included | PASS |
| Offline Nix | One attempt; exit 1 in 0.11 s before evaluation | NOT PROVEN |

## Repository suites from the single full run

| Repository | Tag | Checks | Failed | NOT RUN | Seconds |
|---|---|---|---|---|---|
| usdaeco-core | v0.9.5 | 71 | 6 | 0 | 11.56 |
| usdaeco-axis | v0.1.5 | 54 | 1 | 0 | 15.08 |
| usdaeco-toolchain | v0.3.10 | 65 | 0 | 0 | 618.87 |
| usdaeco-buildup | v0.2.5 | 67 | 0 | 0 | 74.13 |
| usdaeco-wall | v0.2.5 | 87 | 0 | 0 | 71.19 |
| usdaeco-pipe | v0.2.5 | 82 | 0 | 0 | 94.40 |
| usdaeco-cctv | v0.5.6 | 159 | 0 | 0 | 117.47 |
| usdaeco-cctv-exec | v0.2.4 | 54 | 0 | 21 | 0.44 |
| usdaeco-sync | v0.5.5 | 52 | 0 | 0 | 8.19 |
| usdaeco-ifc | v0.2.3 | 101 | 0 | 0 | 633.71 |
| usdaeco-bonsai | v0.1.6 | 70 | 0 | 0 | 304.94 |
| usdaeco-revit | v0.1.5 | 52 | 0 | 1 | 90.99 |
| usdaeco-datacentre | v0.4.9 | 204 | 0 | 4 | 797.45 |
| usdaeco-board | v0.1.5 | 70 | 0 | 0 | 23.04 |
| usdaeco-plan | v0.1.4 | 51 | 0 | 2 | 148.71 |
| usdaeco-compliance | v0.1.3 | 48 | 0 | 0 | 243.53 |
| usdaeco-clash | v0.2.3 | 48 | 0 | 0 | 141.65 |
| usdaeco-solid | v0.1.5 | 50 | 0 | 0 | 122.00 |
| usdaeco-repeat | v0.2.1 | 44 | 0 | 0 | 106.91 |
| usdSolid | v0.1.6 | 29 | 0 | 0 | 9.51 |
| usdSolidOcct | v0.1.5 | 31 | 0 | 0 | 11.67 |

Total: 1489 checks, 7 failed, 28 NOT RUN; 1454 PASS.
No previous suite report was reused. The matching immutable native runtimes
passed the kit build-revision, installed-metadata and compiled-source checks.
The [focused correction](minimal-source-correction.json) records core 71/71
and axis 54/54 separately; it does not replace their full-run rows.

## Exact full-run failures

| Gate | Result | Status |
|---|---|---|
| core check.py | 65/71; 0 NOT RUN; 11.56s | FAIL |
| axis check.py | 53/54; 0 NOT RUN; 15.08s | FAIL |
| family wall-clock budget | 1222.25s / 360s; full profile; 4 suite processes; source isolation, builds, suites and consumers included | FAIL |

## Deviations

- The full profile exceeds the 360-second budget: 1222.26 s.
  The fast profile takes 79.37 s and passes its executed checks;
  its 23 NOT RUN rows include omitted suites and reproductions.
  It does not establish fresh publication parity or replace the full profile.
- The full run exposed a local environment-selection defect: core and axis
  declare a data-centre pin but their published examples require minimal
  sources. The runner incorrectly supplied that pin as an example override.
  The committed correction and regression keep declared source discovery while
  clearing ROOT/STAGE overrides for those two suites. Focused rechecks pass
  71/71 and 54/54; the original full failures remain. The full gate was run
  exactly once for this evidence. The corrected complete run is the reviewer's
  reproduction, with its result to be recorded at merge.
- Sources came from the internal mirror at the requested public release tags.
  Public-only source acquisition was not exercised. Historical fixtures remain
  separately declared; resolved commits are evidence, not cross-mirror pins.
- The generic build kit has no semantic source card or Python suite. Its floor
  is checked; the index states its missing card explicitly. The scenarios
  candidate is tested without claiming that v0.8.1 has already been published.
- The first correction fast run passed index freshness but failed four drift
  revision audits because the hub checkout was absent. Index and drift now share
  a temporary source fetched at its released tag; the final correction fast run
  passes all executed rows. Both correction measurements are recorded separately.
- The one offline Nix attempt exited 1 in 0.11 s: the network-denied
  sandbox also denied access to the Nix daemon socket, before input evaluation.
  Nix is not proven. No retry, dependency installation or native rebuild was made.
- Existing native-template, executable CCTV, live integration and historical
  scenario omissions remain NOT RUN with their reasons in the reports.
  All 21 suites have passing evidence across the full run and two focused
  rechecks; that is not a corrected complete full run. NOT RUN never counts as PASS.

## Prior evidence and remaining work

The [preceding full](acceptance-0.8.0.json),
[fast](acceptance-fast-0.8.0.json), [narrative](acceptance-0.8.0.md),
[drift](drift-0.8.0.md) and [packaging](packaging-0.8.0.md) preserve the earlier
measurements. The prior build-up correction is now covered by its passing
suite in this full run. Current documentation has no retired repository-name
mentions; historical evidence and CHANGELOG retain their original vocabulary.

The reviewer is reproducing the corrected complete full measurement and will
record its result at merge. The full profile's duration and an executable
offline Nix check remain unresolved. Public-only acquisition and explicitly
omitted live/native scenarios remain unproven. No pull request is merged by
this work.
