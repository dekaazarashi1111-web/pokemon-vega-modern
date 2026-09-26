"""script labelを持たない配布metadataと実拒否edgeの結合。"""
import unittest
from test_pr16_circus_entry import entry,node


class CancelOwnerContracts(unittest.TestCase):
    def binding(self):
        address=entry.BASE+0x1000;abort=entry.BASE+0x501;commit=entry.BASE+0x601
        nodes=[node(address,[entry.call(commit),entry.goto(address+0x100)]),
               node(address+0x100,[entry.call(abort),b'\x02'])]
        nodes[0]['instructions'][0]['native']=commit
        nodes[1]['instructions'][0]['native']=abort
        return nodes,dict(entrypoints=dict(FacilityRuntime_Abort=abort,FacilityRuntime_CommitSelection=commit))
    def test_metadata_without_script_symbol_names(self):
        nodes,meta=self.binding();self.assertEqual(entry.cancel_address(nodes,meta),entry.BASE+0x1100)
    def test_reject_missing_commit(self):
        nodes,meta=self.binding()
        with self.assertRaises(ValueError):entry.cancel_address(nodes[1:],meta)
    def test_reject_duplicate_commit(self):
        nodes,meta=self.binding()
        with self.assertRaises(ValueError):entry.cancel_address(nodes+[nodes[0]],meta)
    def test_reject_unowned_cancel(self):
        nodes,meta=self.binding();nodes[1]['instructions'][0]['native']+=2
        with self.assertRaises(ValueError):entry.cancel_address(nodes,meta)
    def test_reject_missing_cancel_target(self):
        nodes,meta=self.binding()
        with self.assertRaises(ValueError):entry.cancel_address(nodes[:1],meta)

