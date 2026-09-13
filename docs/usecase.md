# Family acceptance gate

## 1 The problem

Passing each repository separately does not prove that its released schemas,
imports, integrations and published examples compose together.

## 2 The data as it arrives

Exact release tags are recorded in dependencies.json; resolved commits belong to gate evidence. The
family inventory includes all released repositories, the meta documentation
seed and five newly released use-case repositories. Published stages carry their
own manifests and layer hashes.

## 3 The model in USD

The gate authors no schema. It composes the published base stage with the
CCTV example's inputs, driver layers, derived geometry and study results.
Core registers derived metadata first; axis supplies path drivers. Every
Aeco typed prim used in an example has a stock fallback for vanilla USD.

## 4 Workflow

Audit tags, clone exact sources into disposable output, build seven codeless
libraries, validate the inventory and released requirements, then execute
one check.py row per pinned dependency in four independent processes. Run integration cases via their
entry points. Compose the CCTV example twice and compare findings and
normalized stages. Repeat studies to measure cache reuse. Render three views
from that example, measure all five published variant counts against their
manifests, and consume the fresh plan, compliance, repeat, clash and solid
findings. Export the five-step walkthrough from released outputs and renders,
then run regression, link and sanitization checks.

Both profiles audit the usdAECO suite in a shallow clone without submodules:
compare gitlinks with origin release tags, validate explicit released overrides,
verify the stage file inventory and record package/analysis provenance and proofs.
This row does not execute the suite's stage checks or rebuild the facility.

## 5 Validation

The family Report provides structure checks and the final count. NOT RUN
rows retain a reason and do not count as failures or passes. Declared
coverage gaps remain findings. Missing pending repositories, invalid sources, incompatible released
requirements, broken links and executed check failures remain failures.
Inventory validation allows null-tag seeds; an additional strict validation
of released entries prevents inventory mode from hiding incompatibility.
Each exact dependency pin must lie in the inclusive `floor`–`released` train
interval. Range checks test both the declared pin and released version.
Declared fixtures are inventoried separately and cannot waive direct drift. Each
use-case and integration must retain the nine sections and complete result tree.

## 6 The example on the demo data centre

The stage is dist/base/dc.usda from the pinned data repository. Compare all
layer hashes, counts, identities, phases and fallback types before importing
camera properties through CCTV's example. Compare CriticalDoors and Privacy
against the example's committed expected findings. Renders are transient
views of the same composed example; source files remain unchanged. The
walkthrough proceeds through CCTV, clash, plan, compliance and repeat.
Each step records its owning repository tag and actual data variant pin.
The current floor variant includes a 3.2 m partition extension; the released
repeat example reproduces data v0.4.8 and reports the same 3.2 m delta.

## 7 Trade-offs and alternatives

A released repository runs its own acceptance suite in an isolated checkout;
those suites may regenerate their own fixtures. Exact direct inputs and executable historical fixtures (declared flake inputs or byte-qualified generation sources) are read from each
released manifest and recorded per suite, separately from current-train acceptance. The gate's data-centre
scenario always consumes published stages. This separates publication
verification from the consumer's composition test. Missing historical studies
remain visible with their reason instead of being silently removed.
Core and axis retain their declared data-centre source for dependency discovery,
but their minimal examples receive no data-centre ROOT/STAGE override.
Build-up keeps its explicitly declared facility as its example input.

## 8 Out of scope and open questions

Plan is pinned at v0.1.4, compliance at v0.1.3, repeat at v0.2.1, clash at v0.2.3,
and solid at v0.1.5. Historical fixture pins remain distinct from train pins;
their successful suites cannot establish zero drift across released manifests.
Live Revit and native executable CCTV require their separate runtimes.
The native Solid kits run in their own immutable ABI-compatible runtimes.
No schema comparison is applicable because this repository defines none.
Nix execution is not proven by Python acceptance.

## 9 Status

Version 0.9.0 candidate. See [acceptance](acceptance.md) for measured counts and
[release inventory](release-inventory.json) for exact source provenance.
