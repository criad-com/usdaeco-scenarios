# Release packaging acceptance — 0.7.1

[dependencies.json](../dependencies.json) records exact tags and revisions.
[family.json](../family.json) selects train `aeco-0.7.0`, including toolchain
v0.3.7 and datacentre v0.4.6. All 22 tagged repositories are available; the
23rd entry is a documentation seed. The scenarios source card names v0.7.0;
the current candidate runs its structure and regression checks without recursion.

## Sources and execution scopes

The checkout command clones exact tags into a fresh root. The gate copies
21 dependency repositories into disposable sources, verifies revisions, builds
seven codeless libraries with core first, and requires all eight core validators
to import and load through UsdValidation. Sibling checkouts remain read-only.

The consumer uses the train. Repository suites use their declared direct
inputs, resolved from `dependencies.json.repos` and `nativeKits`, plus any
explicit flake inputs or byte-qualified executable inputs under `fixtures`. The evidence records each
selection as `direct` or `fixture`. Synthetic rejection cases and archived
receipts remain data. They never replace a direct dependency.

Direct pins are checked inside each dependency’s inclusive floor–released
interval. The selected immutable tags contain zero mismatches; see
the [measured dependency audit](drift-0.7.1.md). All 35 requirement ranges contain the
declared and released versions. Declared fixture inputs remain separate.
All 11 story-bearing repositories retain their nine sections and published
result trees (22 checks).

Repository suites select their own declared toolchains for both environment
variables and Python imports. Consumer builds and scenarios lint use train
v0.3.7. Plan v0.1.2 declares its 480-second example budget; solid v0.1.3
pins toolchain v0.3.7. Toolchain v0.3.7 declares core v0.8.4 as a fixture for
legacy template tests. Datacentre retains its byte-qualified toolchain v0.3.5.
The compatibility consumers retarget their ignored inputs/source aliases before
overriding the data stage, so S29 archives paths through their own inputs.
Reproductions retain the published source version:
the five walkthrough examples all declare datacentre v0.4.5, while independent
consumer checks use train v0.4.6. Datacentre itself declares core v0.8.4 and
IFC v0.1.0 as byte-qualified generation fixtures, distinct from its validation
core and current transport inputs.

The native kits use existing immutable runtimes whose build revisions match
their released dependency manifests. Their checks run through their own
ABI-compatible Python processes. Native binaries do not enter the codeless
consumer runtime. Bonsai is explicitly disabled by `--ifc-only`; live
integration and unavailable native-template rows remain NOT RUN.

## Full and fast profiles

Follow the [README](../README.md). Use a fresh `--output` directory per profile.
The full profile reproduces released repository suites and derived consumers.
Four independent suites run concurrently, with two USD worker threads each.
The 360-second target includes source isolation, codeless builds, requested
suites, consumers, renders and regression checks; exceeding it remains FAIL.
Source acquisition is measured separately.

`--profile fast` retains revision/range/drift checks, source-card freshness,
variant counts and hashes, committed example inventories, relocated stock USD
composition, the consumer plugin build, scenarios structure and regressions.
It skips full repository suites because their entry points combine those checks
with publication or native reproduction. It also skips fresh examples, consumer
roundtrips, renders and determinism runs. Every omission is NOT RUN, and a fast
pass cannot establish fresh publication parity.

The optional `--reuse-library-report` mode requires identical source revisions
and a full-profile report. It labels reused successful results and reruns failed
suites. It is not used for fresh-root acceptance. Timing and diagnostic reruns
are recorded separately in [acceptance](acceptance-0.7.1.md).

## Structure and packaging

The unmodified toolchain v0.3.7 structure lint reports 29 rules. The gate's
existing generic-kit adapter projects only the two native kit names/kinds for
the semantic family validator, preserving their libraries, tags and ranges.
The source-card index is generated from exact released sources and checked for
freshness. Native kits remain outside the seven-library codeless flake set.

Exactly one Nix attempt was made for this candidate:

```sh
nix flake check --offline --no-update-lock-file --option restrict-eval true --option allowed-uris '' --option substituters ''
```

It failed resolving the public axis v0.1.3 input with HTTP 404. No retry or
lockfile is committed. Nix is not proven; Python and native runtime checks do
not establish this flake's acceptance.

## Historical evidence

The files named `datacentre-evidence`, `release-evidence`, `packaging-evidence`,
`residual-samples`, `revit-reference`, `suite-diagnosis` and
`solid-publication-drift` and `focused-checks` retain earlier measurements. Their embedded versions
or referenced tags define their scope. Current measurements are in
[acceptance](acceptance-0.7.1.md); historical evidence is not a current PASS.
