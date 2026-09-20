"""通常戦闘の受入は原本を再利用し、改竄/重複受入を拒否する。"""
import copy
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1]/'scripts/pr16_p08_ordinary_acceptance.py'
spec = importlib.util.spec_from_file_location('ordinary_accept', PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def valid():
    return dict(candidate=dict(m.TARGET), workflow_source_head=m.HEAD, recording_run=m.RUN,
                regression_id='P08_CIRCUS_POST_EXIT_ORDINARY', case=m.CASE,
                task='USER-20260920-P08-ORDINARY-ABI', native_verified=True,
                representative_accepted=False, visual_review_completed=False, release_ready=False,
                failures=[], new_emulator_processes=1, fresh_cores=1, host_compiles=1,
                arm_compiles=0, arm_links=0, accepted_standalone_replays=0,
                prefix_wins_reexecuted=0, rom_changes=0,
                screens={name:dict(size=115215, sha256=digest) for name,digest in m.SCREENS.items()},
                previous_trial=dict(run_id=35512429611, conclusion='failure', accepted=False))


class OrdinaryAcceptanceTests(unittest.TestCase):
    def test_original_pass(self):
        before = valid()
        self.assertIsNone(m.verify(before))
        self.assertEqual(before, valid())

    def test_candidate_and_source_identity(self):
        for key, value in [('candidate', dict(size=33554432, sha256='0'*64)),
                           ('workflow_source_head', '0'*40), ('recording_run', 1),
                           ('case', 'facility'), ('regression_id', 'other')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.verify(valid() | {key:value})

    def test_boolean_accounting_is_not_integer(self):
        for key in ('recording_run', 'new_emulator_processes', 'fresh_cores', 'host_compiles',
                    'arm_compiles', 'arm_links', 'accepted_standalone_replays',
                    'prefix_wins_reexecuted', 'rom_changes'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.verify(valid() | {key:bool(valid()[key])})

    def test_reexecution_or_rom_change_rejected(self):
        for key in ('new_emulator_processes', 'fresh_cores', 'arm_compiles', 'arm_links',
                    'accepted_standalone_replays', 'prefix_wins_reexecuted', 'rom_changes'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.verify(valid() | {key:valid()[key]+1})

    def test_unverified_and_already_accepted_rejected(self):
        for key in ('native_verified', 'representative_accepted', 'visual_review_completed', 'release_ready'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.verify(valid() | {key:not valid()[key]})

    def test_old_failure_not_relabelled(self):
        for change in (dict(conclusion='success'), dict(accepted=True), dict(run_id=0)):
            value = valid()
            value['previous_trial'].update(change)
            with self.assertRaises(ValueError):
                m.verify(value)

    def test_screen_inventory_and_hash(self):
        for change in ('missing', 'extra', 'digest'):
            value = valid()
            name = next(iter(value['screens']))
            if change == 'missing':
                value['screens'].pop(name)
            elif change == 'extra':
                value['screens']['other.ppm'] = value['screens'][name]
            else:
                value['screens'][name]['sha256'] = '0'*64
            with self.subTest(change=change), self.assertRaises(ValueError):
                m.verify(value)

    def test_screen_missing_and_tampered_bytes(self):
        expected = valid()['screens']
        with self.assertRaises(ValueError):
            m.verify_images({}, expected)
        members = {'screens/'+name:b'P6\n240 160\n255\n'+b'\0'*115200 for name in m.SCREENS}
        with self.assertRaises(ValueError):
            m.verify_images(members, expected)


if __name__ == '__main__':
    unittest.main()
