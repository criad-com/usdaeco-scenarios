# Family walkthrough and roundtrip examples

The release walkthrough uses the owning repositories' committed findings and
one render each, in order: CCTV → clash → plan → compliance → repeat.
After [source acquisition](../README.md#build-and-check), run:

```sh
env -u PYTHONPATH "$PYTHON" run_scenarios.py demo --output out/demo
```

Open `out/demo/README.md` for local images and complete findings. The same
narrative is [exported in the root README](../README.md#the-example) with
versioned links into the repositories. No USD plugins are needed to read it.
The family gate separately verifies the freshly executed examples.

The additional synthetic examples below exercise integration behavior.

Run the [family gate](../README.md) first. It records the isolated source and
plugin paths in its transient runtime file. Set `PLUGINSET` to that run's
`pluginset` directory and choose a new output for each operation.

```sh
env -u PYTHONPATH "$PYTHON" demo/roundtrip.py --pluginset "$PLUGINSET" --output .work/roundtrip-demo
env -u PYTHONPATH "$PYTHON" demo/datacentre.py --pluginset "$PLUGINSET" --output .work/published-demo
```

The small roundtrip creates a synthetic wall/pipe IFC, converts through the
IFC integration, imports production wall/pipe drivers, then applies three
edits independently through IFC and native Bonsai. Both clear intent; the
comparison checks resolved drivers, geometry and diagnostics. Revit live
execution is outside the offline gate.

[size_catalog.json](size_catalog.json) supplies synthetic DN65/DN80 rows for
that fixture before any edits. Occurrence identities remain separate from
catalog class prims. The six CCTV lobby cases use the released case definitions
and expected results. In their disposable fixture copies, Mesh provenance
marks change from `exact` to `tessellated` for the core 0.9 rule; geometry and
drivers are unchanged. The shared renderer creates two transient lobby views.

The facility command composes the published `dist/base/dc.usda` and calls the
CCTV example's hook. It verifies counts, hashes, identities, phases, core
validation, expected findings, determinism, idempotence, three rendered views,
vanilla composition and unchanged source files. It never invokes a generator
or converter. CCTV's two released studies are CriticalDoors and Privacy.
The third view is the lobby sensor in the same example, authored only in the
transient presentation layer. All 33 extent guides are hidden.

Historical studies and live rows that the pinned example cannot supply remain
`NOT RUN` in [acceptance](../docs/acceptance.md). They are never counted as
successful coverage evidence.
