# Family 0.7.1 acceptance

The fresh-root full gate reports **122 checks, 7 failed, 28 not run; 87 PASS; 931.50 s**. Fast reports **53 checks, 0 failed, 23 not run; 30 PASS; 77.44 s**. Dependency drift is **0**. The full gate's exact failed rows are retained below; corrected full acceptance is not proven.

[Full report](acceptance-0.7.1.json), [fast report](acceptance-fast-0.7.1.json), [source inventory](release-inventory-0.7.1.json) and [drift](drift-0.7.1.md) retain the measured scope.

## Acceptance

| Requirement | Measured result | Status |
|---|---|---|
| Fresh-root full gate, excluding wall-clock budget | 6 failed rows | FAIL |
| revision pins | 21/21 exact sources | PASS |
| drift dependency train intervals | 121/121; 0 mismatches | PASS |
| drift requirement ranges | 35/35; 0 mismatches | PASS |
| drift use-case publication contracts | 22/22; 0 mismatches | PASS |
| family index freshness | 23 rows; live tagged sources | PASS |
| five-use-case walkthrough | 5 released example outputs and 5 renders; README story matches | PASS |
| new use-case PASS coverage | 5/5 repositories have at least one measured PASS row | PASS |
| core validator registry | 8/8 loaded through UsdValidation | PASS |
| scenarios check.py | 29/29 structure checks; current candidate, no recursive gate | PASS |
| gate regression tests | 127 passed in 14.07s | PASS |
| sanitization | 109 files; 0 violations | PASS |
| buildup check.py | 58/59; 0 NOT RUN; 43.6s | FAIL |
| cctv-exec check.py | 32/54; 21 NOT RUN; 0.44s | FAIL |
| datacentre check.py | no acceptance count; see datacentre.log | FAIL |
| wall published clash compatibility | see wall-clash-consumer.log | FAIL |
| pipe published clash compatibility | see pipe-clash-consumer.log | FAIL |
| DC-idempotence | 0/60 views reused; stable results | FAIL |
| family wall-clock budget | 931.5s / 360s; full profile; 4 suite processes; source isolation, builds, suites and consumers included | FAIL |
| Fast profile | 53 checks, 0 failed, 23 not run; 30 PASS; 77.44 s | PASS |
| Nix | One attempt; public axis input returned HTTP 404 | NOT PROVEN |
| Final candidate verification | 29 structure checks, 0 failed; 128 pytest passed; 111 files, 0 term violations | PASS |
| Corrected CCTV consumer (separate) | 53 rows, 0 failed, 20 not run; 60/60 views reused; 41.487 s | PASS |

## One fresh-root full run

All 22 tagged entries were acquired in a new root; 21 dependency revisions were verified in disposable gate checkouts. The scenarios card names v0.7.0; this candidate runs without recursion. No previous suite report was reused and the full gate was run once.

The full process started at `92659f8dd211`. Suite harness selection and override source aliases exposed two runner defects during that execution. The correction at `1dcf944f9efa` is covered by 128 final regression tests, the [focused dependency proof](harness-proof.json), and a separate [CCTV consumer run](consumer-correction.json). Fast ran at `7921732` and omits repository suites. All original failed rows remain in the full report.

## Exact remaining full-run failures

| Gate | Result | Status |
|---|---|---|
| buildup check.py | 58/59; 0 NOT RUN; 43.6s | FAIL |
| cctv-exec check.py | 32/54; 21 NOT RUN; 0.44s | FAIL |
| datacentre check.py | no acceptance count; see datacentre.log | FAIL |
| wall published clash compatibility | see wall-clash-consumer.log | FAIL |
| pipe published clash compatibility | see pipe-clash-consumer.log | FAIL |
| DC-idempotence | 0/60 views reused; stable results | FAIL |
| family wall-clock budget | 931.5s / 360s; full profile; 4 suite processes; source isolation, builds, suites and consumers included | FAIL |

The three suite failures all originate from the same harness substitution:

