"""旧commitと一致する3ファイルだけを更新し、受入状態は保存する。"""
from pathlib import Path
import copy
import importlib.util
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_trace_bindings as b

class BindingTests(unittest.TestCase):
    def setup_values(self):
        old={p:('old:'+p).encode() for p in b.PATHS};new={p:('new:'+p).encode() for p in b.PATHS}
        state=dict(source_bindings={p:b.task.identity(v) for p,v in old.items()},bp_npc_exchange={'accepted':True},pending_runs=[{'id':1}])
        state['source_bindings']['unchanged']={'size':1,'sha256':'fixed'}
        return state,old,new
    def test_scope_and_acceptance_are_preserved(self):
        state,old,new=self.setup_values();before=copy.deepcopy(state);out=b.refresh(state,old,new)
        self.assertEqual(state,before)
        self.assertEqual(out['bp_npc_exchange'],state['bp_npc_exchange'])
        self.assertEqual(out['pending_runs'],state['pending_runs'])
        self.assertEqual(out['source_bindings']['unchanged'],state['source_bindings']['unchanged'])
        for p in b.PATHS:self.assertEqual(out['source_bindings'][p],b.task.identity(new[p]))
    def test_unexpected_old_hash_rejected(self):
        state,old,new=self.setup_values();state['source_bindings'][b.PATHS[0]]['sha256']='wrong'
        with self.assertRaises(ValueError):b.refresh(state,old,new)
    def test_undeclared_or_missing_path_rejected(self):
        state,old,new=self.setup_values();new['extra']=b'extra'
        with self.assertRaises(ValueError):b.refresh(state,old,new)
        new.pop('extra');new.pop(b.PATHS[0])
        with self.assertRaises(ValueError):b.refresh(state,old,new)
    def test_replaying_same_patch_is_not_allowed(self):
        state,old,new=self.setup_values()
        with self.assertRaises(ValueError):b.refresh(state,old,old)
        out=b.refresh(state,old,new)
        with self.assertRaises(ValueError):b.refresh(out,old,new)
    def test_configure_preserves_trace_import_identity_and_is_idempotent(self):
        with patch.object(b.task,'FILES',b.task.FILES),patch.object(b.task,'WORKFLOW',b.task.WORKFLOW):
            original=b.task.SELF
            b.configure();first=b.task.FILES;b.configure()
            self.assertEqual(b.task.SELF,original)
            self.assertEqual(Path(b.task.__file__).resolve(),ROOT/b.task.SELF)
            self.assertEqual(b.task.FILES,first)
            for path in (b.SELF,b.TEST,b.WORKFLOW,original):self.assertEqual(first.count(path),1)
            spec=importlib.util.spec_from_file_location('configured_trace_regression',ROOT/b.task.SELF)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            self.assertTrue(callable(module.policy_text))
            self.assertTrue(callable(module.chained_native_source))
            self.assertEqual(module.SELF,original)

if __name__=='__main__':unittest.main()
