"""Scan release source and generated asset metadata without publishing matches."""
from pathlib import Path
import re
import subprocess

PATTERNS = {
    'private-address': r'\b(?:(?:10|100)(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b',
    'local-path': r'/(?:Users|Volumes|home)/[^\s"<>]+|[A-Z]:\\(?:Users|aeco)[^\s"<>]*',
    'mac-address': r'\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b',
    'internal-name': r'\b(?:\x43\x44\x43[-_ ]?1|\x43\x72\x69\x61\x64|\x66\x6f\x72\x75\x6d-\d+|\x4e\x50\x47-\d+|\x66\x65\x6c\x69\x78(?:\x6e\x65\x75\x66\x65\x6c\x64)?)\b',
}


def scan(paths):
    count, violations = 0, []
    for path in sorted(set(map(Path, paths))):
        if not path.is_file():
            continue
        if path.suffix in ('.usdc', '.usd'):
            from pxr import Sdf
            layer = Sdf.Layer.FindOrOpen(str(path))
            text = layer.ExportToString() if layer else ''
        else:
            try:
                text = path.read_text()
            except UnicodeDecodeError:
                continue
        count += 1
        if path.name == 'LICENSE':
            text = re.sub(r'(?m)^Copyright \(c\) 2026 Cr[i]ad$', '', text)
        if path.name == 'README.md' and '## Licence\n' in text:
            head, licence = text.split('## Licence\n', 1)
            text = head + re.sub(r'Copyright \(c\) 2026 Cr[i]ad\.', '', licence)
        for label, pattern in PATTERNS.items():
            inspected = re.sub(r'(?<![\w-])criad-com(?![\w-])', '', text) if label == 'internal-name' else text
            if re.search(pattern, inspected, re.I):
                violations.append(dict(file=path.name, category=label))
    return dict(files=count, violations=violations, passed=not violations)


def source_files(root):
    names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=root, text=True).splitlines()
    return [Path(root)/n for n in names if n != 'STEERING.md']
