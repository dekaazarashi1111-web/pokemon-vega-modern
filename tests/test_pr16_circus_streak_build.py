"""Circus限定clone・serializer・patch preimage契約。native受入とは分離。"""
from pathlib import Path
import csv
import importlib.util
import os
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('circus_streak_build',ROOT/'scripts/pr16_circus_streak.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class CircusStreakBuildTests(unittest.TestCase):
    def test_serializer_preserves_4016_other_bytes_and_binds_save_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe=Path(tmp)/'io'
            subprocess.run([os.environ.get('CC','cc'),'-std=c11','-O2','-Wall','-Wextra','-Werror','-pedantic',
                '-fsanitize=undefined','-fno-sanitize-recover=all','-I',str(ROOT),
                str(ROOT/'tests/fixtures/circus_streak_io_fixture.c'),str(ROOT/(b.PREFIX+'circus_streak.c')),
                str(ROOT/(b.PREFIX+'circus_streak_io.c')),'-o',str(exe)],check=True,capture_output=True,text=True)
            p=subprocess.run([str(exe)],check=True,capture_output=True,text=True,timeout=30)
            self.assertEqual(p.stdout,'PASS_CIRCUS_IO_HOST_ONLY untouched_payload_bytes=4016 native_processes=0\n')

    def test_clone_retains_selection_exchange_but_does_not_alias_factory_streaks(self):
        original=(ROOT/b.OLD_SOURCE).read_text()
        clone=b.isolated_source(original,(ROOT/(b.PREFIX+'circus_facility_policy.c')).read_text())
        for name in ('CommitSelection','BeginExchange','CommitExchange','SkipExchange'):
            renamed=original.replace('FacilityRuntime_','CircusRuntime_')
            a,z=b.function_span(renamed,'CircusRuntime_'+name)
            c,d=b.function_span(clone,'CircusRuntime_'+name)
            self.assertEqual(renamed[a:z],clone[c:d])
        for forbidden in ('factory.current_streak','factory.best_streak','factory.reward_claim_bits','VegaFactoryClaimReward','VegaSaveInitNew'):
            self.assertNotIn(forbidden,clone)
        for edge in ('CircusStreakRuntimeBegin()','CircusStreakRuntimeArm()','CircusStreakRuntimeRecord(outcome)','CircusStreakRuntimeRecover()'):
            self.assertIn(edge,clone)

    def test_source_boundary_drift_rejected(self):
        original=(ROOT/b.OLD_SOURCE).read_text();policy=(ROOT/(b.PREFIX+'circus_facility_policy.c')).read_text()
        with self.assertRaises(ValueError):
            b.isolated_source(original.replace('original_count =','changed_count ='),policy)
        with self.assertRaises(ValueError):
            b.isolated_source(original+original,policy)
        with self.assertRaises(ValueError):
            b.function_span('static void bad(void) {','bad')

    def test_patch_is_exact_and_reversible(self):
        original=bytes(range(32));patches=[dict(name='one',offset=4,before='04050607',after='ffffffff')]
        changed=b.bounded_patch(original,patches)
        self.assertEqual(changed,original[:4]+b'\xff'*4+original[8:])
        self.assertEqual(original,bytes(range(32)))

    def test_patch_rejects_stale_overlap_bounds_and_size(self):
        original=bytes(range(32));good=dict(name='one',offset=4,before='04050607',after='ffffffff')
        for patch in ({**good,'before':'eeeeeeee'},{**good,'offset':31},{**good,'after':'ff'}):
            with self.assertRaises(ValueError):b.bounded_patch(original,[patch])
        with self.assertRaises(ValueError):b.bounded_patch(original,[good,good])

    def test_owner_layout_has_no_live_overlap(self):
        for name,space,start,end in (('ram_layout.csv','EWRAM',0x0203DB00,0x0203DB40),
                                    ('save_layout.csv','SAVE_PARASITE_IMAGE_OFFSET',0x2A18,0x2A58)):
            with (ROOT/'config'/name).open() as f: rows=list(csv.DictReader(f))
            owned=[r for r in rows if r['owner']=='USER_20260919_CIRCUS_STREAK']
            self.assertEqual(len(owned),1)
            self.assertEqual(int(owned[0]['start'],16),start)
            self.assertEqual(int(owned[0]['end_exclusive'],16),end)
            self.assertEqual(int(owned[0]['size']),64)
            for row in rows:
                if row is owned[0] or row['address_space']!=space or row['status']!='LIVE':continue
                a,z=int(row['start'],16),int(row['end_exclusive'],16)
                self.assertFalse(a<end and start<z,(name,row['owner']))

    def test_sp072_adapter_is_read_only_and_requires_real_armed_owner(self):
        source=(ROOT/(b.PREFIX+'circus_streak_runtime.c')).read_text()
        get=source[source.index('EXPORT uint16_t CircusStreakRuntimeGet'):]
        self.assertIn('CircusStreakRuntimeArmed()',get)
        self.assertIn('STATE_GET(0x403Au) == 3u',get)
        self.assertIn('0x091025EDu',get)
        self.assertNotIn('->current =',get)
        self.assertNotIn('0x0203DFBC',source)
        self.assertNotIn('gBattleCircusFlags',source)

if __name__=='__main__':unittest.main()
