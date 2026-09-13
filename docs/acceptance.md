# Family 0.9.0 acceptance

Train `aeco-0.9.0` adds the usdAECO suite at **v0.3.0**, the newest released
tag resolved on the origin. The [fast report](acceptance-fast-0.9.0.json)
records **54 checks, 0 failed, 23 not run; 31 PASS; 95.11 s**,
including **165 pytest tests passed in 25.08 s**. The full profile's existing execution is unchanged
and has not been rerun for this candidate.

## Acceptance

| Requirement | Measured result | Status |
|---|---|---|
| Fast profile | 54 checks, 0 failed, 23 NOT RUN; 31 PASS; 95.11 s / 360 s | PASS |
| Pytest | 165 passed in 25.08 s | PASS |
| Family inventory | 25 entries; 24 released pins, including the scenarios baseline; 1 unpinned metadata entry | PASS |
| Released compatibility | 24 entries, 0 incompatible requirements | PASS |
| Suite | v0.3.0; 23/23 gitlinks equal origin release tags; 2 explicit released overrides | PASS |
| Stage provenance | 284/284 references resolve to released package, analysis or suite tags | PASS |
| Stage evidence | 250 file sizes and hashes; 12 proof groups; manifest and integration document hashes recorded | PASS |
| Suite checkout | Shallow; 0 initialized submodules; no recursive suite execution | PASS |
| Train drift | 125/125 direct pins, 35/35 requirement ranges, 22/22 publication contracts | PASS |
| Family index | 25 fresh source cards; candidate version distinct from released pin | PASS |
| Focused suite regressions | 26 passed in 10.15 s | PASS |
| Structure | 29 checks, 0 failed | PASS |
| Documentation links | 45/45 roots | PASS |
| Final sanitization | 138 files, 0 violations; retired-term sweep clean | PASS |
| Whitespace check | git diff --check clean | PASS |
| Full profile reproduction | Not rerun for 0.9.0 | NOT RUN |
| Nix | One input-resolution failure, exit 1 in 0.68 s | NOT PROVEN |

## What the suite row proves

The gate compares the complete repository sets in `family.json`, the released
suite's `suite.json`, `.gitmodules` and the HEAD gitlink tree. Each suite pin
must equal its train release or carry an explicit override with status
`released`. Origin tags are peeled before comparing commits, including
annotated tags. No submodule checkout is needed. The suite's own checkout,
metadata version and origin release tag must agree and its worktree must be clean.

| Released override | Train | Suite |
|---|---|---|
| usdaeco-datacentre | v0.4.9 | v0.5.1 |
| usdaeco-ifc | v0.2.3 | v0.3.1 |

Suite v0.3.0 does not provide `pins.py --check --from-gitlinks`; its CLI help
confirms that. The fallback verifies all 23 gitlinks using `git ls-tree` and
origin tags. A future release supporting the option also runs that command.
The root suite `check.py` requires submodules and is not executed here.

Both stage documents must contain measured evidence. The gate hashes them,
checks the 250 files against the manifest, requires tagged packages and
analyses, and resolves all 284 tag references on the appropriate origins.
Historical producer stamps remain valid release provenance: generator v0.5.0
stamps coexist with the v0.5.1 delivery pin. Suite-authored roots and the
Bonsai-produced cooling twins carry the suite's v0.3.0 tag. Repository
ownership is resolved from source paths and explicit producer/package stamps;
a tag merely existing in a different repository cannot satisfy the check.

## Recorded stage limits

These are measurements published by the suite, not freshly executed proofs:

- Nine packages and nine analyses; eight hooks ran, while solid retains a
  committed result with `run: false`. Hook adaptations and differing findings
  remain in the acceptance evidence.
- Twelve proof groups record plugin-free composition/rendering, connected
  parity, flattening, inventories, layout, muting, size, rebuilding, strict
  checking, validators and the Bonsai delivery. The integration document
  records 83 recomputed quantities.
- Connected/twin parity records 15,576 prims per form and two mesh exclusions.
  The flattened crate is 3,166,293 bytes. The row checks its committed hash;
  it does not repeat flattening or open the stage.
- Validator evidence records 55 raw errors, zero unexpected errors and
  `zeroErrors: false`. Muting records 117 rows and
  `portOnlyRequirementMet: false`. Those limitations are preserved; the
  provenance PASS does not claim zero validator errors or the stricter mute rule.

## Deviations

- Scenarios remains released at v0.8.1 while `library.json`, package metadata
  and the source card identify candidate v0.9.0. Bumping the released field
  before publication would both claim an unavailable release and invalidate
  the immutable suite's scenarios pin without an override. All prior train
  pins and floors are retained; the suite requires the baseline train.
- The first fast run finished in 98.40 s with 54 checks, 1 failed and 23 NOT RUN:
  an existing regression expected 24 inventory entries. The expectation now
  includes the suite; the corrected run passes all executed rows. [Verification](verification-0.9.0.json) retains that result.
- Advertised tags were unavailable in some supplied sibling checkouts.
  Validation used fresh disposable acquisitions from the origin. The suite
  source is shallow and nonrecursive; public-only acquisition is not proven.
- Full-profile runtime suites and fresh stage execution were not rerun.
  This source-provenance addition keeps the existing full execution path;
  fast-profile omissions remain explicit NOT RUN rows.
- The inherited tracked lockfile is removed from version control; the local
  copy remains ignored. No lockfile is added or updated by this release.
- The one Nix attempt failed during direct board input resolution. The external
  registry did not redirect that input. No retry, installation or lockfile was
  made; [packaging](packaging.md) and its receipt record the limitation.

[Previous acceptance](acceptance-0.8.1.md) and its linked reports retain the
prior full and fast evidence. They do not establish full acceptance for 0.9.0.
