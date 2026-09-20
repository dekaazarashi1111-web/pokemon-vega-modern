"""合成原本による照合器の契約。これ自体はnative受入ではない。"""
import copy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_circus_battle30_receipt as r

class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.result=dict(status='PASS_CIRCUS_CONTINUOUS_LIFECYCLE',candidate_sha256=r.TARGET['sha256'],
            wins=30,losses=0,battles=30,bp_earned=90,host_write_barriers=7,input_only_after_guard=True,
            warnings_errors=0,owner_bytes_verified=64,party_bytes_verified=600,manual_saves=1,
            fresh_cores=2,save_counter_before=2,save_counter_after=3,
            physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
        self.files={'execution/'+r.CASE+'.stdout':b'synthetic stdout only',
                    'execution/'+r.CASE+'.stderr':b'synthetic stderr only',
                    'execution/'+r.CASE+'.process.json':json.dumps(dict(schema_version=1,returncode=0,timed_out=False,spawn_error=None)).encode()}
        self.visual={}
        for n in range(4):
            name=f'synthetic-{n}.ppm';self.files['screens/'+name]=b'P6\n240 160\n255\n'+bytes(240*160*3)
            self.visual[name]='合成fixture。実画面の受入ではない。'
        self.report=dict(recording_run=r.RUN,source_head=r.SOURCE,workflow_source_head=r.SOURCE,candidate=r.TARGET,
            new_emulator_processes=1,arm_compiles=0,arm_links=0,rom_changes=0,accepted_standalone_replays=0,
            process=dict(schema_version=1,returncode=0,timed_out=False,spawn_error=None),result=self.result,prefix={},matchup_prefix=dict(exact_event_count=138,continuation_prefix_wins=29),
            generated={},screens={n:r.identity(self.files['screens/'+n]) for n in self.visual},failures=[],
            lifecycle_verified=True,genuine_30_wins_verified=True,executable={},native_source_head=r.SOURCE,
            physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
            previous_attempt={'original_conclusion':'failure','review':{'legacy_validator_failure_preserved':True}},
            text_evidence={r.PREFIX+r.CASE+s:r.identity(self.files['execution/'+r.CASE+s]) for s in ('.stdout','.stderr','.process.json')})
        self.run=dict(id=r.RUN,head_sha=r.SOURCE,status='completed',conclusion='success')
        self.job=dict(id=r.JOB,run_id=r.RUN,status='completed',conclusion='success')
        self.artifact=dict(id=r.ARTIFACT,workflow_run=dict(id=r.RUN,head_sha=r.SOURCE),expired=False)

    def archive(self):
        self.files['native-result.json']=json.dumps(self.report).encode()
        return self.pack(self.files)

    @staticmethod
    def pack(files):
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
            for name,raw in files.items():z.writestr(name,raw)
        return buffer.getvalue()

    def check(self,raw=None,visual=None):
        if raw is None:raw=self.archive()
        bound=r.identity(raw);self.artifact.update(size_in_bytes=len(raw),digest='sha256:'+bound['sha256'])
        with patch.object(r,'ARCHIVE',bound):
            return r.validate(self.report,raw,self.run,self.job,self.artifact,self.visual if visual is None else visual)

    def test_complete_projection_is_scoped_and_does_not_replay(self):
        value=self.check()
        self.assertTrue(value['genuine_30_wins_verified'])
        self.assertEqual(value['new_emulator_processes'],0)
        self.assertEqual(value['arm_compiles'],0)
        self.assertEqual(value['accepted_standalone_replays'],0)
        self.assertFalse(value['physical_admission_accepted'])
        self.assertFalse(value['release_ready'])
        self.assertEqual(value['previous_failure_preserved']['original_conclusion'],'failure')

    def test_scoped_loss_keeps_failed_conclusion(self):
        self.report['result'].update(wins=29,losses=1,bp_earned=81)
        self.report['genuine_30_wins_verified']=False
        self.run['conclusion']=self.job['conclusion']='failure'
        value=self.check()
        self.assertFalse(value['genuine_30_wins_verified'])
        self.assertEqual(value['original_conclusion'],'failure')

    def test_running_not_completed(self):
        self.run['status']='in_progress'
        with self.assertRaises(ValueError):self.check()

    def test_wrong_head(self):
        self.run['head_sha']='0'*40
        with self.assertRaises(ValueError):self.check()

    def test_original_failure_not_relabelled(self):
        self.run['conclusion']='failure'
        with self.assertRaises(ValueError):self.check()

    def test_lifecycle_failure_not_promoted(self):
        self.report['lifecycle_verified']=False
        self.report['failures']=[{'stage':'prefix','type':'ValueError'}]
        with self.assertRaises(ValueError):self.check()

    def test_projection_corruption(self):
        raw=self.archive();self.report['result']=dict(self.result,wins=31)
        with self.assertRaises(ValueError):self.check(raw)

    def test_missing_visual(self):
        with self.assertRaises(ValueError):self.check(visual={})

    def test_image_corruption(self):
        name='screens/'+next(iter(self.visual));self.files[name]=self.files[name][:-1]+b'x'
        with self.assertRaises(ValueError):self.check()

    def test_physical_gate_cannot_be_closed(self):
        self.report['suppression_accepted']=True
        with self.assertRaises(ValueError):self.check()

    def test_unsafe_member(self):
        raw=self.pack({'../escape.json':b'{}'})
        with self.assertRaises(ValueError):r.members(raw)

    def test_private_binary_excluded(self):
        raw=self.pack({'scratch.srm':b'synthetic-not-a-save'})
        with self.assertRaises(ValueError):r.members(raw)

    def test_process_failure_not_hidden_by_pass_stdout(self):
        self.report['process']['returncode']=1
        with self.assertRaises(ValueError):self.check()

    def test_process_raw_must_match_report(self):
        self.files['execution/'+r.CASE+'.process.json']=b'{"returncode":0}'
        self.report['text_evidence'][r.PREFIX+r.CASE+'.process.json']=r.identity(self.files['execution/'+r.CASE+'.process.json'])
        with self.assertRaises(ValueError):self.check()

    def test_duplicate_zip_member_rejected(self):
        import warnings
        buffer=io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',UserWarning)
            with zipfile.ZipFile(buffer,'w') as archive:
                archive.writestr('duplicate.json','{}');archive.writestr('duplicate.json','{}')
        with self.assertRaises(ValueError):r.members(buffer.getvalue())

class CompactTraceTests(unittest.TestCase):
    def fixture(self):
        def event(label,frame):
            return 'CIRCUS_CONTINUOUS '+json.dumps(dict(label=label,frame=frame,battle=29,outcome=1,bp=90,save_counter=3,flags=8192))
        mon=bytearray(88);mon[0]=8;mon[33:35]=bytes([11,11]);mon[40]=110;mon[44]=182;mon[76]=32;mon[36:40]=bytes([40,13,32,16])
        observation='CIRCUS_RELIABILITY frame=20 streak=29 selected=1 actual=2 blocked=0 accuracy=100 score=458737 own='+mon.hex()+' foe='+mon.hex()
        return ('\n'.join([event('action',10),observation,event('outcome',30),event('saved',40),event('reloaded',50)])+'\n').encode()

    def test_observed_ids_bits_and_terminal_only(self):
        value=r.compact_trace(self.fixture())
        self.assertEqual(value['battle_number'],30)
        self.assertEqual(value['row_count'],1)
        self.assertEqual(value['rows'][0]['own']['status1_hex'],'00000020')
        self.assertFalse(value['truncated'])
        self.assertNotIn('genuine_30_wins_verified',value)

    def test_malformed_snapshot_rejected(self):
        with self.assertRaises(ValueError):r.compact_trace(self.fixture().replace(b'own=08',b'own=',1))

    def test_no_action_rejected(self):
        with self.assertRaises(ValueError):r.compact_trace(b'no evidence\n')

    def test_frame_order_rejected(self):
        raw=self.fixture();line=next(l for l in raw.splitlines() if l.startswith(b'CIRCUS_RELIABILITY'))
        with self.assertRaises(ValueError):r.compact_trace(raw+line+b'\n')

    def test_explicit_truncation(self):
        raw=self.fixture();line=next(l for l in raw.splitlines() if l.startswith(b'CIRCUS_RELIABILITY'))
        value=r.compact_trace(raw+line.replace(b'frame=20',b'frame=21')+b'\n',limit=1)
        self.assertTrue(value['truncated']);self.assertEqual(value['row_count'],2)
        self.assertEqual(len(value['rows']),1)

if __name__=='__main__':unittest.main()


