# usdaeco-scenarios — Pinned family acceptance

## Use case

Check that released family repositories work together on the published
`demo-datacentre-01`. [Acceptance](docs/acceptance.md) records measured results;
[the workflow](docs/usecase.md) explains what the gate proves.

## The schema on an index card

This gate defines no schema. [family.json](family.json) inventories 24
repositories: 22 released dependencies, this candidate and a private documentation seed.
[dependencies.json](dependencies.json) pins 19 family dependencies
and two native kits. The scenarios entry names this release; the
candidate is checked without recursively running its own gate. The generic
build kit is inventoried separately from the executable semantic suites.

## The example

<!-- demo:start -->
Walk through `demo-datacentre-01` in train `aeco-0.8.0`. Each step uses its repository's released findings and one recorded render. Public links name intended mirror locations; network availability is not checked.

**1. CCTV** — Start with visibility: 45 sensors generate 45 sectors. CriticalDoors covers 11/11 fixed targets; Privacy reports 0 covered exclusions.

[Example and output](https://github.com/criad-com/usdaeco-cctv/tree/v0.5.6/examples/datacentre) · [Findings](https://github.com/criad-com/usdaeco-cctv/tree/v0.5.6/examples/datacentre/expected/findings.json)
Data source: `v0.4.8` / `base`.

![cctv example](https://github.com/criad-com/usdaeco-cctv/raw/v0.5.6/examples/datacentre/renders/overview.png)

**2. CLASH** — Then inspect physical interference across 3 measured pairs: through-wall: mesh hard, exact hard; over-tray: mesh undecidable, exact clearance; tangent: mesh undecidable, exact touching. Exact geometry resolves the mesh uncertainty.

[Example and output](https://github.com/criad-com/usdaeco-clash/tree/v0.2.3/examples/datacentre) · [Findings](https://github.com/criad-com/usdaeco-clash/tree/v0.2.3/examples/datacentre/expected/findings.json)
Data source: `v0.4.8` / `clash`.

![clash example](https://github.com/criad-com/usdaeco-clash/raw/v0.2.3/examples/datacentre/renders/overview.png)

**3. PLAN** — Sequence the pod delivery and ceiling closure. Programme A reports AccessAfterEnclosure (4), WorkspaceOccupied (1), EnclosureBeforeInspection (2). Programme B reports 0 such findings after the sequence changes; work dates remain programme data.

[Example and output](https://github.com/criad-com/usdaeco-plan/tree/v0.1.4/examples/datacentre) · [Findings](https://github.com/criad-com/usdaeco-plan/tree/v0.1.4/examples/datacentre/expected/findings.json)
Data source: `v0.4.8` / `pod`.

![plan example](https://github.com/criad-com/usdaeco-plan/raw/v0.1.4/examples/datacentre/renders/A.0.png)

**4. COMPLIANCE** — Check the iris readers against illustrative requirements: 10 readers pass and 1 fails across 11 readers, producing 2 clause failures. These are demonstration clauses, not a regulatory certification.

[Example and output](https://github.com/criad-com/usdaeco-compliance/tree/v0.1.3/examples/datacentre) · [Findings](https://github.com/criad-com/usdaeco-compliance/tree/v0.1.3/examples/datacentre/expected/findings.json)
Data source: `v0.4.8` / `iris`.

![compliance example](https://github.com/criad-com/usdaeco-compliance/raw/v0.1.3/examples/datacentre/renders/overview.png)

**5. REPEAT** — Finally compare repeated office floors: 1 changed wall and 1 extra door. The released example reports a partition-length delta of 3.2 m and a door delta of 1. Its pinned floor source is recorded below; newer data variants are checked separately.

[Example and output](https://github.com/criad-com/usdaeco-repeat/tree/v0.2.1/examples/datacentre) · [Findings](https://github.com/criad-com/usdaeco-repeat/tree/v0.2.1/examples/datacentre/expected/findings.json)
Data source: `v0.4.8` / `floors`.

![repeat example](https://github.com/criad-com/usdaeco-repeat/raw/v0.2.1/examples/datacentre/renders/overview.png)

<!-- demo:end -->

## Build and check

Set and export `PYTHON` to a Python with USD, IfcOpenShell, numpy, pytest, Jinja2, Pillow
and the family runtime dependencies. No package installation or setuptools
is required. Set `AECO_GIT_BASE` to your repository mirror base if needed;
`AECO_KIT_GIT_BASE` selects a separate native-kit mirror. The checkout command
requires empty destination directories and verifies each checkout against its release tag. Resolved commit identities
are recorded as run evidence; they are not cross-mirror input pins.
The scenarios entry links this checkout into the family root, so a candidate
can be checked before its release tag is published.
Before the full command, also export `AECO_BLENDER`, `USD_SOLID_RUNTIME` and
`USD_SOLID_OCCT_RUNTIME` for the available Blender executable and matching
immutable native runtimes. The runtime directories contain `paths.json`; their
release requirements are linked from the family index.

```sh
export AECO_FAMILY_ROOT="$PWD/out/family"
env -u PYTHONPATH "$PYTHON" run_scenarios.py checkout --output "$AECO_FAMILY_ROOT"
export TOOLCHAIN_DIR="$AECO_FAMILY_ROOT/usdaeco-toolchain"
export AECO_CORE_ROOT="$AECO_FAMILY_ROOT/usdaeco-core"
env -u PYTHONPATH PYTHONPATH="$AECO_CORE_ROOT:$PWD" "$PYTHON" check.py --output out/gate
env -u PYTHONPATH -u AECO_FAMILY_ROOT "$PYTHON" -m pytest -q
env -u PYTHONPATH "$PYTHON" run_scenarios.py demo --output out/demo
```

The gate audits revisions and builds disposable copies in `out/gate/sources`.
Standalone pytest uses that recorded disposable runtime; its command clears
the acquisition root so collection does not select the source archive.
It requires all eight core validators to load through UsdValidation.
Every repository check runs from source with an explicit import environment.
Four independent suites run concurrently, with two USD worker threads each;
`--jobs 1` serializes them. The report includes the whole gate's wall-clock
duration and fails the six-minute budget when exceeded. Choose a fresh output
directory for independent acceptance. `--ifc-only` disables native Bonsai and
live integrations; their rows remain NOT RUN with reasons.

For a shorter audit, use a separate output directory:

```sh
env -u PYTHONPATH PYTHONPATH="$AECO_CORE_ROOT:$PWD" "$PYTHON" check.py --profile fast --output out/fast
```

The fast profile verifies the train, source cards, variant manifests, committed
result inventories and relocated plugin-free stages. It builds the consumer
plugin set and runs this repository's tests. Full repository suites and derived
consumer reproductions are NOT RUN: those entry points combine their checks
with publication, render or native execution. A fast result does not establish
fresh publication parity or replace the full profile.

`run_scenarios.py demo` is the source-checkout form of `scenarios demo`. It exports
one local README, five exact findings files and five recorded renders. The
story above uses those same artifacts and the gate checks its freshness.

Set `AECO_BLENDER` to a Blender executable with Bonsai and IfcOpenShell for
native integration cases. Set `USD_SOLID_RUNTIME` and `USD_SOLID_OCCT_RUNTIME`
to immutable built runtime directories containing `paths.json`. Their suites
verify build revisions and compiled source manifests, then use their own
ABI-compatible Python subprocesses. A matching runtime version alone is
insufficient; its dependency revisions must also match the kit release.
The generic native kits are recorded under `dependencies.json.nativeKits`;
they are outside the seven-library codeless flake plugin set.

```sh
env -u PYTHONPATH "$PYTHON" check.py --structure-only
nix flake check --offline --no-update-lock-file
```

Flake inputs use public names. For a private mirror, follow the toolchain's
external registry instructions or use `--override-input <name> path:<checkout>`
for every direct input. No private registry or lockfile belongs in this tree.
[Packaging](docs/packaging.md) records the one Nix attempt and execution limits.

## Family

Train `aeco-0.8.0` uses core v0.9.5, axis v0.1.5 and toolchain v0.3.10.
Datacentre v0.4.9 supplies the published variants; repeat v0.2.1 supplies the
repeated-floor example. Requirements are ranges copied from released manifests.
Inventory validation admits the private metadata entry; separate strict
validation checks released compatibility. A local adapter projects generic
kit names and kinds for the semantic-family validator, preserving tags and ranges. The
[generated family index](docs/family/README.md) reads source cards from exact
tags and has a freshness check against those sources.

Each family entry declares `released` (the tag executed by the gate) and
`floor` (the oldest permitted direct dependency pin). Direct pins must lie
inside this inclusive interval and satisfy their declared requirement ranges.
The released version must also satisfy those ranges. A pin carrying commit evidence
is verified against its own tag, accepting an explicitly recorded public commit
when supplied. The floor is the first public release, so older direct pins fail. The `tag` field is a checked alias of
`released` for the pinned toolchain index generator. Declarations under `dependencies.json.fixtures` are inventoried separately and never satisfy direct requirements or waive a direct mismatch.
OpenUSD inputs remain external. The generic build kit is subject to its public floor.
The nine-section use-case and published-result checks follow the toolchain's
scope: use-case and integration repositories; reduced kinds are exempt.

## Layout

`check.py` / `check_all.py`: gate and reports; `family.py`: isolated sources and
runtime; `family_manifest.py`: generic-kit inventory adapter; `testenv/`:
regression tests; `scenarios/`: published-stage checks; `demo/`: synthetic
roundtrip; `baselines/`: synthetic inputs; `docs/`: acceptance and provenance.
`out/` and `.work/` are disposable and uncommitted.

## Status

Version 0.8.0 candidate. Full: **124 checks, 5 failed, 25 not run; 94 PASS; 1247.70 s**.
Fast: **53 checks, 3 failed, 23 not run; 27 PASS; 79.25 s**. Drift: **32 upstream direct pins**.
Local structure: **29/0**; pytest: **134 passed**. Build-up's runner correction
passes a separate **67/67** suite. Four upstream broken links and the full
wall-clock budget remain unresolved; complete acceptance is not proven.
The [acceptance report](docs/acceptance.md) preserves the original measurements,
[focused correction](docs/buildup-correction.json) and historical evidence.
See [remaining work](BLOCKED.md). NOT RUN never counts as PASS.

## Licence

[MIT](LICENSE). Copyright (c) 2026 Criad.

Runtime dependencies retain their licences: OpenUSD (Apache-2.0-style TOST),
numpy, Jinja2 and packaging (BSD), PyYAML, pydantic and openpyxl (MIT),
Pillow (HPND), embreex (Apache-2.0), and IfcOpenShell (LGPL-3.0, imported only).
OCCT is LGPL-2.1 and dynamically linked only by the optional native kit.
No third-party code is vendored.
