"""通常UIの過大受入を拒否する新規境界試験。保存済みnative/旧unitは実行しない。"""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_special_wild_gameplay_native as m


class NativeResultTests(unittest.TestCase):
    def events(self, method='hidden'):
        mon=bytearray(100);struct.pack_into('<I',mon,0,12345);struct.pack_into('<H',mon,32,843)
        struct.pack_into('<4H',mon,44,1,2,3,244);mon[52:56]=bytes([10,20,30,10]);mon[84]=44
        pcs=[0x09220198,0x093BEA98,0x0939273C] if method=='hidden' else [0x08082750,0x093BEA68,0x09392714]
        events=[dict(event='entry',method=method,attempt=1,pc=pc,frame=15) for pc in pcs]
        events += [dict(event='special_setter',attempt=1,frame=17,move=244)]
        events += [dict(event=k,method=method,attempt=1,frame=n,party=mon.hex()) for k,n in [('enemy',20),('captured',30),('saved',40),('reloaded',50)]]
        events += [dict(status='PASS',scope=m.SCOPE,method=method,candidate_sha256=m.prep.CANDIDATE['sha256'],
            manual_saves=1,fresh_cores=2,host_write_barriers=7,observed_host_calls=0,ball_consumed=1,
            initial_fixtures=True,party_and_inventory_persisted=True,release_ready=False,witness=[10,20,30,40,50],frames=60,
            attempts=1,species=843,special_move=244)]
        return events

    def run_events(self, ev, method='hidden'):
        return m.native_result(('\n'.join(json.dumps(x) for x in ev)+'\n').encode(),method)

    def test_hidden_exact_evidence(self): self.assertEqual(self.run_events(self.events())['species'],843)
    def test_fishing_exact_evidence(self): self.assertEqual(self.run_events(self.events('fishing'),'fishing')['species'],843)
    def test_terminal_is_required(self):
        with self.assertRaises(ValueError): self.run_events(self.events()[:-1])
    def test_no_events_after_result(self):
        with self.assertRaises(ValueError): self.run_events(self.events()+[dict(event='late')])
    def test_duplicate_result(self):
        ev=self.events();ev.append(copy.deepcopy(ev[-1]))
        with self.assertRaises(ValueError): self.run_events(ev)
    def test_wrong_native_scope(self):
        ev=self.events();ev[-1]['scope']='DIRECT_CALL'
        with self.assertRaises(ValueError): self.run_events(ev)
    def test_candidate_mismatch(self):
        ev=self.events();ev[-1]['candidate_sha256']='0'*64
        with self.assertRaises(ValueError): self.run_events(ev)
    def test_method_mismatch(self):
        with self.assertRaises(ValueError): self.run_events(self.events(),'fishing')
    def test_all_counter_boundaries(self):
        for key in ('manual_saves','fresh_cores','host_write_barriers','observed_host_calls','ball_consumed'):
            with self.subTest(key=key):
                ev=self.events();ev[-1][key]+=1
                with self.assertRaises(ValueError): self.run_events(ev)
    def test_boolean_count_rejected(self):
        ev=self.events();ev[-1]['manual_saves']=True
        with self.assertRaises(ValueError): self.run_events(ev)
    def test_fixture_disclosure_required(self):
        ev=self.events();ev[-1]['initial_fixtures']=False
        with self.assertRaises(ValueError): self.run_events(ev)
    def test_release_promotion_rejected(self):
        ev=self.events();ev[-1]['release_ready']=True
        with self.assertRaises(ValueError): self.run_events(ev)
    def test_out_of_order_witness_rejected(self):
        ev=self.events();ev[-1]['witness']=[10,30,20,40,50]
        with self.assertRaises(ValueError): self.run_events(ev)
    def test_missing_individual_stage(self):
        ev=[e for e in self.events() if e.get('event')!='saved']
        with self.assertRaises(ValueError): self.run_events(ev)
    def test_continue_individual_change(self):
        ev=self.events();ev[-2]['party']='ff'+ev[-2]['party'][2:]
        with self.assertRaises(ValueError): self.run_events(ev)
    def test_capture_pp_change(self):
        ev=self.events()
        for e in ev:
            if e.get('event') in ('captured','saved','reloaded'):
                raw=bytearray.fromhex(e['party']);raw[52]+=1;e['party']=raw.hex()
        with self.assertRaises(ValueError): self.run_events(ev)
    def test_wrong_special_slot(self):
        ev=self.events();ev[-1]['special_move']=245
        with self.assertRaises(ValueError): self.run_events(ev)
    def test_production_chain_required(self):
        ev=self.events();ev[0]['pc']=0x12345678
        with self.assertRaises(ValueError): self.run_events(ev)
    def test_only_one_setter(self):
        ev=self.events();ev.insert(3,copy.deepcopy(ev[3]))
        with self.assertRaises(ValueError): self.run_events(ev)
    def test_modified_artifact_refused_without_open(self):
        with self.assertRaises(ValueError): m.unwrap_data(b'not the fixed ZIP')
    def test_wrong_rom_refused(self):
        with self.assertRaises(ValueError): m.bind_ui(b'not the candidate')
    def test_runtime_radar_binding_not_catalog_scanner(self):
        rom=bytearray(0x1050768+40);table=0x1050768-348*40
        for item,cb in ((264,0x080A260D),(348,0x092201E1)):
            struct.pack_into('<H',rom,table+item*40+10,item);struct.pack_into('<I',rom,table+item*40+24,cb)
        with patch.object(m,'identity',return_value=m.prep.CANDIDATE):
            result=m.bind_ui(rom);self.assertEqual(result['hidden']['id'],348)
            struct.pack_into('<I',rom,0x1050768+24,0x080A34F9)
            with self.assertRaises(ValueError):m.bind_ui(rom)


if __name__=='__main__':unittest.main()
