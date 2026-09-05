import copy
import hashlib
import io
import tarfile
import unittest
from scripts import portable_python_identity as identity


class PortablePythonIdentityTests(unittest.TestCase):
    def probe(self):
        return {'version': '3.12.3', 'implementation': 'cpython', 'machine': 'x86_64',
                'pointer_bits': 64, 'byteorder': 'little', 'soabi': 'cpython-312-x86_64-linux-gnu',
                'packed': '78563412', 'sha256_abc': hashlib.sha256(b'abc').hexdigest(),
                'zlib_roundtrip': True, 'canonical_json': '{"a":1,"b":2}'}

    def archive(self, payload=b'python', *, symlink=False, duplicate=False):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w') as archive:
            member = tarfile.TarInfo('./usr/bin/python3.12')
            member.size = len(payload)
            if symlink:
                member.type = tarfile.SYMTYPE
                member.linkname = 'elsewhere'
                member.size = 0
            archive.addfile(member, io.BytesIO(payload))
            if duplicate:
                archive.addfile(member, io.BytesIO(payload))
        return stream.getvalue()

    def test_exact_version_abi_and_features(self):
        identity.verify_probe(self.probe(), '3.12.3')

    def test_wrong_version_abi_and_features_are_all_rejected(self):
        for key in self.probe():
            with self.subTest(field=key):
                info = copy.deepcopy(self.probe())
                info[key] = 'incorrect'
                with self.assertRaises(identity.PythonIdentityError):
                    identity.verify_probe(info, '3.12.3')

    def test_exact_package_record(self):
        record = 'Package: python3.12-minimal\nVersion: 3.12.3-1ubuntu0.16\nArchitecture: amd64\nSHA256: ' + 'a' * 64
        self.assertEqual(identity.package_record(record, '3.12.3-1ubuntu0.16')['SHA256'], 'a' * 64)

    def test_wrong_package_record_and_missing_sha_are_rejected(self):
        valid = 'Package: python3.12-minimal\nVersion: 3.12.3-1ubuntu0.16\nArchitecture: amd64\nSHA256: ' + 'a' * 64
        for old, new in [('python3.12-minimal', 'another'), ('amd64', 'arm64'), ('3.12.3-1ubuntu0.16', '3.12.3-1ubuntu0.15'), ('SHA256', 'MD5sum')]:
            with self.subTest(field=old):
                with self.assertRaises(identity.PythonIdentityError):
                    identity.package_record(valid.replace(old, new), '3.12.3-1ubuntu0.16')

    def test_conflicting_package_hashes_are_rejected(self):
        row = 'Package: python3.12-minimal\nVersion: 3.12.3-1ubuntu0.16\nArchitecture: amd64\nSHA256: '
        with self.assertRaises(identity.PythonIdentityError):
            identity.package_record(row + 'a' * 64 + '\n\n' + row + 'b' * 64, '3.12.3-1ubuntu0.16')

    def test_package_and_member_sha256(self):
        identity.verify_deb_member(b'deb', hashlib.sha256(b'deb').hexdigest(), self.archive(), hashlib.sha256(b'python').hexdigest())

    def test_wrong_outer_sha256_is_rejected(self):
        with self.assertRaisesRegex(identity.PythonIdentityError, 'package SHA'):
            identity.verify_deb_member(b'deb', '0' * 64, self.archive(), hashlib.sha256(b'python').hexdigest())

    def test_wrong_member_sha256_is_rejected(self):
        with self.assertRaisesRegex(identity.PythonIdentityError, 'package member'):
            identity.verify_deb_member(b'deb', hashlib.sha256(b'deb').hexdigest(), self.archive(), '0' * 64)

    def test_symlink_member_is_rejected(self):
        with self.assertRaisesRegex(identity.PythonIdentityError, 'regular file'):
            identity.verify_deb_member(b'deb', hashlib.sha256(b'deb').hexdigest(), self.archive(symlink=True), '0' * 64)

    def test_duplicate_member_is_rejected(self):
        with self.assertRaisesRegex(identity.PythonIdentityError, 'regular file'):
            identity.verify_deb_member(b'deb', hashlib.sha256(b'deb').hexdigest(), self.archive(duplicate=True), '0' * 64)
