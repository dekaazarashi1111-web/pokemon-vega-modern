"""Update the exact plan-footprint assertion after the verified repair is applied."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[2]
relative = 'tests/test_modernization_stage79_cumulative_mgba.py'
path = root / relative
assert hashlib.sha256(path.read_bytes()).hexdigest() == '15140faa213f796bb6d49d8ad65ed5abb52940c7c224e7927a360aff9124b748'
before = 'self.assertEqual(plan["input"]["changed_bytes_from_parent"], 8)'
after = 'self.assertEqual(plan["input"]["changed_bytes_from_parent"], 51)'
source = path.read_text()
assert source.count(before) == 1
path.write_text(source.replace(before, after, 1))
manifest = root / '.local/stage79-field-paths-repair/targets.json'
targets = json.loads(manifest.read_text())
assert relative not in targets
targets.append(relative)
manifest.write_text(json.dumps(sorted(targets), indent=2) + '\n')
print('Exact plan footprint updated from the historical 8-byte recipe to the independently tested 51-byte recipe.')
