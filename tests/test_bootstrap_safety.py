from __future__ import annotations

import json
import os
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))

import bootstrap_project as bootstrap  # noqa: E402
import common  # noqa: E402
import guard_private_files as guard  # noqa: E402
import run_baseline_audit as audit  # noqa: E402


def write_zip(path: Path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)


def synthetic_expected(vega: bytes = b'vega', factory: bytes = b'factory') -> dict:
    vega_path = None
    factory_path = None
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        vega_path = root / 'vega'
        factory_path = root / 'factory'
        vega_path.write_bytes(vega)
        factory_path.write_bytes(factory)
        vega_hashes = common.hashes(vega_path)
        factory_hashes = common.hashes(factory_path)
    return {
        'vega_output_size': vega_hashes['size'],
        'vega_output_crc32': vega_hashes['crc32'],
        'vega_output_sha256': vega_hashes['sha256'],
        'factory_output_size': factory_hashes['size'],
        'factory_output_crc32': factory_hashes['crc32'],
        'factory_output_sha256': factory_hashes['sha256'],
    }


def ups_vli(value: int) -> bytes:
    result = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value == 0:
            result.append(byte | 0x80)
            return bytes(result)
        result.append(byte)
        value -= 1


def one_byte_ups(source: bytes, offset: int, target_byte: int) -> bytes:
    target = bytearray(source)
    target[offset] = target_byte
    body = bytearray(b'UPS1')
    body += ups_vli(len(source)) + ups_vli(len(target))
    body += ups_vli(offset)
    body.append(source[offset] ^ target_byte)
    body.append(0)
    body += struct.pack('<II', zlib.crc32(source) & 0xFFFFFFFF, zlib.crc32(target) & 0xFFFFFFFF)
    body += struct.pack('<I', zlib.crc32(body) & 0xFFFFFFFF)
    return bytes(body)


def one_byte_ips(offset: int, target_byte: int) -> bytes:
    return (
        b'PATCH'
        + offset.to_bytes(3, 'big')
        + (1).to_bytes(2, 'big')
        + bytes([target_byte])
        + b'EOF'
    )


class HashContractTests(unittest.TestCase):
    def test_example_config_pins_every_required_input_and_output(self) -> None:
        cfg = common.load_toml(ROOT / 'config/project.example.toml')
        for name in common.INPUT_EXPECTATION_KEYS:
            self.assertTrue(common.input_expectations(cfg['expected'], name))
        for name in common.OUTPUT_EXPECTATION_KEYS:
            self.assertTrue(common.output_expectations(cfg['expected'], name))

    def test_verified_hashes_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'input.bin'
            path.write_bytes(b'known')
            common.verified_hashes(path, {'sha256': common.hashes(path)['sha256']}, 'input')
            with self.assertRaises(common.HashMismatchError):
                common.verified_hashes(path, {'sha256': '0' * 64}, 'input')


class PortablePathTests(unittest.TestCase):
    def test_project_path_rejects_absolute_and_parent_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(ValueError):
                common.project_path(root, '/tmp/private.gba')
            with self.assertRaises(ValueError):
                common.project_path(root, '../private.gba')

    def test_resolved_paths_are_relative_and_config_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'state').mkdir()
            cfg = {'inputs': {'clean_rom': 'inputs/private/clean.gba'}}
            common.write_json(
                root / 'state/resolved_paths.json',
                {
                    'schema_version': 2,
                    'config_fingerprint': common.stable_digest(cfg['inputs']),
                    'inputs': {'clean_rom': 'inputs/selected.gba'},
                },
            )
            self.assertEqual(
                common.resolved_input_paths(root, cfg)['clean_rom'],
                root / 'inputs/selected.gba',
            )

            state = json.loads((root / 'state/resolved_paths.json').read_text())
            state['inputs']['clean_rom'] = '/home/someone/private.gba'
            common.write_json(root / 'state/resolved_paths.json', state)
            self.assertEqual(
                common.resolved_input_paths(root, cfg)['clean_rom'],
                root / 'inputs/private/clean.gba',
            )

            state['config_fingerprint'] = 'stale'
            state['inputs']['clean_rom'] = 'inputs/selected.gba'
            common.write_json(root / 'state/resolved_paths.json', state)
            self.assertEqual(
                common.resolved_input_paths(root, cfg)['clean_rom'],
                root / 'inputs/private/clean.gba',
            )


