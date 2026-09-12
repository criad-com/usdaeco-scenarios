# Release packaging acceptance — 0.8.0

[family.json](../family.json) selects the public train `aeco-0.8.0`.
Every active reference in [dependencies.json](../dependencies.json) and the
flake uses a release tag under the public `criad-com` organization. Resolved
commit identities are recorded in run evidence because public orphan releases
can differ from the internal mirror's commits. Historical fixtures retain their
own declarations and never satisfy direct requirements.

## Sources and execution scopes

The inventory contains 24 entries: 22 released dependencies, the scenarios
candidate and private, unpinned metadata. Twenty-one dependencies have Python
acceptance suites; the generic build kit has no semantic library manifest or
Python gate. Its public floor still applies to direct dependency pins. The
index reports its missing source card explicitly and marks scenarios as the
current candidate, without claiming that its tag has already been published.

The gate clones exact tags into a fresh disposable root, audits their resolved
commits and clean source state, and builds seven codeless consumer libraries.
All eight core validators must import and load through UsdValidation.
Repository suites select their own declared toolchains and inputs; consumer
builds and scenarios lint use toolchain v0.3.10. The data-centre publication
uses its vendored, byte-qualified generation fixtures while modern dependency
builds use its validation core. Fixtures with recorded historical revisions
remain separate from active public pins.

Full acceptance uses available Blender and immutable native Solid runtimes.
The native suites verify compiled-source and dependency receipts using their
own compatible subprocesses. No dependency installation or native rebuild is
performed. Live integration and native-template gaps retain NOT RUN rows.

## Full and fast profiles

Follow the [README](../README.md), with a fresh output directory per profile.
The full profile runs released suites, publication reproductions, derived
consumers and regressions. The 360-second budget includes source isolation,
builds, suites and consumer checks. Four independent suites run concurrently.
The fast profile checks source pins, committed publication inventories,
relocated vanilla USD stages and local regressions. It marks full suite and
consumer reproductions NOT RUN, and does not establish publication parity.

[Acceptance](acceptance.md) records the single full run, the separate fast
measurement and exact failures. Upstream direct pins below their public floors
remain drift even when those older tags can be retrieved from the internal
archive. This run does not establish public-only fresh-root reproduction.

## Nix

Exactly one offline attempt was made:

```sh
nix flake check --offline --no-update-lock-file --option restrict-eval true --option allowed-uris '' --option substituters ''
```

Outbound IP connections were denied for the attempt. It exited 1 after
0.13 seconds while resolving the uncached public board v0.1.4 input. Nix is
not proven. No retry or lockfile is committed. See [receipt](nix-evidence.json).

## Historical evidence

The [preceding full report](acceptance-0.7.1.json),
[fast report](acceptance-fast-0.7.1.json), [acceptance narrative](acceptance-0.7.1.md)
and [packaging record](packaging-0.7.1.md) preserve the earlier runner diagnosis.
The focused harness, source-alias and evaluator-idempotence proofs remain in
[harness-proof.json](harness-proof.json) and
[consumer-correction.json](consumer-correction.json). Their embedded versions
define their scope; they are not current PASS evidence.
