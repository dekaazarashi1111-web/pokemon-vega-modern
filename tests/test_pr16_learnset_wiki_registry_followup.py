"""新registry adapterのidentity境界。旧Wiki/原本/native試験なし。"""
import copy
import unittest
from scripts.pr16_learnset_wiki_registry_followup import normalize


class RegistryTests(unittest.TestCase):
    def setUp(self):self.rows=[{'id':0,'key':'A','name':'空'},{'id':1,'key':'B','name':'追加フォーム'}]
    def test_preserves_display_and_identity(self):
        actual=normalize(self.rows,'species_key',2)
        self.assertEqual(actual[1]['species_key'],'B');self.assertEqual(actual[1]['display_name'],'追加フォーム')
    def test_duplicate_id_rejected(self):
        self.rows[1]['id']=0
        with self.assertRaises(ValueError):normalize(self.rows,'species_key',2)
    def test_missing_id_rejected(self):
        with self.assertRaises(ValueError):normalize(self.rows,'species_key',3)
    def test_empty_key_rejected(self):
        self.rows[0]['key']=''
        with self.assertRaises(ValueError):normalize(self.rows,'species_key',2)
    def test_duplicate_key_rejected(self):
        self.rows[1]['key']='A'
        with self.assertRaises(ValueError):normalize(self.rows,'species_key',2)
    def test_boolean_id_rejected(self):
        self.rows[0]['id']=False
        with self.assertRaises(ValueError):normalize(self.rows,'species_key',2)
    def test_missing_name_rejected(self):
        self.rows[0].pop('name')
        with self.assertRaises(ValueError):normalize(self.rows,'species_key',2)
    def test_source_is_not_mutated(self):
        self.rows[1]['details']={'condition':['a']};prior=copy.deepcopy(self.rows)
        output=normalize(self.rows,'species_key',2);output[1]['details']['condition'].append('b')
        self.assertEqual(self.rows,prior)


if __name__=='__main__':unittest.main()
