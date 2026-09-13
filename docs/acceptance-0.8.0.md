# Family 0.8.0 acceptance

Full: **124 checks, 5 failed, 25 not run; 94 PASS; 1247.70 s**. Fast: **53 checks, 3 failed, 23 not run; 27 PASS; 79.25 s**.
The required public floors expose **32 upstream direct-pin mismatches**.
The local runner correction passes a separate build-up suite: **67 checks,
0 failed, 72.71 s**. Complete full-gate acceptance remains unproven.

[Full report](acceptance.json), [fast report](acceptance-fast.json),
[source inventory](release-inventory.json), [drift declarations](drift.md) and
[focused correction](buildup-correction.json) retain their separate scopes.

## Acceptance

| Requirement | Measured result | Status |
|---|---|---|
| Public train | 24 entries; exact released tags and first-public floors; private metadata unpinned | PASS |
| Current source pins | 21/21 exact dependency checkouts; scenarios checked as a candidate | PASS |
| Drift | 93/125 direct declarations pass; 32 upstream pins below public floors | FAIL |
| Requirement ranges | 35/35 | PASS |
| Publication contracts | 22/22 | PASS |
| Family index | 24 fresh rows, with explicit candidate and unavailable build-kit source card | PASS |
| Walkthrough | 5/5 released examples and recorded renders; includes repeat v0.2.1 | PASS |
| Executable repository suites | 20/21 pass in the full run; 1489 checks, 1 failed, 28 NOT RUN | FAIL |
| Corrected build-up suite | 67/67; 72.71 s; explicit datacentre v0.4.8 input retained | PASS |
| Consumer plugin registry | 7/7 codeless libraries; all 8 core validators loaded through UsdValidation | PASS |
| Wall and pipe clash consumers | Both pass against datacentre v0.4.9 | PASS |
| Native Bonsai | 21/21 scenarios; zero repeat mutations | PASS |
| IFC/Bonsai demo parity | 152/152; three edits per integration; cleared intent | PASS |
| CCTV idempotence | 60/60 views reused after reopening the stage | PASS |
| Local structure | 29 checks, 0 failed | PASS |
| Local pytest | 134 passed in full; 134 passed in fast | PASS |
| Sanitization during both gates | 118 source files, 0 violations | PASS |
| Final source sweep | 122 files, 0 violations; [receipt](final-verification.json) | PASS |
| Full wall-clock | 1247.70 s / 360 s | FAIL |
| Fast wall-clock | 79.25 s / 360 s | PASS |
| Offline Nix | One attempt; uncached board v0.1.4 input; outbound networking denied | NOT PROVEN |

## Repository suites from the single full run

| Repository | Tag | Checks | Failed | NOT RUN | Seconds |
|---|---|---:|---:|---:|---:|
| usdaeco-core | v0.9.5 | 71 | 0 | 0 | 223.19 |
| usdaeco-axis | v0.1.5 | 54 | 0 | 0 | 43.82 |
| usdaeco-toolchain | v0.3.10 | 65 | 0 | 0 | 617.48 |
| usdaeco-buildup | v0.2.5 | 67 | 1 | 0 | 24.15 |
| usdaeco-wall | v0.2.5 | 87 | 0 | 0 | 71.26 |
| usdaeco-pipe | v0.2.5 | 82 | 0 | 0 | 93.77 |
| usdaeco-cctv | v0.5.6 | 159 | 0 | 0 | 117.43 |
| usdaeco-cctv-exec | v0.2.4 | 54 | 0 | 21 | 0.44 |
| usdaeco-sync | v0.5.5 | 52 | 0 | 0 | 7.48 |
| usdaeco-ifc | v0.2.2 | 101 | 0 | 0 | 639.06 |
| usdaeco-bonsai | v0.1.5 | 70 | 0 | 0 | 303.29 |
| usdaeco-revit | v0.1.4 | 52 | 0 | 1 | 91.69 |
| usdaeco-datacentre | v0.4.9 | 204 | 0 | 4 | 794.04 |
| usdaeco-board | v0.1.4 | 70 | 0 | 0 | 23.06 |
| usdaeco-plan | v0.1.4 | 51 | 0 | 2 | 149.52 |
| usdaeco-compliance | v0.1.3 | 48 | 0 | 0 | 240.49 |
| usdaeco-clash | v0.2.3 | 48 | 0 | 0 | 143.12 |
| usdaeco-solid | v0.1.5 | 50 | 0 | 0 | 121.13 |
| usdaeco-repeat | v0.2.1 | 44 | 0 | 0 | 106.84 |
| usdSolid | v0.1.5 | 29 | 0 | 0 | 9.34 |
| usdSolidOcct | v0.1.4 | 31 | 0 | 0 | 11.74 |

