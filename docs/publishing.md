# Publishing the family gate

Generate the family index from this repository's explicit train and tagged
source checkouts. The shared Toolchain v0.3.10 generator writes
`docs/family/README.md` and `docs/family/index.json`; the gate checks these
against the live tagged sources. The generic-kit adapter preserves names,
tags and ranges in the generated output.

```sh
env -u PYTHONPATH "$PYTHON" tools/usdaeco_scenarios/index.py --family family.json --repos out/family
```

The [README](../README.md) explains source acquisition and gate execution.
The [packaging record](packaging.md) states which release claims are proven.
Publish a release only after reviewing the acceptance report and its deviations.