| Suite | Failed check | Required harness | Supplied harness |
|---|---|---|---|
| build-up | checked dependency releases | v0.3.5 | v0.3.7 |
| CCTV-exec | tested dependency versions | v0.3.5 | v0.3.7 |
| datacentre | runtime byte validation before acceptance | v0.3.5 | v0.3.7 |

CCTV idempotence also failed in the full run: the example replays a v0.5.3 receipt while the evaluator runs v0.5.4. The corrected consumer establishes a current-version baseline before reopening the stage to measure persistent reuse. See the separate [consumer correction](consumer-correction.json); this does not replace the original full-run row.

## Timing and scope

Full: 122 checks, 7 failed, 28 not run; 87 PASS; 931.50 s. Fast: 53 checks, 0 failed, 23 not run; 30 PASS; 77.44 s. The profiles use separate output roots and do not overlap. The budget row measures elapsed time before final report writing; report seconds include that write. The full duration includes the datacentre startup failure and does not measure a complete corrected run. Source acquisition is separate: 1.95 s for 22 tagged checkouts.

The full scope includes source isolation, builds, suites, consumers and renders. Fast verifies source revisions, train intervals and ranges, index freshness, manifests and committed inventories, relocated plugin-free stages, the consumer plugin build, structure and regressions. Fast does not prove fresh publication parity. NOT RUN never counts as PASS.

## Released suites in the full run

| Repository | Released ref | Checks | Failed | Not run | Seconds |
|---|---|---|---|---|---|
| core | v0.9.3 | 71 | 0 | 0 | 223.53 |
| axis | v0.1.3 | 53 | 0 | 0 | 43.70 |
| toolchain | v0.3.7 | 65 | 0 | 0 | 610.77 |
| buildup | v0.2.2 | 59 | 1 | 0 | 43.60 |
| wall | v0.2.3 | 87 | 0 | 0 | 71.43 |
| pipe | v0.2.3 | 82 | 0 | 0 | 93.87 |
| cctv | v0.5.4 | 159 | 0 | 0 | 117.82 |
| cctv-exec | v0.2.2 | 54 | 1 | 21 | 0.44 |
| sync | v0.5.3 | 52 | 0 | 0 | 7.51 |
| ifc | v0.2.1 | 101 | 0 | 0 | 609.59 |
| revit | v0.1.3 | 48 | 0 | 0 | 56.48 |
| datacentre | v0.4.6 | 0 | 0 | 0 | 0.08 |
| board | v0.1.3 | 70 | 0 | 0 | 23.04 |
| plan | v0.1.2 | 51 | 0 | 2 | 148.05 |
| compliance | v0.1.1 | 45 | 0 | 0 | 146.41 |
| typical | v0.1.1 | 43 | 0 | 0 | 68.60 |
| clash | v0.2.1 | 48 | 0 | 0 | 142.06 |
| solid | v0.1.3 | 50 | 0 | 0 | 121.34 |
| usdSolid | v0.1.2 | 28 | 0 | 0 | 9.38 |
| usdSolidOcct | v0.1.1 | 28 | 0 | 0 | 11.63 |

A suite with zero checks and no acceptance summary failed to start; zero reported failed checks is not a PASS. Repository summaries can include informational records; they are not additional family PASS rows.

## Published variants

| Variant | Elements | Levels | Spaces | Meshes | Ports | Unparented | Unclassified |
|---|---|---|---|---|---|---|---|
| base | 2954 | 2 | 33 | 2987 | 6212 | 0 | 2 |
| floors | 2983 | 3 | 39 | 3022 | 6212 | 0 | 2 |
| pod | 2977 | 2 | 35 | 3012 | 6238 | 0 | 2 |
| clash | 2980 | 2 | 35 | 3015 | 6244 | 0 | 2 |
| iris | 2954 | 2 | 33 | 2987 | 6212 | 0 | 2 |

The independent consumers checked these published counts and layer hashes. The five-step demo uses its owners’ datacentre v0.4.5 examples; independent consumers use train v0.4.6.

## Deviations