The focused build-up result does not replace its failed full-run row. Every
executable suite now has passing measured evidence, but these separate results
do not establish a complete corrected full run.

## Exact full-run failures

| Gate | Result | Status |
|---|---|---|
| drift dependency train intervals | 93/125; 32 mismatches | FAIL |
| links before builds | 42/45 roots; usdSolid/README.md: a since-removed blocker note; usdSolid/README.md: a since-removed blocker note; usdSolid/docs/verification.md: a since-removed blocker note; usdSolidOcct/docs/public-repin.md: a since-removed blocker note | FAIL |
| buildup check.py | 66/67; 0 NOT RUN; 24.15s | FAIL |
| links at end | 42/45 roots; usdSolid/README.md: a since-removed blocker note; usdSolid/README.md: a since-removed blocker note; usdSolid/docs/verification.md: a since-removed blocker note; usdSolidOcct/docs/public-repin.md: a since-removed blocker note | FAIL |
| family wall-clock budget | 1247.7s / 360s; full profile; 4 suite processes; source isolation, builds, suites and consumers included | FAIL |

## Deviations

- The board, IFC, Bonsai and Revit releases contain 32 direct pins below the
  specified public floors. All are listed in [drift](drift.md). They remain
  failures; no dependency manifest was modified and no direct pin was relabelled
  as a fixture. This repository's active pins use the requested released tags.
- Four broken documentation links are present in the two released Solid kits:
  two README links and one verification link in usdSolid target
  a since-removed blocker note; usdSolidOcct's public-repin document also targets
  a since-removed blocker note. Both family link checks retain their measured
  counts and failures above, with neutral descriptions of the removed targets.
- The full run exposed a local section-suite environment defect. Build-up's
  declared datacentre source was cleared by an inherited minimal-example rule.
  The runner now clears only undeclared facility inputs. Its regression passes,
  and the corrected suite passes 67/67 in a separate measurement. The family
  gate was not rerun and its original failure is preserved.
- Full execution exceeds the 360-second budget. The fast profile fits it but
  intentionally omits suite and consumer reproductions; it still fails the
  upstream drift and documentation checks. NOT RUN never counts as PASS.
- Sources were obtained from the internal archive using the requested release
  tags. Some released suites still require older direct inputs and historical
  fixtures, so public-only fresh-root reproduction is not proven. Resolved
  commits are evidence, not cross-mirror input refs.
- The generic build kit has no semantic library manifest or Python check.py.
  It is inventoried and its dependency floor is checked, while the index
  explicitly reports the unavailable source card. The scenarios card uses the
  current candidate without claiming its future tag has been published.
- Exactly one offline Nix attempt failed resolving an uncached public input;
  see [packaging](packaging.md) and [receipt](nix-evidence.json). No retry or
  lockfile is committed. Native template, executable CCTV and live integration
  omissions retain their own NOT RUN rows.

## Prior evidence and remaining work

The [preceding full](acceptance-0.7.1.json) and
[fast](acceptance-fast-0.7.1.json) reports, [historical drift](drift-0.7.1.md),
[harness proof](harness-proof.json) and [consumer correction](consumer-correction.json)
retain earlier measurements and fixture identities. Their old versions are
historical evidence, not active public input pins.

This full process began at `e941f40`; the local runner correction is committed
at `291ebc4` and measured separately. No previous suite report was reused.
Remaining work is to release compatible upstream pins and repair their broken
links, resolve Nix inputs, and obtain a corrected complete full run while
addressing its duration. No pull request is merged by this work.
