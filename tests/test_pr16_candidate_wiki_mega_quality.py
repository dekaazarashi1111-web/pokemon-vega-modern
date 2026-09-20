"""旧self-referenceを真のメガとして受入せず、不一致は可視化する。"""
from pathlib import Path
import sys
import unittest
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from pr16_candidate_wiki_mega_quality import partition,normalize


class MegaQualityTest(unittest.TestCase):
    def row(self,base=1,target=2,reverse=True,scope='LEGACY'):
        return dict(base_species_id=base,mega_species_id=target,reverse_verified=reverse,
                    mapping_scope=scope,item_id=10,item_key='ITEM_KEY_FIXTURE')

    def test_positive_forward_reverse_only(self):
        good,bad=partition([self.row()]);self.assertEqual(len(good),1);self.assertEqual(bad,[])

    def test_self_reference_is_not_a_mega_form(self):
        good,bad=partition([self.row(target=1,reverse=False)])
        self.assertEqual(good,[]);self.assertFalse(bad[0]['is_accepted_mega_form'])
        self.assertEqual(bad[0]['consumer_behavior'],'DEFERRED_AUDIT')

    def test_unknown_mapping_failure_is_not_hidden(self):
        for row in [self.row(reverse=False),self.row(target=1),self.row(target=1,reverse=False,scope='P04_ADDED')]:
            with self.assertRaises(ValueError):partition([row])

    def test_normal_species_is_not_reclassified_as_mega(self):
        model={'megas':[self.row(target=1,reverse=False)],'species':[
            {'id':1,'form_status':'MEGA_BATTLE_ONLY','classification':'OFFICIAL','mega_forms':[1,1]}]}
        result=normalize(model);species=result['species'][0]
        self.assertEqual(species['form_status'],'OFFICIAL');self.assertEqual(species['mega_forms'],[])
        self.assertEqual(result['mega_mapping_summary']['raw_rows'],1)
        self.assertEqual(result['mega_mapping_summary']['forward_reverse_verified'],0)
        self.assertEqual(len(species['mega_mapping_anomalies']),1)


if __name__=='__main__':unittest.main()
