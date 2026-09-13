"""Validate train intervals with the shared semantic-family validator."""
import copy
import json
from pathlib import Path

KITS = {"usdSolid": "usdaeco-solid-kit", "usdSolidOcct": "usdaeco-solid-occt-kit",
        "aeco-toolchain": "usdaeco-build-kit"}


def validate_family(document, **kwargs):
    """Project generic kit names and the suite kind; preserve pins and ranges.

    The shared validator restricts repository names to usdaeco-* and has no
    kit or suite kind. The public inventory retains the actual names and kinds.
    """
    from usdaeco_check.family import validate_family as shared_validate
    from usdaeco_check.report import Result
    from packaging.version import Version
    data = json.loads(Path(document).read_text()) if isinstance(document, (str, Path)) else copy.deepcopy(document)
    for entry in data.get("repos", []):
        try:
            floor, released = entry['floor'], entry['released']
            # The shared index still reads tag; it is a checked compatibility
            # alias, never a second independently selectable release.
            if entry['tag'] != released or (floor is None) != (released is None):
                raise ValueError('released/tag disagreement or incomplete interval')
            if released is not None and Version(floor) > Version(released):
                raise ValueError('floor exceeds released')
        except (KeyError, ValueError, TypeError) as exc:
            return Result('family train interval', False, entry.get('name', 'Unknown') + ': ' + str(exc))
        if entry.get("name") in KITS and entry.get("kind") == "kit":
            entry["name"] = KITS[entry["name"]]
            entry["kind"] = "library"
        if entry.get('kind') == 'suite':
            if entry.get('name') != 'usdaeco' or entry.get('library') is not None:
                return Result('family suite', False, 'suite must be usdaeco with no schema library')
            entry['kind'] = 'gate'
        entry['requires'] = {KITS.get(name, name): bounds for name, bounds in entry['requires'].items()}
    return shared_validate(data, **kwargs)
