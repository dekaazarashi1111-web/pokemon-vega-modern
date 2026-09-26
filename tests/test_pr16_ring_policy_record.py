"""記録器の拒否契約。合成fixtureはnative成功や受入数へ数えない。"""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from scripts import pr16_ring_policy_record as r

class RecordContracts(unittest.TestCase):
    def archive(self,entries=None,manifest=None):
        entries={'evidence.txt':b'original\n'} if entries is None else entries
        members={name:r.identity(data) for name,data in entries.items()} if manifest is None else manifest
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            for name,data in entries.items():z.writestr(name,data)
            z.writestr('members.json',json.dumps(members).encode())
        return out.getvalue()

    def inputs(self):
        c=dict(candidate=dict(sha256=r.BP_SHA),latest_native_run=34946969126,physical_gap_count=3,
               earning_result={'wins':3,'bp':9},spending_result={'bp_after':8})
        s=dict(candidate=dict(c['candidate']),latest_native_run=34946969126,latest_native_job=104308573084,
               status='PASS_NATIVE_BP_SPENDING_SAVE_CONTINUE',latest_native_tested_head='a'*40,
               last_accepted_native_run=34946969126,last_accepted_native_tested_head='a'*40,
               remaining_p08_gate_ids=['FINAL_NATIVE_ACCEPTANCE','RELEASE_DECISION'],
               remaining_physical_gap_ids=[r.RING,r.POLICY,'PHYSICAL_CIRCUS_ADMISSION'],
               release_ready=False,bp=dict(spending_accepted=True),next_action={},do_not_repeat=[])
        b=dict(next_integration_candidate={'candidate':dict(c['candidate']),'source_path':'bp-original.json'},
               remaining_conditions=[dict(id='NATURAL_CAPTURE_GEAR',remaining_supply_gap_ids=[r.RING,r.POLICY],
                    selected_supply_entrypoints={r.RING:None,r.POLICY:{'scope':'legacy'}},reason_ja='旧境界。'),
                    dict(id='PHYSICAL_CIRCUS_ADMISSION',phase='P05',notes='untouched'),
                    *[dict(id=key,phase='P08',notes='untouched') for key in s['remaining_p08_gate_ids']]])
        report=dict(classification='SCOPED_RING_ORDINARY_POLICY_ACCEPTANCE',closed_physical_ids=[r.RING,r.POLICY],
                    ring_acquisition_accepted=True,ordinary_battle_accepted=True,release_ready=False,
                    candidate=dict(r.CANDIDATE,crc32='9EFB0E56'),run_id=123,tested_head='b'*40)
        return s,b,c,report

    def test_manifest_and_original_bytes_round_trip(self):
        data=self.archive();files,m=r.unpack(data,r.identity(data))
        self.assertEqual(files['evidence.txt'],b'original\n');self.assertEqual(m['evidence.txt'],r.identity(b'original\n'))

    def test_zip_identity_rejects_before_read(self):
        data=self.archive()
        with self.assertRaises(ValueError):r.unpack(data,dict(size=len(data),sha256='0'*64))

    def test_changed_member_or_manifest_fails(self):
        for manifest in ({}, {'evidence.txt':r.identity(b'changed')}):
            data=self.archive(manifest=manifest)
            with self.assertRaises(ValueError):r.unpack(data,r.identity(data))

    def test_private_suffix_path_traversal_and_binary_text_rejected(self):
        for name,data in (('candidate.gba',b'private'),('../leak.txt',b'a'),('/outside.txt',b'a'),
                          ('a\\b.txt',b'a'),('not-text.txt',b'\0')):
            raw=self.archive({name:data})
            with self.assertRaises(ValueError):r.unpack(raw,r.identity(raw))

    def test_failed_or_boolean_process_rejected(self):
        r.verify_process(copy.deepcopy(r.PROCESS))
        for key,value in (('returncode',1),('returncode',False),('timed_out',True),('spawn_error','error'),('extra',0)):
            p=dict(r.PROCESS);p[key]=value
            with self.assertRaises(ValueError):r.verify_process(p)

    def test_current_source_binding_and_drift(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'source.py';p.write_bytes(b'pass\n');bound={'source.py':r.identity(p.read_bytes())}
            r.verify_sources(bound,root);p.write_bytes(b'changed\n')
            with self.assertRaises(ValueError):r.verify_sources(bound,root)
            with self.assertRaises(ValueError):r.verify_sources({'../source.py':{}},root)

    def test_projection_is_nonmutating(self):
        inputs=self.inputs();before=copy.deepcopy(inputs);r.project(*inputs);self.assertEqual(inputs,before)

    def test_bp_authority_and_results_are_preserved(self):
        s,b,c,report=self.inputs();ns,nb,nc=r.project(s,b,c,report)
        for key in ('candidate','latest_native_run','latest_native_tested_head','status','release_ready'):
            self.assertEqual(ns[key],s[key])
        restored=dict(nc,physical_gap_count=3);self.assertEqual(restored,c)
        self.assertEqual(nb['next_integration_candidate']['candidate'],b['next_integration_candidate']['candidate'])
        self.assertEqual(nb['next_integration_candidate']['source_path'],'bp-original.json')

    def test_only_ring_policy_ids_close_and_global_count_matches(self):
        s,b,c,report=self.inputs();ns,nb,nc=r.project(s,b,c,report)
        self.assertEqual(ns['remaining_physical_gap_ids'],['PHYSICAL_CIRCUS_ADMISSION'])
        self.assertEqual(nc['physical_gap_count'],1)
        self.assertTrue(nb['remaining_conditions'][0]['complete'])
        self.assertEqual(nb['remaining_conditions'][1:],b['remaining_conditions'][1:])
        self.assertEqual(ns['next_action']['id'],'PHYSICAL_CIRCUS_ADMISSION')
        self.assertEqual(ns['bp']['next_step'],ns['next_action']['goal_ja'])

    def test_unverified_or_release_acceptance_rejected(self):
        for key,value in (('ordinary_battle_accepted',False),('ring_acquisition_accepted',False),
                          ('release_ready',True),('closed_physical_ids',[r.RING])):
            args=list(self.inputs());args[3][key]=value
            with self.assertRaises(ValueError):r.project(*args)

    def test_previous_bp_or_unknown_candidate_may_not_be_relabelled(self):
        args=list(self.inputs());args[3]['candidate']['sha256']=r.BP_SHA
        with self.assertRaises(ValueError):r.project(*args)
        args=list(self.inputs());args[0]['latest_native_run']=123
        with self.assertRaises(ValueError):r.project(*args)

    def test_missing_duplicate_or_already_closed_ledger_fails(self):
        args=list(self.inputs());args[1]['remaining_conditions'].append(copy.deepcopy(args[1]['remaining_conditions'][0]))
        with self.assertRaises(ValueError):r.project(*args)
        args=list(self.inputs());args[1]['remaining_conditions'][0]['remaining_supply_gap_ids']=[]
        with self.assertRaises(ValueError):r.project(*args)

    def test_unknown_existing_gap_count_or_extra_p08_gate_fails(self):
        args=list(self.inputs());args[2]['physical_gap_count']=4
        with self.assertRaises(ValueError):r.project(*args)
        args=list(self.inputs());args[1]['remaining_conditions'].append(dict(id='EXTRA',phase='P08'))
        with self.assertRaises(ValueError):r.project(*args)

if __name__=='__main__':unittest.main()
