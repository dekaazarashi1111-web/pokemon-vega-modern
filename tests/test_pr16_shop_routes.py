"""Synthetic fail-closed contracts, not emulator acceptance."""
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_shop_routes as m
class ShopRoutesTests(unittest.TestCase):
    def sample(self,name):
        row=m.expected(name);row['total_frames']=10000
        row['witness']={key:(i+1)*100 for i,key in enumerate(m.TRACE)}
        if name=='missing-ring':
            for key in ('menu','selection','revisit'):row['witness'][key]=0
        return row
    def test_ten_cases_twenty_cores_six_exact_stones(self):
        self.assertEqual(len(m.CASES),10)
        self.assertEqual({v[0] for v in m.CASES.values() if v[1]==0},{1016,1012,1031,1029,1014,1035})
        self.assertEqual(sum(m.expected(n)['fresh_cores'] for n in m.CASES),20)
        for name in m.CASES:
            row=self.sample(name);self.assertEqual(m.validate(json.dumps(row).encode(),name,0),row)
    def test_each_witness_required_or_explicitly_absent(self):
        for name in m.CASES:
            for key in m.TRACE:
                row=self.sample(name);row['witness'][key]=0 if row['witness'][key] else 100
                with self.subTest(name=name,key=key),self.assertRaises(ValueError):m.validate(json.dumps(row).encode(),name,0)
    def test_wrong_order_is_rejected(self):
        for name in m.CASES:
            row=self.sample(name);row['witness']['saved']=row['witness']['returned']
            with self.assertRaises(ValueError):m.validate(json.dumps(row).encode(),name,0)
    def test_economy_and_inventory_are_not_only_boolean_checks(self):
        for name in m.CASES:
            for key in ('item','catalog_index','result','pages','quantity','bp_before','bp_after','automatic_saves','manual_saves'):
                row=self.sample(name);row[key]+=1
                with self.subTest(name=name,key=key),self.assertRaises(ValueError):m.validate(json.dumps(row).encode(),name,0)
    def test_negative_routes_cannot_be_relabelled_success(self):
        for name in ('cancel-first','cancel-page','insufficient-bp','missing-ring'):
            row=self.sample(name);self.assertEqual(row['quantity'],0);self.assertEqual(row['bp_before'],row['bp_after'])
            row['result']=0
            with self.assertRaises(ValueError):m.validate(json.dumps(row).encode(),name,0)
    def test_no_capture_battle_or_release_promotion(self):
        for key in ('natural_capture_accepted','battle_connection_accepted','full_p05_acceptance','release_ready'):
            row=self.sample('eelektross');row[key]=True
            with self.assertRaises(ValueError):m.validate(json.dumps(row).encode(),'eelektross',0)
    def test_source_identity_barriers_prerequisites_and_scope(self):
        for key,value in [('rom_sha256','0'*64),('scope','other'),('host_write_barriers',6),('rtc_flash_bytes_preserved',65536),('fresh_cores',1),('map_ring_bp_claims_are_fixtures',False),('inventory_and_party_preserved',False),('claim_catalogue_rechecked',False),('physical_host',[96,5,3,24,19]),('warnings_errors',1)]:
            row=self.sample('eelektross');row[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.validate(json.dumps(row).encode(),'eelektross',0)
    def test_noninteger_duplicate_json_and_extra_fields_rejected(self):
        good=self.sample('eelektross')
        for code in (False,0.0,1,None):
            with self.assertRaises(ValueError):m.validate(json.dumps(good).encode(),'eelektross',code)
        for raw in (b'{}',b'{"a":1,"a":2}',json.dumps(good|{'extra':1}).encode(),json.dumps(good|{'total_frames':True}).encode()):
            with self.assertRaises(ValueError):m.validate(raw,'eelektross',0)
    def test_no_rom_calls_or_host_writes_after_observation_boundary(self):
        source=(ROOT/m.SOURCE).read_text();guarded=source.split('/* The only actions after this boundary are physical input and reads. */',1)[1]
        for forbidden in ('call_preserving(', 'write8(', 'write16(', 'write32(', 'set_mon_data_u32('):self.assertNotIn(forbidden,guarded)
        for required in ('g_open(c,v->action!=4U)','g_menu_check(c,v->action==0U?index:45U)','b_save(c)','b_continue(c)','memcmp(now,expected','memcmp(party,party_after'):self.assertIn(required,guarded)
        self.assertIn('g_menu_check(c,45U)',source);self.assertIn('b_position(c,96,5,24,20)',source)
if __name__=='__main__':unittest.main()
