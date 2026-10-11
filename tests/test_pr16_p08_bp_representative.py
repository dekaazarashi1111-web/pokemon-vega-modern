"""P08 BPだけの新規契約。合成fixtureはunit専用、native証拠とはしない。"""
from pathlib import Path
import copy
import json
import os
import sys
import tempfile
import unittest
from unittest import mock
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts'),str(Path(__file__).resolve().parents[1])]
import pr16_p08_bp_representative as m
import pr16_p08_checkpoint as cp
import tests.test_pr16_bp_loss_return_evidence as fixtures


def sample():
    row,trace=fixtures.LossEvidenceTests().sample()
    row.update(status=m.STATUS,scope=m.SCOPE,case=m.CASE,candidate_sha256=m.TARGET['sha256'],
        manual_saves=1,fresh_cores=2,total_frames=18000,p08_saved_frame=12000,p08_reloaded_frame=18000,
        p08_save_counter_after=3,p08_loss_entry=m.LOSS_ENTRY,p08_party_bytes=600,p08_factory_bytes=106,
        p08_inventory_preserved=True,automatic_full_saves=0)
    trace=trace.replace(b'cb2=09ff4681',b'cb2=09ff59bd')
    trace+=b'original core destroyed; new core boot and normal Continue\n'
    trace+=b'P08_BP_LIFECYCLE saved=12000 reloaded=18000 counter_before=2 counter_after=3 party_bytes=600 factory_bytes=106\n'
    for name,frame,data in [('original_party',100,b'\x01'*600),('returned_party',9000,b'\x01'*600),
        ('returned_factory',9000,b'\0'*106),('reloaded_party',18000,b'\x01'*600),('reloaded_factory',18000,b'\0'*106)]:
        trace+=f'P08_BP_BYTES name={name} frame={frame} size={len(data)} hex={data.hex()}\n'.encode()
    return row,trace,dict(returncode=0,timed_out=False,spawn_error=None)


class BPRepresentativeTests(unittest.TestCase):
    def test_strict_target_context(self):
        row,trace,proc=sample();self.assertEqual(m.validate(m.e.stable(row),trace,proc),row)
    def test_old_candidate_not_relabelled(self):
        row,trace,proc=sample();row['candidate_sha256']='fcda15075a586d59f4f9da5f7f55a294765f826ab1453a576e74192df822d879'
        with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace,proc)
    def test_bad_processes(self):
        for key,value in [('returncode',1),('returncode',False),('timed_out',True),('spawn_error','failed')]:
            with self.subTest(key=key,value=value):
                row,trace,proc=sample();proc[key]=value
                with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace,proc)
    def test_missing_byte_witness(self):
        row,trace,proc=sample();trace=b'\n'.join(x for x in trace.split(b'\n') if not x.startswith(b'P08_BP_BYTES name=reloaded_party '))
        with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace,proc)
    def test_duplicate_byte_witness(self):
        row,trace,proc=sample();line=next(x for x in trace.splitlines() if b'name=returned_party ' in x)
        with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace+line+b'\n',proc)
    def test_changed_party_byte(self):
        row,trace,proc=sample();trace=trace.replace(b'name=reloaded_party frame=18000 size=600 hex=01',b'name=reloaded_party frame=18000 size=600 hex=02')
        with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace,proc)
    def test_changed_factory_byte(self):
        row,trace,proc=sample();trace=trace.replace(b'name=reloaded_factory frame=18000 size=106 hex=00',b'name=reloaded_factory frame=18000 size=106 hex=01')
        with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace,proc)
    def test_wrong_return_and_accounting(self):
        for key,value in [('battle_outcome',1),('final_party_count',3),('p08_loss_entry',0x09FF4681),('final_script_pointer',1),
            ('manual_saves',0),('fresh_cores',1),('p08_save_counter_after',4),('p08_inventory_preserved',False),
            ('automatic_full_saves',1),('p08_saved_frame',18001),('final_marker',1)]:
            with self.subTest(key=key):
                row,trace,proc=sample();row[key]=value
                with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace,proc)
    def test_missing_new_loss_dispatch(self):
        row,trace,proc=sample();trace=trace.replace(b'cb2=09ff59bd',b'cb2=09ff4681')
        with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace,proc)
    def test_whiteout_rejected(self):
        row,trace,proc=sample()
        with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace+b'BP_RETURN label=bad cb2=08055f65\n',proc)
    def test_missing_cold_boot(self):
        row,trace,proc=sample();trace=trace.replace(b'original core destroyed; new core boot and normal Continue\n',b'')
        with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace,proc)
    def test_unknown_or_missing_field(self):
        for remove in (False,True):
            row,trace,proc=sample()
            if remove:del row['input_only_after_guard']
            else:row['unexpected']=True
            with self.assertRaises((ValueError,KeyError)):m.validate(m.e.stable(row),trace,proc)
    def test_bool_as_counter_rejected(self):
        row,trace,proc=sample();row['manual_saves']=True
        with self.assertRaises(ValueError):m.validate(m.e.stable(row),trace,proc)
    def test_original_validator_context_restored(self):
        import pr16_bp_selection_native as launch
        before=launch.SHA;row,trace,proc=sample();m.validate(m.e.stable(row),trace,proc);self.assertEqual(launch.SHA,before)
    def test_derivation_preserves_prefix_and_adds_only_extension(self):
        import pr16_bp_loss_return_native as old
        source=old.derived_driver().assemble_controller().encode();header=(m.ROOT/m.HEADER).read_bytes()
        new=m.adapt_controller(source,header)
        self.assertIn(header,new);self.assertIn(b'struct BPReturn finish=br_battle_return(c,party,counter);',new)
        self.assertIn(b'struct P08BPLifecycle p08=p08_bp_lifecycle',new)
        self.assertEqual(new.count(b'"'+m.CASE.encode()+b'"'),1)
        for token in (b'write8(',b'write16(',b'write32(',b'call_preserving(',b'loadState',b'saveState'):
            self.assertNotIn(token,header)
    def test_changed_derivation_anchor_rejected(self):
        with self.assertRaises(ValueError):m.adapt_controller(b'int main(void){}',b'/* header */')
    def test_checkpoint_invalid_scope_rejected_before_writes(self):
        with mock.patch.object(cp.b,'scope',return_value='a'*40),mock.patch.object(cp.b.resume,'validate',return_value={}),mock.patch.dict(os.environ,GITHUB_RUN_ID='1'):
            for phase,value in [('UNKNOWN',dict(task='TEST',release_ready=False,rom_changes=0)),('START',dict(task='TEST',release_ready=True,rom_changes=0))]:
                with self.subTest(phase=phase),self.assertRaises(ValueError):
                    cp.save('unused',value,(),Path('/unused'),phase,'stop','TEST','next',[])
    def test_pack_excludes_rom_private_work_and_preserves_text(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);(out/'work').mkdir();(out/'original').mkdir()
            (out/'work/private.srm').write_bytes(b'secret');(out/'work/candidate.gba').write_bytes(b'rom')
            (out/'original/source.json').write_bytes(b'{}\n');(out/'captured.stdout').write_bytes(b'original\n\n')
            cp.pack(out,())
            self.assertEqual([x.name for x in (out/'artifact').iterdir()],['captured.stdout'])
            self.assertEqual((out/'artifact/captured.stdout').read_bytes(),b'original\n\n')


if __name__=='__main__':unittest.main()
