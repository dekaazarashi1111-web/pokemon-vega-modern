"""記録validatorの異常系。synthetic fixtureを実入場証拠として使用しない。"""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from scripts import pr16_circus_record as m
from scripts.pr16_circus_link_probe import REQUIRED_FUNCTIONS


def reports():
    source=dict(classification='CIRCUS_PENDING_IMPLEMENTED_SOURCE_LINK_PENDING',independent_arm_compiles=2,
        new_emulator_processes=0,accepted_native_cases_replayed=0,rom_changes=0,physical_admission_accepted=False,release_ready=False)
    functions={name:dict(address=0x09100000+i*32,size=24,sha256=str(i)*64) for i,name in enumerate(REQUIRED_FUNCTIONS)}
    symbols={name:dict(address=row['address'],size=row['size'],kind='T',matches_candidate=True,
        elf_bytes={k:row[k] for k in ('size','sha256')},candidate_bytes={k:row[k] for k in ('size','sha256')}) for name,row in functions.items()}
    link=dict(classification='CIRCUS_OWNER_LINKED_NOT_PHYSICAL_ACCEPTANCE',candidate=m.PARENT,
        new_emulator_processes=0,accepted_native_cases_replayed=0,rom_changes=0,physical_admission_accepted=False,release_ready=False,
        new_runtime=dict(independent_links=2,payload=m.PAYLOAD,no_rom_payload_inserted=True,placement_is_link_test_only=True,
            owners={name:functions[name]['address'] for name in REQUIRED_FUNCTIONS[:2]}),
        fixed_build={'verified_functions':functions},symbols=symbols,
        routes=dict(decoded_roots=5335,invalid_roots=[{}]*6,native_indirect_callers_fully_excluded=False,
            no_match_proves_absence=False,physical_entrance_accepted=False,selected_references=[]))
    return source,link


def archive(files,manifest=True):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        for name,raw in files.items():z.writestr(name,raw)
        if manifest:z.writestr('members.json',m.stable({n:m.identity(raw) for n,raw in files.items()}))
    return out.getvalue()


