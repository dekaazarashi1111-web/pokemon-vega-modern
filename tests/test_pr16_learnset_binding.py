"""新規adapter入力契約だけを試験し、受入済み生成器/nativeを呼ばない。"""
import copy
import io
import tempfile
from pathlib import Path
import stat
import unittest
import zipfile
from tools import pr16_learnset_binding as b


def bundle(entries=None):
    receipt = {'files': {'table.jsonl': b.identity(b'{}\n')}}
    if entries is None:
        entries = [('table.jsonl', b'{}\n'), ('receipt.json', b.encode(receipt))]
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as z:
        for name, raw in entries:
            z.writestr(name, raw)
    raw = stream.getvalue()
    artifact = {'size_in_bytes': len(raw), 'digest': 'sha256:' + b.identity(raw)['sha256']}
    return raw, artifact, receipt


def hatch(present=False):
    return {'consumer': 'pre_evolution_carry', 'direct_grant': False, 'shared_grant': False,
            'receiver_species_id': 3, 'hatch_species_id': 1, 'move_id': 22,
            'hatch_selected_direct_egg_membership': present,
            'cross_source_status': 'MEMBERSHIP_ONLY_NATIVE_PENDING' if present else 'HATCH_BASELINE_DIFFERENCE_REQUIRES_ADAPTER_REVIEW',
            'provenance': {'row_key': 'source:1', 'classification': 'PRE_EVOLUTION_EGG',
                           'species_id': 3, 'hatch_species_id': 1, 'move_id': 22,
                           'adopt_as_receiver_direct_egg': False, 'add_as_shared_egg': False,
                           'original_direct_egg_rows': [{'move_id': 22}]}}


class ArchiveTests(unittest.TestCase):
    def test_valid_restore(self):
        raw, artifact, receipt = bundle()
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp)/'.local/tables'
            b.restore_archive(temp, dest, raw, artifact, receipt)
            self.assertEqual((dest/'table.jsonl').read_bytes(), b'{}\n')

    def test_outer_digest(self):
        raw, artifact, receipt = bundle()
        artifact['digest'] = 'sha256:' + '0'*64
        with self.assertRaises(ValueError): b.validate_archive(raw, artifact, receipt)

    def test_member_hash(self):
        raw, artifact, receipt = bundle()
        receipt['files']['table.jsonl']['sha256'] = '0'*64
        with self.assertRaises(ValueError): b.validate_archive(raw, artifact, receipt)

    def test_missing_member(self):
        raw, artifact, receipt = bundle([('table.jsonl', b'{}\n')])
        with self.assertRaises(ValueError): b.validate_archive(raw, artifact, receipt)

    def test_extra_member(self):
        raw, artifact, receipt = bundle([('table.jsonl', b'{}\n'), ('extra', b'x')])
        with self.assertRaises(ValueError): b.validate_archive(raw, artifact, receipt)

    def test_duplicate_member(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            raw, artifact, receipt = bundle([('table.jsonl', b'{}\n'), ('table.jsonl', b'{}\n')])
        with self.assertRaises(ValueError): b.validate_archive(raw, artifact, receipt)

    def test_symlink_member(self):
        info = zipfile.ZipInfo('table.jsonl')
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        receipt = bundle()[2]
        raw, artifact, receipt = bundle([(info, b'{}\n'), ('receipt.json', b.encode(receipt))])
        with self.assertRaises(ValueError): b.validate_archive(raw, artifact, receipt)

    def test_traversal_contract(self):
        raw, artifact, receipt = bundle()
        receipt['files']['../outside'] = receipt['files'].pop('table.jsonl')
        with self.assertRaises(ValueError): b.validate_archive(raw, artifact, receipt)

    def test_bad_archive_leaves_destination_absent(self):
        raw, artifact, receipt = bundle()
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp)/'.local/tables'
            with self.assertRaises(ValueError): b.restore_archive(temp, dest, raw+b'x', artifact, receipt)
            self.assertFalse(dest.exists())

    def test_existing_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp)/'.local/tables'; dest.mkdir(parents=True)
            with self.assertRaises(ValueError): b.safe_destination(temp, dest)

    def test_outside_local(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError): b.safe_destination(temp, Path(temp)/'tables')

    def test_symlink_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp)/'.local'; dest.symlink_to(Path(temp), target_is_directory=True)
            with self.assertRaises(ValueError): b.safe_destination(temp, dest/'tables')


class HatchTests(unittest.TestCase):
    def test_gap_never_becomes_new_grant(self):
        result = b.hatch_disposition(hatch())
        self.assertEqual(result['disposition'], 'HISTORICAL_HATCH_REFERENCE_NO_NEW_GRANT')
        for key in ('direct_grant','shared_grant','owner_overlay_grant','grant_on_evolution','acquisition_impossible_claimed','runtime_applied'):
            self.assertIs(result[key], False)

    def test_present_is_not_native_acceptance(self):
        result = b.hatch_disposition(hatch(True))
        self.assertEqual(result['disposition'], 'SELECTED_HATCH_MEMBERSHIP_CARRY_REFERENCE')
        self.assertFalse(result['runtime_applied'])

    def test_input_unchanged(self):
        row = hatch(); before = copy.deepcopy(row)
        b.hatch_disposition(row)
        self.assertEqual(row, before)

    def test_identity_mismatch(self):
        row = hatch(); row['hatch_species_id'] = 4
        with self.assertRaises(ValueError): b.hatch_disposition(row)

    def test_bool_identity(self):
        row = hatch(); row['hatch_species_id'] = True
        with self.assertRaises(ValueError): b.hatch_disposition(row)

    def test_unknown_membership(self):
        row = hatch(); row['hatch_selected_direct_egg_membership'] = None
        with self.assertRaises(ValueError): b.hatch_disposition(row)

    def test_source_promotion(self):
        row = hatch(); row['provenance']['add_as_shared_egg'] = True
        with self.assertRaises(ValueError): b.hatch_disposition(row)

    def test_grant_promotion(self):
        row = hatch(); row['direct_grant'] = True
        with self.assertRaises(ValueError): b.hatch_disposition(row)

    def test_missing_source(self):
        row = hatch(); row['provenance']['original_direct_egg_rows'] = []
        with self.assertRaises(ValueError): b.hatch_disposition(row)

    def test_duplicate_source_key(self):
        with self.assertRaises(ValueError): b.hatch_plan([hatch(), hatch()])

    def test_inconsistent_status(self):
        row = hatch(); row['cross_source_status'] = 'MEMBERSHIP_ONLY_NATIVE_PENDING'
        with self.assertRaises(ValueError): b.hatch_disposition(row)

    def test_side_change_excluded(self):
        row = hatch(); row['move_id'] = row['provenance']['move_id'] = 1063
        with self.assertRaises(ValueError): b.hatch_disposition(row)


if __name__ == '__main__': unittest.main()
