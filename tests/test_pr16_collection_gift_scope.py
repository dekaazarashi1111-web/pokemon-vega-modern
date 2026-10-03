"""追加scopeだけ検証。22旧unitやnativeを呼び直さない。"""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_collection_gift_scope as s
from tests.test_pr16_collection_gifts import model


def inputs():
    m=model();m['forms'][11]['target_species']=1281
    rows={i:[(33,1)] for i in range(1,19) if i!=12};pp={33:35}
    index=[dict(consumer='level_up',species_id=i,species_key='TEST',status='PAYLOAD_PREPARED_NOT_INSTALLED',payload={}) for i in rows]
    index.append(dict(consumer='level_up',species_id=1281,species_key='SPECIES_KEY_PICHU_SPIKY',status='IDENTITY_ONLY_NO_REPLACEMENT',payload=None,
        identity=dict(automatic_fallback=False,policy=s.POLICY,preserve_current_moves=True,preserve_identity=True,species_id=1281,species_key='SPECIES_KEY_PICHU_SPIKY')))
    return m,rows,pp,index


class GiftScopeTests(unittest.TestCase):
    def test_seventeen_and_one_not_accepted(self):
        cases,excluded=s.split_cases(*inputs());self.assertEqual(len(cases),17);self.assertEqual(sum(c['is_egg'] for c in cases),15)
        self.assertEqual([c['gift_index'] for c in cases[:2]],[5,17]);self.assertEqual(excluded[0]['species'],1281)
        self.assertEqual(excluded[0]['status'],'NOT_ACCEPTED_IDENTITY_ONLY_NO_AUTOFILL')
    def test_known_identity_policy_is_required(self):
        args=inputs();args[-1][-1]['identity']['policy']='UNKNOWN'
        with self.assertRaises(ValueError):s.split_cases(*args)
    def test_automatic_fallback_is_rejected(self):
        args=inputs();args[-1][-1]['identity']['automatic_fallback']=True
        with self.assertRaises(ValueError):s.split_cases(*args)
    def test_fake_pichu_moves_are_rejected(self):
        args=inputs();args[1][1281]=[(33,1)]
        with self.assertRaises(ValueError):s.split_cases(*args)
    def test_empty_learning_moves_are_rejected(self):
        args=inputs();args[1][1]=[]
        with self.assertRaises(ValueError):s.split_cases(*args)
    def test_other_missing_owner_not_blanket_excluded(self):
        args=inputs();del args[1][1]
        with self.assertRaises(ValueError):s.split_cases(*args)
    def test_no_exclusion_requires_review(self):
        args=inputs();args[0]['forms'][11]['target_species']=12
        with self.assertRaises(ValueError):s.split_cases(*args)
    def test_duplicate_source_or_gift_rejected(self):
        a=inputs();a[-1].append(deepcopy(a[-1][0]))
        with self.assertRaises(ValueError):s.split_cases(*a)
        a=inputs();a[0]['forms'][1]['target_species']=1
        with self.assertRaises(ValueError):s.split_cases(*a)
    def test_identity_cannot_be_research_egg(self):
        a=inputs();a[0]['gifts'][11]['kind']='RESEARCH_EGG'
        with self.assertRaises(ValueError):s.split_cases(*a)


if __name__=='__main__':unittest.main()