class RecordContracts(unittest.TestCase):
    def test_json_duplicate_and_nonfinite_rejected(self):
        for data in ('{"a":1,"a":2}','{"a":NaN}','{"a":Infinity}'):
            with self.subTest(data=data),self.assertRaises(ValueError):m.load(data)

    def test_exact_boolean_not_integer(self):
        with self.assertRaises(ValueError):m.exact(True,1,'bad')
        with self.assertRaises(ValueError):m.exact(0,False,'bad')

    def test_safe_text_archive_and_all_members(self):
        original={'dir/a.ld':b'TEXT\n','data.json':b'{}\n'};raw=archive(original)
        files,manifest=m.unpack(raw,m.identity(raw));self.assertEqual(set(manifest),set(original))
        self.assertEqual(files['dir/a.ld'],original['dir/a.ld'])

    def test_wrong_archive_identity_rejected(self):
        raw=archive({'a.txt':b'hi'})
        with self.assertRaises(ValueError):m.unpack(raw,dict(size=len(raw),sha256='0'*64))

    def test_traversal_nontext_and_secrets_rejected(self):
        for name,data in (('../escape.txt',b'a'),('/abs.txt',b'a'),('a/../b.txt',b'a'),('a\\b.txt',b'a'),
                          ('a.gba',b'a'),('a.txt',b'\0'),('a.txt',b'ghp_'+b'x'*36)):
            raw=archive({name:data})
            with self.subTest(name=name),self.assertRaises(ValueError):m.unpack(raw,m.identity(raw))

    def test_symlink_member_rejected(self):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            info=zipfile.ZipInfo('a.txt');info.create_system=3;info.external_attr=0o120777<<16;z.writestr(info,'target')
        raw=out.getvalue()
        with self.assertRaises(ValueError):m.unpack(raw,m.identity(raw))

    def test_member_digest_corruption_rejected(self):
        raw=archive({'a.txt':b'old','members.json':m.stable({'a.txt':m.identity(b'new')})},False)
        with self.assertRaises(ValueError):m.unpack(raw,m.identity(raw))

    def test_manifestless_ci_uses_bound_zip(self):
        raw=archive({'check.json':b'{}'},False)
        files,manifest=m.unpack(raw,m.identity(raw),False)
        self.assertEqual(manifest['check.json'],m.identity(files['check.json']))

    def test_test_count_failure_and_skips_rejected(self):
        m.tests_pass(b'Ran 10 tests in 0.123s\n\nOK\n',10)
        for raw in (b'Ran 9 tests in 1s\n\nOK\n',b'Ran 10 tests in 1s\n\nFAILED\n',b'Ran 10 tests in 1s\n\nOK (skipped=1)\n'):
            with self.assertRaises(ValueError):m.tests_pass(raw,10)

    def test_owner_link_boundaries_accept_unit_fixture(self):m.validate_reports(*reports())

    def test_each_owner_whole_bytes_required(self):
        for name in REQUIRED_FUNCTIONS:
            source,link=reports();link['symbols'][name]['candidate_bytes']={'size':24,'sha256':'f'*64}
            with self.subTest(name=name),self.assertRaises(ValueError):m.validate_reports(source,link)

    def test_owner_closure_and_link_target_rejected(self):
        source,link=reports();del link['fixed_build']['verified_functions'][REQUIRED_FUNCTIONS[-1]]
        with self.assertRaises(ValueError):m.validate_reports(source,link)
        source,link=reports();link['new_runtime']['owners'][REQUIRED_FUNCTIONS[0]]+=2
        with self.assertRaises(ValueError):m.validate_reports(source,link)

    def test_no_physical_or_release_promotion(self):
        for index in (0,1):
            for name in ('physical_admission_accepted','release_ready'):
                values=reports();values[index][name]=True
                with self.subTest(index=index,name=name),self.assertRaises(ValueError):m.validate_reports(*values)

    def test_no_native_replay_or_rom_change(self):
        for index in (0,1):
            for name in ('new_emulator_processes','accepted_native_cases_replayed','rom_changes'):
                values=reports();values[index][name]=1
                with self.subTest(index=index,name=name),self.assertRaises(ValueError):m.validate_reports(*values)

    def test_no_root_absence_inference(self):
        for key in ('no_match_proves_absence','native_indirect_callers_fully_excluded','physical_entrance_accepted'):
            source,link=reports();link['routes'][key]=True
            with self.subTest(key=key),self.assertRaises(ValueError):m.validate_reports(source,link)

    def test_payload_compilation_and_placement_boundaries(self):
        for k,v in (('independent_links',1),('no_rom_payload_inserted',False),('placement_is_link_test_only',False),('payload',{})):
            source,link=reports();link['new_runtime'][k]=v
            with self.subTest(key=k),self.assertRaises(ValueError):m.validate_reports(source,link)

    def test_source_bytes_and_safe_path_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'a.py').write_bytes(b'pass\n');binding={'a.py':m.identity(b'pass\n')}
            m.verify_sources(root,binding);(root/'a.py').write_bytes(b'changed')
            with self.assertRaises(ValueError):m.verify_sources(root,binding)
            with self.assertRaises(ValueError):m.verify_sources(root,{'../outside':binding['a.py']})

    def test_current_projection_preserves_other_acceptance_and_bp(self):
        from scripts import pr16_resume as resume
        state=m.load((m.ROOT/resume.STATE).read_bytes());backlog=m.load((m.ROOT/resume.BACKLOG).read_bytes())
        old=copy.deepcopy((state,backlog))
        report=dict(classification='CIRCUS_PENDING_IMPLEMENTATION_LINKED_PHYSICAL_ENTRY_OPEN',physical_admission_accepted=False,
            rom_changes=0,tested_head='8df683fb7bbb6cea490ea8a97616b5171fe5383a',link_run_id=35353620141)
        s,b=m.project(state,backlog,report)
        self.assertEqual((state,backlog),old)
        self.assertEqual(s['candidate'],state['candidate']);self.assertEqual(s['remaining_physical_gap_ids'],['PHYSICAL_CIRCUS_ADMISSION'])
        for oldrow,newrow in zip(backlog['remaining_conditions'],b['remaining_conditions']):
            if oldrow['id']!='PHYSICAL_CIRCUS_ADMISSION':self.assertEqual(oldrow,newrow)
            else:self.assertIsNone(newrow['success_evidence']);self.assertIsNot(newrow.get('complete'),True)

    def test_closed_entry_rejected(self):
        from scripts import pr16_resume as resume
        state=m.load((m.ROOT/resume.STATE).read_bytes());backlog=m.load((m.ROOT/resume.BACKLOG).read_bytes())
        next(r for r in backlog['remaining_conditions'] if r['id']=='PHYSICAL_CIRCUS_ADMISSION')['complete']=True
        report=dict(classification='CIRCUS_PENDING_IMPLEMENTATION_LINKED_PHYSICAL_ENTRY_OPEN',physical_admission_accepted=False,rom_changes=0)
        with self.assertRaises(ValueError):m.project(state,backlog,report)


if __name__=='__main__':unittest.main()
