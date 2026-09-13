# Release packaging acceptance — 0.9.0

Train `aeco-0.9.0` adds suite v0.3.0. The 24 existing released tags and floors
remain unchanged. Scenarios v0.9.0 is the current candidate; the released
v0.8.1 pin remains truthful and matches the suite's scenarios gitlink.

Sources are acquired at exact tags in disposable checkouts. The suite alone
uses `--depth 1 --no-recurse-submodules`, both through `checkout` and its gate.
Its 23 submodule directories remain uninitialized. The suite is outside the
consumer plugin set and existing repository-execution loop; both profiles
add the same source-only provenance row. No new flake inputs are required.

The fast run passes 54 checks with zero failures and 23 NOT RUN in 95.11 s;
165 pytest tests pass. The measurement includes source isolation, seven codeless plugin builds,
committed publication probes, source-card freshness and local regressions.
The full execution path is otherwise unchanged and was not rerun. See
[acceptance](acceptance.md) for the measured scopes and preserved stage limits.
No dependency installation or native rebuild was made.

## Nix

One attempt used an external registry and this command:

```sh
nix flake check --no-write-lock-file --offline
```

It exited 1 in 0.68 seconds while resolving the direct public board v0.1.5
input, with HTTP 404. The external registry did not redirect that direct
input, a limitation documented by the toolchain. Evaluation and builds are
not proven. No retry or lockfile was made. An inherited tracked lockfile was
removed from version control; its local copy remains ignored. The [receipt](nix-evidence-0.9.0.json)
records the scope; README describes the external registry and explicit
input-override workflow for a configured environment.

[Previous packaging](packaging-0.8.1.md) retains the earlier release's evidence.
