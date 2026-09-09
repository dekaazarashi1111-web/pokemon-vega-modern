#!/usr/bin/env python3
"""Materialize eight hash-reviewed P08 sources and the credential-redirect regression."""
import base64
import hashlib
import json
from pathlib import Path
import zlib

root = Path('.')
sha = lambda raw: hashlib.sha256(raw).hexdigest()
parts = [root / f'tools/stage81_p08_bootstrap/part{i}.b64' for i in (1, 2, 3)]
packed = ''.join(p.read_text().strip() for p in parts)
if sha(packed.encode()) == '9e0583e3b9de9cb5d095259eae11474abb265f1cfd13464d7ba16ca0f7ae68b1':
    value = parts[0].read_text().strip()
    assert value[1327:1351] == 'oaPD0U4ObfwO37vxuty38cQD'
    parts[0].write_text(value[:1339] + '0' + value[1339:] + '\n')
    packed = ''.join(p.read_text().strip() for p in parts)
assert sha(packed.encode()) == '1e7b8db7b8cc477c324564e1391839678d31967d0886f94b7e3a694864feeb53'
raw = zlib.decompress(base64.b64decode(packed, validate=True))
assert sha(raw) == '9796a57846733f8134945aba3300edef56fbc01a462791da84cb2ac2f3659dd9'
rows = json.loads(raw)
allowed = {
    'tools/modernization_p08_stage81_evidence.py',
    'scripts/integrate_modernization_p08_stage81_evidence.py',
    'tests/test_modernization_p08_stage81_evidence.py',
    'scripts/build_modernization_p08.py',
    'scripts/check_modernization_p08_current_acceptance.py',
    'tests/test_modernization_p08_current_acceptance.py',
    'docs/P08_CURRENT_ACCEPTANCE.md',
    'docs/P08_STAGE81_NATIVE_PP.md',
}
assert set(rows) == allowed, 'exact eight-source manifest required'
# Two explicit follow-up changes: keep GitHub credentials off signed blob redirects,
# and prove the redirect behavior with a regression. Original ZIP pins are untouched.
old = """        headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
                 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
    with urllib.request.urlopen(request, timeout=60) as response:"""
new = """        headers={'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
    # Authenticate GitHub only; signed artifact redirects must not inherit this credential.
    request.add_unredirected_header('Authorization', 'Bearer ' + os.environ['GH_TOKEN'])
    with urllib.request.urlopen(request, timeout=60) as response:"""
anchor = "\nif __name__ == '__main__': unittest.main()\n"
addition = '''
class DownloadRedirectTests(unittest.TestCase):
    def test_artifact_redirect_never_forwards_github_authorization(self):
        name = next(iter(e.ARCHIVES))
        payload = b'exact-archive-bytes'

        def open_request(request, timeout):
            self.assertEqual(timeout, 60)
            self.assertEqual(request.get_header('Authorization'), 'Bearer unit-test-token')
            redirected = importer.urllib.request.HTTPRedirectHandler().redirect_request(
                request, None, 302, 'Found', {},
                'https://example.blob.core.windows.net/artifacts/source.zip?sig=unit-test')
            self.assertIsNone(redirected.get_header('Authorization'))
            response = mock.MagicMock()
            response.__enter__.return_value.read.return_value = payload
            return response

        with mock.patch.dict(importer.os.environ, {'GH_TOKEN': 'unit-test-token'}), \\
                mock.patch.object(importer.urllib.request, 'urlopen', side_effect=open_request), \\
                mock.patch.object(importer.evidence, 'unpack') as unpack:
            self.assertEqual(importer.download(name), payload)
            unpack.assert_called_once_with(payload, name)

'''
fixes = {
    'scripts/integrate_modernization_p08_stage81_evidence.py':
        (old, new, '52714a2082b3abd1bff551754c79d0188dad7cc6d579e1c8f10821fbcc96374c'),
    'tests/test_modernization_p08_stage81_evidence.py':
        (anchor, '\n' + addition + anchor, 'b135a0a544bbcb2a6dd0d26d3041d33c37551e74621de8baf4deb2b6b7cc0e75'),
}
for relative, (before, after, expected) in fixes.items():
    row = rows[relative]
    assert sha(row['content'].encode()) == row['after_sha256']
    assert row['content'].count(before) == 1
    content = row['content'].replace(before, after)
    assert sha(content.encode()) == expected, 'reviewed redirect correction mismatch'
    row.update(content=content, after_sha256=expected)
for relative, row in rows.items():
    path = root
    for part in Path(relative).parts:
        path /= part
        assert not path.is_symlink(), relative
    current = sha(path.read_bytes()) if path.exists() else None
    assert current in (row['before_sha256'], row['after_sha256']), 'concurrent source change: ' + relative
    assert sha(row['content'].encode()) == row['after_sha256']
for relative, row in rows.items():
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(row['content'].encode())
receipt = {p: {k: v for k, v in row.items() if k != 'content'} for p, row in rows.items()}
Path('.local/p08-stage81-integration/code-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('Exact source manifest and all before/after hashes verified: 8 files')