class SafeArchiveTests(unittest.TestCase):
    def test_safe_archive_flattens_one_wrapper_and_promotes_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / 'source.zip'
            destination = root / 'source'
            write_zip(archive, {'wrapper/readme.txt': b'ok'})
            bootstrap.extract_archive(archive, destination)
            self.assertEqual((destination / 'readme.txt').read_bytes(), b'ok')
            self.assertFalse(any(root.glob('.source.staging-*')))

    def test_archive_rejects_path_traversal_absolute_drive_and_backslash(self) -> None:
        unsafe_names = ('../escape', '/absolute', 'C:/drive', r'folder\escape')
        for unsafe_name in unsafe_names:
            with self.subTest(unsafe_name=unsafe_name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                archive = root / 'unsafe.zip'
                write_zip(archive, {unsafe_name: b'bad'})
                destination = root / 'output'
                with self.assertRaises(bootstrap.UnsafeArchiveError):
                    bootstrap.extract_archive(archive, destination)
                self.assertFalse(destination.exists())

    def test_archive_rejects_symlink_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive_path = root / 'symlink.zip'
            info = zipfile.ZipInfo('link')
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(archive_path, 'w') as archive:
                archive.writestr(info, '../target')
            with self.assertRaises(bootstrap.UnsafeArchiveError):
                bootstrap.extract_archive(archive_path, root / 'output')

    def test_archive_enforces_entry_and_total_expansion_limits(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / 'large.zip'
            write_zip(archive, {'one': b'12345'})
            with self.assertRaises(bootstrap.UnsafeArchiveError):
                bootstrap.extract_archive(archive, root / 'entry', max_entry_size=4)

            write_zip(archive, {'one': b'123', 'two': b'456'})
            with self.assertRaises(bootstrap.UnsafeArchiveError):
                bootstrap.extract_archive(archive, root / 'total', max_total_size=5)

    def test_archive_cache_detects_replaced_zip_and_preserves_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / 'source.zip'
            destination = root / 'source'
            write_zip(archive, {'wrapper/value.txt': b'first'})
            bootstrap.ensure_archive_extracted(archive, destination)
            write_zip(archive, {'wrapper/value.txt': b'second'})
            with self.assertRaises(RuntimeError):
                bootstrap.ensure_archive_extracted(archive, destination)
            self.assertEqual((destination / 'value.txt').read_bytes(), b'first')


class SourceProvenanceTests(unittest.TestCase):
    def test_archive_source_never_claims_configured_commit_was_verified(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'archives').mkdir()
            archive = root / 'archives/source.zip'
            write_zip(archive, {'project/file.txt': b'source'})
            cfg = {
                'dest': 'vendor/source',
                'archive': 'archives/source.zip',
                'repo': 'https://example.invalid/source.git',
                'commit': 'a' * 40,
            }
            record = bootstrap.acquire_source(root, 'source', cfg)
            self.assertEqual(record['provenance'], 'archive')
            self.assertIsNone(record['actual_commit'])
            self.assertIsNone(record['resolved_commit'])
            self.assertFalse(record['configured_commit_verified'])
            self.assertEqual(record['path'], 'vendor/source')
            self.assertEqual(record['archive']['path'], 'archives/source.zip')
            self.assertNotIn(str(root), json.dumps(record))

    def test_archive_under_parent_git_repo_remains_archive_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
            (root / 'archives').mkdir()
            archive = root / 'archives/source.zip'
            write_zip(archive, {'project/file.txt': b'source'})
            cfg = {
                'dest': 'vendor/source',
                'archive': 'archives/source.zip',
                'repo': 'https://example.invalid/source.git',
                'commit': 'a' * 40,
            }

            record = bootstrap.acquire_source(root, 'source', cfg)

            self.assertFalse(bootstrap._is_git_repository(root / 'vendor/source'))
            self.assertEqual(record['provenance'], 'archive')
            self.assertFalse(record['configured_commit_verified'])

    def test_git_source_checks_out_the_exact_full_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / 'repo'
            repo.mkdir()
            subprocess.run(['git', 'init', '-q'], cwd=repo, check=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.invalid'], cwd=repo, check=True)
            subprocess.run(['git', 'config', 'user.name', 'Synthetic Test'], cwd=repo, check=True)
            (repo / 'value').write_text('one')
            subprocess.run(['git', 'add', 'value'], cwd=repo, check=True)
            subprocess.run(['git', 'commit', '-qm', 'one'], cwd=repo, check=True)
            first = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
            (repo / 'value').write_text('two')
            subprocess.run(['git', 'commit', '-qam', 'two'], cwd=repo, check=True)

            actual = bootstrap._checkout_pinned_commit(repo, first)
            self.assertEqual(actual, first)
            self.assertEqual(
                subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
                first,
            )
            with self.assertRaises(ValueError):
                bootstrap._checkout_pinned_commit(repo, first[:12])

    def test_git_source_rejects_tracked_changes_after_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / 'repo'
            repo.mkdir()
            subprocess.run(['git', 'init', '-q'], cwd=repo, check=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.invalid'], cwd=repo, check=True)
            subprocess.run(['git', 'config', 'user.name', 'Synthetic Test'], cwd=repo, check=True)
            (repo / 'value').write_text('committed')
            subprocess.run(['git', 'add', 'value'], cwd=repo, check=True)
            subprocess.run(['git', 'commit', '-qm', 'source'], cwd=repo, check=True)
            commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
            (repo / 'value').write_text('dirty')
            cfg = {
                'dest': 'repo',
                'repo': 'https://example.invalid/source.git',
                'commit': commit,
            }

            with self.assertRaisesRegex(RuntimeError, 'tracked changes'):
                bootstrap.acquire_source(Path(temporary), 'source', cfg)

    def test_git_source_rejects_untracked_files_after_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / 'repo'
            repo.mkdir()
            subprocess.run(['git', 'init', '-q'], cwd=repo, check=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.invalid'], cwd=repo, check=True)
            subprocess.run(['git', 'config', 'user.name', 'Synthetic Test'], cwd=repo, check=True)
            (repo / 'value').write_text('committed')
            subprocess.run(['git', 'add', 'value'], cwd=repo, check=True)
            subprocess.run(['git', 'commit', '-qm', 'source'], cwd=repo, check=True)
            commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
            (repo / 'untracked').write_text('local')
            cfg = {
                'dest': 'repo',
                'repo': 'https://example.invalid/source.git',
                'commit': commit,
            }

            with self.assertRaisesRegex(RuntimeError, 'untracked files'):
                bootstrap.acquire_source(Path(temporary), 'source', cfg)


class ArtifactCacheTests(unittest.TestCase):
    def test_directory_cache_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / 'exact_conflicts.csv').write_text('csv')
            (directory / 'exact_conflicts.json').write_text('{}')
            (directory / 'exact_conflicts.md').write_text('md')
            descriptor = {'input': 'hash'}
            cache_key = common.stable_digest(descriptor)
            audit.write_cache(directory, cache_key, descriptor)
            self.assertTrue(audit.cache_matches(directory, cache_key, audit.AUDIT_ARTIFACTS))
            (directory / 'exact_conflicts.md').write_text('changed')
            self.assertFalse(audit.cache_matches(directory, cache_key, audit.AUDIT_ARTIFACTS))

    def test_promotion_refuses_unexpected_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            staging = root / 'stage'
            destination = root / 'destination'
            staging.mkdir()
            destination.mkdir()
            (staging / 'new').write_text('new')
            (destination / 'old').write_text('old')
            with self.assertRaises(FileExistsError):
                audit.promote_directory(staging, destination, replace_existing=False)
            self.assertEqual((destination / 'old').read_text(), 'old')
            self.assertEqual((staging / 'new').read_text(), 'new')

    def test_reference_normalization_uses_required_names_and_hashes(self) -> None:
        expected = synthetic_expected()
        with tempfile.TemporaryDirectory() as temporary:
            staging = Path(temporary)
            (staging / 'vega_reference.gba').write_bytes(b'vega')
            (staging / 'factory_reference.gba').write_bytes(b'factory')
            audit._normalize_generated_references(staging, expected)
            self.assertEqual((staging / 'vega.gba').read_bytes(), b'vega')
            self.assertEqual((staging / 'factory.gba').read_bytes(), b'factory')
            self.assertFalse((staging / 'vega_reference.gba').exists())


class CompactAuditTests(unittest.TestCase):
    def test_compact_audit_classifies_overlap_and_writes_references(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            clean = root / 'clean.gba'
            ips = root / 'vega.ips'
            ups = root / 'factory.ups'
            out = root / 'out'
            clean.write_bytes(b'abcd')
            ips.write_bytes(one_byte_ips(2, ord('Z')))
            ups.write_bytes(one_byte_ups(b'abcd', 2, ord('X')))
            audit.run_compact_exact_audit(
                clean, ips, ups, out, write_reference_roms=True
            )
            summary = json.loads((out / 'exact_conflicts.json').read_text())
            self.assertEqual(summary['comparison']['double_touched_bytes'], 1)
            self.assertEqual(summary['comparison']['different_target_bytes'], 1)
            self.assertEqual(
                (out / 'reference_roms/vega_reference.gba').read_bytes(), b'abZd'
            )
            self.assertEqual(
                (out / 'reference_roms/factory_reference.gba').read_bytes(), b'abXd'
            )

    def test_compact_audit_handles_zero_overlap_with_header_only_csv(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            clean = root / 'clean.gba'
            ips = root / 'vega.ips'
            ups = root / 'factory.ups'
            out = root / 'out'
            clean.write_bytes(b'abcd')
            ips.write_bytes(one_byte_ips(0, ord('Z')))
            ups.write_bytes(one_byte_ups(b'abcd', 2, ord('X')))
            audit.run_compact_exact_audit(
                clean, ips, ups, out, write_reference_roms=False
            )
            summary = json.loads((out / 'exact_conflicts.json').read_text())
            self.assertEqual(summary['comparison']['double_touched_bytes'], 0)
            csv_lines = (out / 'exact_conflicts.csv').read_text(encoding='utf-8-sig').splitlines()
            self.assertEqual(len(csv_lines), 1)


class PrivateGuardTests(unittest.TestCase):
    def test_zip_guard_allows_source_zip_but_finds_rom_or_patch_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            safe = root / 'safe.zip'
            private = root / 'private.zip'
            write_zip(safe, {'audit_seed/tools/analyze.py': b'pass'})
            write_zip(private, {'payload/game.gba': b'rom', 'payload/update.ips': b'patch'})
            self.assertEqual(guard.blocked_zip_members(safe), [])
            self.assertEqual(
                guard.blocked_zip_members(private),
                ['payload/game.gba', 'payload/update.ips'],
            )

    def test_user_path_detection_ignores_urls_and_safe_zip_notation(self) -> None:
        windows = 'C:' + r'\Users\alice\Downloads\private.gba'
        text = '\n'.join(
            [
                'audit_seed/source_bundle.zip is a safe logical notation',
                'https://example.invalid/home/alice/reference',
                windows,
                '/mnt/c/Users/alice/Downloads/private.gba',
                '/home/alice/project/private.gba',
            ]
        )
        self.assertEqual(common.user_absolute_path_lines(text), [3, 4, 5])


if __name__ == '__main__':
    unittest.main()
