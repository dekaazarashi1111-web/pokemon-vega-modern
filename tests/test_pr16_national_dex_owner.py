"""Synthetic static route mutations; never starts a game or grants flags."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_national_dex_owner as m

def valid():
    return dict(town_condition=[0x4072,9,0x8853824],lab_condition=[0x4072,10,0x88538b0],legacy_condition=[0x4055,7,0x817c61d],
        special367=0x806da21,special403=0x806da51,town_set=[0x885387c,0x4072,10],town_warp=[0x8853884,4,3],
        lab_set=[0x8853a5d,0x4072,11],lab_grant=[0x8853a68,367],lab_warp=[0x8853a6b,30,0],legacy_grant=[0x817c740,367],
        graph_diagnostics=0,visited_nodes=20)

class OwnerTests(unittest.TestCase):
    def test_scope_not_gameplay(self):
        result=m.check_routes(valid())
        self.assertEqual(result['status'],'PASS_NATIONAL_DEX_GRANT_OWNER_SCOPED')
        for key in ('early_unlock_reachable_accepted','var9_natural_arrival_accepted','dex_enabled_in_save','evolution_accepted','gate_modified','full_map_inventory_acceptance_claimed','release_ready'):
            self.assertFalse(result[key])
    def test_other_rom(self):
        with self.assertRaises(ValueError):m.audit(b'not the story ROM')

MUTATIONS={
 'wrong_town_condition':('town_condition',[0x4072,0,0x8853824]),
 'wrong_lab_condition':('lab_condition',[0x4072,9,0x88538b0]),
 'legacy_mixed_with_vega':('legacy_condition',[0x4072,7,0x817c61d]),
 'wrong_native_grant':('special367',0x806da51),
 'wrong_native_predicate':('special403',0x806da21),
 'no_town_advance':('town_set',[0x885387c,0x4072,9]),
 'wrong_town_destination':('town_warp',[0x8853884,4,0]),
 'repeat_lab_condition':('lab_set',[0x8853a5d,0x4072,10]),
 'lab_predicate_not_grant':('lab_grant',[0x8853a68,403]),
 'grant_after_warp':('lab_warp',[0x8853a5b,30,0]),
 'legacy_missing':('legacy_grant',[]),
 'decode_error':('graph_diagnostics',1),
}
for name,(key,value) in MUTATIONS.items():
    def reject(self,key=key,value=value):
        d=valid();d[key]=value
        with self.assertRaises(ValueError):m.check_routes(d)
    setattr(OwnerTests,'test_reject_'+name,reject)
if __name__=='__main__':unittest.main()
