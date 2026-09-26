"""New save/load-delegate regression guards; no emulator/old acceptance runs."""
import hashlib
import json
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_research_save_delegate as m


class SaveDelegateTests(unittest.TestCase):
    def fixture(self):
        raw=bytearray(range(128));raw[64:68]=m.BEFORE;raw=bytes(raw)
        fixed=bytearray(raw);fixed[64:68]=m.AFTER
        return raw,bytes(fixed)

    def run_repair(self, mutation=None, candidate_bad=False, context_bad=False, target_bad=False):
        raw,fixed=self.fixture()
        constants={'PARENT':m.identity(raw),'CANDIDATE':m.identity(fixed),'OFFSET':64,
                   'CONTEXT_SHA':hashlib.sha256(raw[48:84]).hexdigest(),
                   'TARGETS':[(0,16,hashlib.sha256(raw[:16]).hexdigest())]}
        if candidate_bad:constants['CANDIDATE']['sha256']='0'*64
        if context_bad:constants['CONTEXT_SHA']='0'*64
        if target_bad:constants['TARGETS'][0]=(0,16,'0'*64)
        if mutation:raw=mutation(raw)
        with patch.multiple(m,**constants):return m.apply(raw),fixed

    def test_exact_save_delegate_repair_and_rollback(self):
        (actual,recipe),expected=self.run_repair()
        self.assertEqual(actual,expected);self.assertEqual(recipe['changed_bytes'],1)
        self.assertTrue(recipe['rollback_verified']);self.assertEqual(recipe['arm_compiles'],0)
    def test_wrong_parent(self):
        with self.assertRaises(ValueError):self.run_repair(lambda x:b'Z'+x[1:])
    def test_wrong_output(self):
        with self.assertRaises(ValueError):self.run_repair(candidate_bad=True)
    def test_wrong_context(self):
        with self.assertRaises(ValueError):self.run_repair(context_bad=True)
    def test_wrong_delegate_body(self):
        with self.assertRaises(ValueError):self.run_repair(target_bad=True)
    def test_already_fixed_parent_refused(self):
        raw,fixed=self.fixture()
        with self.assertRaises(ValueError):m.apply(fixed)
    def config(self):return b'{"delegates": {"qol_save": "0x09377695", "other": "keep"}, "flags": []}\n'
    def blob(self,raw):return hashlib.sha1(('blob '+str(len(raw))+'\0').encode()+raw).hexdigest()
    def test_config_one_field_only(self):
        raw=self.config()
        with patch.object(m,'CONFIG_BLOB',self.blob(raw)):out=m.correct_config(raw)
        a=json.loads(raw);b=json.loads(out);a['delegates']['qol_save']='0x09377661'
        self.assertEqual(a,b);self.assertEqual(out,raw.replace(b'0x09377695',b'0x09377661'))
    def test_config_input_hash(self):
        with self.assertRaises(ValueError):m.correct_config(self.config())
    def test_config_missing_literal(self):
        raw=self.config().replace(b'0x09377695',b'0x09377661')
        with patch.object(m,'CONFIG_BLOB',self.blob(raw)),self.assertRaises(ValueError):m.correct_config(raw)
    def test_duplicate_config_literal(self):
        raw=self.config().replace(b'"flags": []',b'"flags": {"qol_save": "0x09377695"}')
        with patch.object(m,'CONFIG_BLOB',self.blob(raw)),self.assertRaises(ValueError):m.correct_config(raw)
