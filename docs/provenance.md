# Neutral asset provenance

This repository distributes authored gate code, synthetic fixtures and numeric
acceptance evidence under [MIT](../LICENSE). It includes no vendor family
or native client project. [The asset inventory](provenance-assets.json) records
hashes for retained assets. Third-party tools retain their own licences.

The family supplies the published `demo-datacentre-01` stages. CCTV owns its
example inputs, expected findings and committed images. The gate composes
those files read-only and writes derived and presentation layers into transient
output. It distributes no duplicate facility images.

`baselines/wallpipe.py` and `baselines/wall_corner.py` produce synthetic geometry.
`demo/size_catalog.json` contains illustrative pipe sizes. The retained
`spikes/revit/wallpipe-export.ifc` is the neutral wall/pipe experiment, not a
vendor family. `testenv/fixtures/column-view-exception.json` preserves historical
numeric proof solely for regression testing of strict exception matching.

The older evidence JSON files retain their embedded release scope and are not
claims of current native execution. Current results and deviations are linked
from [acceptance](acceptance.md). Portable reports contain repository-relative
paths. Local logs and generated render files remain in ignored output.