- The single full run used train toolchain v0.3.7 for repository suites. Build-up and CCTV-exec require their declared v0.3.5, and datacentre v0.4.6 requires its exact runtime bytes. The corrected runner preserves each suite's declared toolchain in both imports and environment. Focused regression and dependency-resolution checks pass, but those suites were not rerun; corrected full-suite acceptance remains not proven.
- Wall and pipe compatibility consumers retained the older source alias during a train-stage override, failing S29. The runner now retargets that alias; copies of both failed archives pass S29 after rebasing. Complete consumer reruns were not performed.
- The original CCTV idempotence row compared a historical v0.5.3 example receipt with the v0.5.4 evaluator, causing 0/60 cache hits. The corrected check establishes a current-version baseline before measuring reuse on a reopened stage. The targeted consumer reports 53 rows, 0 failed, 20 not run, and 60/60 views reused in 41.487 s; it is separate from the full run.
- The full 360-second wall-clock target is exceeded and remains FAIL.
- Fast omits full suites and fresh publication/consumer reproduction; every omission remains NOT RUN.
- Native Bonsai, live integrations and unavailable native templates remain NOT RUN under the declared IFC-only scope.
- Nix is not proven after the one input-resolution failure; no retry was made.

## What is left

Run the corrected build-up, CCTV-exec and datacentre suites plus the two clash consumers, then obtain a complete full-gate acceptance report when another run is authorized; review the 360-second full budget. No sibling repository was changed and no PR was merged.

## Full-run rows

