import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_integrated_domains as m
class IntegratedDomainBinding(unittest.TestCase):
    def test_seven_contracts_and_preimages_are_not_weakened(self):
        old=m.prior.derived_config();new=m.derived_config()
        for key in ('domains','runtime_candidate','latest_rom_preimages','orchestrator'):
            self.assertEqual(old[key],new[key],key)
        self.assertEqual(new['final_integration']['parent_p03_contract'],old['p03_contract'])
        self.assertEqual(new['p03_contract'],m.candidate_p03_contract(old['p03_contract']))
        restored=json.loads(json.dumps(new['p03_contract']))
        for key,(before,after) in (m.P03_RELOCATIONS|m.P03_CONSUMER_DELTAS).items():
            self.assertEqual(restored['arguments'][key],after)
            restored['arguments'][key]=before
        self.assertEqual(restored,old['p03_contract'])
        self.assertEqual(len(new['domains']),7)
        self.assertNotEqual(new['execution']['state_root'],old['execution']['state_root'])
    def test_new_candidate_is_separate_from_preserved_parent(self):
        c=m.derived_config()['final_integration']
        self.assertEqual(c['rom']['sha256'],m.native.ROM_SHA)
        self.assertEqual(c['parent_stage84']['rom']['sha256'],m.prior.SHA)
        self.assertFalse(c['release_ready'])
        self.assertIn(m.SELF,c['sources'])
    def test_historical_engine_sources_are_fixed(self):
        parent=m.prior.parent_adapter()
        for path,sha in parent.PINS.items():self.assertEqual(m.prior.identity(path)['sha256'],sha)
if __name__=='__main__':unittest.main()
