"""旧commitと一致する3ファイルだけを更新し、受入状態は保存する。"""
from pathlib import Path
import copy
import sys
import unittest
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

if __name__=='__main__':unittest.main()