| Gate | Result | Status |
|---|---|---|
| revision pins | 21/21 exact sources | PASS |
| family inventory | 23 repositories, 13 libraries; 0 sibling manifests compared; 0 legacy manifests unavailable; 0 checkouts absent; sibling comparison not requested; inventory only: 1 unreleased seeds; 0 incompatible requirements; compatibility not proven | PASS |
| released family compatibility | 22 repositories, 13 libraries; 0 sibling manifests compared; 0 legacy manifests unavailable; 0 checkouts absent; sibling comparison not requested | PASS |
| drift dependency train intervals | 121/121; 0 mismatches | PASS |
| drift requirement ranges | 35/35; 0 mismatches | PASS |
| drift use-case publication contracts | 22/22; 0 mismatches | PASS |
| family index freshness | 23 rows; live tagged sources | PASS |
| family release manifests | 21/21 versions and declared ranges match tagged manifests | PASS |
| released requirements | 56/56 tags and declared requirements | PASS |
| optional cctv-exec compatibility | Declared ranges satisfied: usdAeco >=0.9.2,<1.0 against released 0.9.3; usdAecoCctv >=0.5.2,<0.6 against released 0.5.4; outside the runtime plugin set; native execution not tested | PASS |
| meta check.py | documentation seed; no executable suite | NOT RUN |
| links before builds | 45/45 roots | PASS |
| one plugin path | 7/7 libraries | PASS |
| core check.py | 71/71; 0 NOT RUN; 223.53s | PASS |
| axis check.py | 53/53; 0 NOT RUN; 43.7s | PASS |
| toolchain native templates | installed native template artifacts unavailable; source suite runs; no dependency downloads attempted | NOT RUN |
| toolchain check.py | 65/65; 0 NOT RUN; 610.77s | PASS |
| buildup check.py | 58/59; 0 NOT RUN; 43.6s | FAIL |
| wall check.py | 87/87; 0 NOT RUN; 71.43s | PASS |
| pipe check.py | 82/82; 0 NOT RUN; 93.87s | PASS |
| cctv check.py | 159/159; 0 NOT RUN; 117.82s | PASS |
| cctv-exec check.py | 32/54; 21 NOT RUN; 0.44s | FAIL |
| sync check.py | 52/52; 0 NOT RUN; 7.51s | PASS |
| ifc check.py | 101/101; 0 NOT RUN; 609.59s | PASS |
| ifc scenarios | 21/21; IFC entry point | PASS |
| ifc camera scenarios | 9/9; IFC entry point | PASS |
| ifc datacentre scenarios | 9/9; IFC entry point | PASS |
| bonsai check.py | native host explicitly disabled | NOT RUN |
| revit check.py | 48/48; 0 NOT RUN; 56.48s | PASS |
| datacentre check.py | no acceptance count; see datacentre.log | FAIL |
| board check.py | 70/70; 0 NOT RUN; 23.04s | PASS |
| plan check.py | 49/51; 2 NOT RUN; 148.05s | PASS |
| compliance check.py | 45/45; 0 NOT RUN; 146.41s | PASS |
| typical check.py | 43/43; 0 NOT RUN; 68.6s | PASS |
| clash check.py | 48/48; 0 NOT RUN; 142.06s | PASS |
| solid check.py | 50/50; 0 NOT RUN; 121.34s | PASS |
| usdSolid check.py | 28/28; 0 NOT RUN; 9.38s | PASS |
| usdSolidOcct check.py | 28/28; 0 NOT RUN; 11.63s | PASS |
| wall published clash compatibility | see wall-clash-consumer.log | FAIL |
| pipe published clash compatibility | see pipe-clash-consumer.log | FAIL |
| scenarios check.py | 29/29 structure checks; current candidate, no recursive gate | PASS |
| scenario + S4 parity | split integration case sets; production roundtrip parity is measured separately | NOT RUN |
| revit scenarios | live Revit execution outside this gate | NOT RUN |
| cctv-exec native | native consumer unavailable; source check recorded separately | NOT RUN |
| core validator registry | 8/8 loaded through UsdValidation | PASS |
| published variant base | elements=2954; levels=2; spaces=33; meshes=2987; ports=6212; unparented=0; unclassified=2; manifest counts and layer hashes | PASS |
| published variant floors | elements=2983; levels=3; spaces=39; meshes=3022; ports=6212; unparented=0; unclassified=2; manifest counts and layer hashes | PASS |
| published variant pod | elements=2977; levels=2; spaces=35; meshes=3012; ports=6238; unparented=0; unclassified=2; manifest counts and layer hashes | PASS |
| published variant clash | elements=2980; levels=2; spaces=35; meshes=3015; ports=6244; unparented=0; unclassified=2; manifest counts and layer hashes | PASS |
| published variant iris | elements=2954; levels=2; spaces=33; meshes=2987; ports=6212; unparented=0; unclassified=2; manifest counts and layer hashes | PASS |
| plan fresh example findings | Programme A: {'AccessAfterEnclosure': 4, 'WorkspaceOccupied': 1, 'EnclosureBeforeInspection': 2}; B: 0 findings; XER/MSPDI agree | PASS |
| compliance fresh example findings | 10 pass / 1 fail readers; 2 clause failures | PASS |
| typical fresh example findings | {'changed': 1, 'extra': 1} floor differences; 3.2 m / 1 door delta | PASS |
| clash fresh example findings | 3 mesh/exact pairs; 5 mm gap and exact touching resolved | PASS |
| solid fresh example findings | 109/109 exact bodies; 109 twins within tolerance; 42 walls / 6 pipes measured | PASS |
| solid publication determinism | 2 temporary roots; fresh publication and authored-layer reflattening; normalized hashes, bytes and prim counts compared | PASS |
| new use-case PASS coverage | 5/5 repositories have at least one measured PASS row | PASS |
| five-use-case walkthrough | 5 released example outputs and 5 renders; README story matches | PASS |
| cctv scenarios | 31/31 (embree) | PASS |
| demo ifc + bonsai | 3 edits per host; cleared intent | NOT RUN |
| demo parity | 0/0 | NOT RUN |
| roundtrip profile | 0 errors | PASS |
| cctv demo derivation | 4/4 sensors | PASS |
| cctv demo steps | 6/6 steps | PASS |
| cctv demo render | 2/2 images | PASS |
| datacentre build | consumer uses published stages; generator timing is in the data repository check | NOT RUN |
| DC-build | published dist/base; source mode pinned; generator not invoked | PASS |
| DC-layer dc.geometry.usdc | 332637 bytes; manifest hash matches | PASS |
| DC-layer dc.semantics.usdc | 1471556 bytes; manifest hash matches | PASS |
| DC-layer dc.usda | 517 bytes; manifest hash matches | PASS |
| DC-count elements | 2954/2954 | PASS |
| DC-count levels | 2/2 | PASS |
| DC-count spaces | 33/33 | PASS |
| DC-count meshes | 2987/2987 | PASS |
| DC-count ports | 6212/6212 | PASS |
| DC-count unparented | 0/0 | PASS |
| DC-count unclassified | 2/2 | PASS |
| DC-identities | 2954 unique element identities | PASS |
| DC-phases | 2954/2954 authored asset phases | PASS |
| DC-convert | published conversion; no USD type or composition errors | PASS |
| DC-profile | 0 core errors; 2 non-errors | PASS |
| DC-vanilla-base | published base composes with no family plugins | PASS |
| DC-example findings | CCTV committed expected findings match | PASS |
| DC-import | 45 cameras; 45 sensors; 3 types; 7 presets | PASS |
| DC-derive | 45 sensors; 45 sectors; 3 tours | PASS |
| DC-critical-doors | 11/11 fixed targets; 0 exclusions covered; expected findings match | PASS |
| DC-privacy-baseline | 0/0 fixed targets; 0 exclusions covered; expected findings match | PASS |
| DC-idempotence | 0/60 views reused; stable results | FAIL |
| DC-determinism | two independent compositions; normalized stage, findings and study results | PASS |
| DC-stale | driver edit invalidates prior study | PASS |
| DC-results-incomplete | removed result is diagnosed | PASS |
| DC-render lobby | 576x360; 95395 bytes; mean 0.683810; standard deviation 0.246999 | PASS |
| DC-render lookthrough | 576x360; 354001 bytes; mean 0.650514; standard deviation 0.264553 | PASS |
| DC-render overview | 576x360; 87286 bytes; mean 0.162708; standard deviation 0.320483 | PASS |
| DC-render | 3/3 views; 33 extent guides hidden; diagnostic camera light 160% | PASS |
| DC-vanilla | 3 consumer stages compose with no family plugins | PASS |
| DC-source unchanged | 17 published source and CCTV input/artifact files unchanged | PASS |
| DC-system | released CCTV example does not supply this historical study or policy case | NOT RUN |
| DC-external | released CCTV example does not supply this historical study or policy case | NOT RUN |
| DC-corridors | released CCTV example does not supply this historical study or policy case | NOT RUN |
| DC-yard-day | released CCTV example does not supply this historical study or policy case | NOT RUN |
| DC-yard-night | released CCTV example does not supply this historical study or policy case | NOT RUN |
| DC-lobby | released CCTV example does not supply this historical study or policy case | NOT RUN |
| DC-revit-parity | released CCTV example does not supply this historical study or policy case | NOT RUN |
| DC-column | released CCTV example does not supply this historical study or policy case | NOT RUN |
| DC-tray | released CCTV example does not supply this historical study or policy case | NOT RUN |
| DC-temporary | released CCTV example does not supply this historical study or policy case | NOT RUN |
| DC-privacy | released CCTV example does not supply this historical study or policy case | NOT RUN |
| DC-hall-rule | released CCTV example does not supply this historical study or policy case | NOT RUN |
| DC-noc-turn | released CCTV example does not supply this historical study or policy case | NOT RUN |
| DC-ptz-duty | released CCTV example does not supply this historical study or policy case | NOT RUN |
| DC-night-override | released CCTV example does not supply this historical study or policy case | NOT RUN |
| DC-sync-ifc | published USD has no editable native document; integration data-centre cases run separately | NOT RUN |
| DC-sync-bonsai | published USD has no editable native document; integration data-centre cases run separately | NOT RUN |
| DC-revit-reference | historical evidence does not match the current released artifacts | NOT RUN |
| DC-revit | live Revit execution outside this gate | NOT RUN |
| datacentre sanitization | 37 text/stage assets; 0 violations | PASS |
| DC-budget | 39.097s; 240s budget | PASS |
| gate regression tests | 127 passed in 14.07s | PASS |
| sanitization | 109 files; 0 violations | PASS |
| links at end | 45/45 roots | PASS |
| family wall-clock budget | 931.5s / 360s; full profile; 4 suite processes; source isolation, builds, suites and consumers included | FAIL |
