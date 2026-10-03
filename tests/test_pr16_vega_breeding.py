import copy
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import pr16_vega_breeding as b

SOURCE = Path(os.environ.get('PR16_VEGA_BREEDING_SOURCE',str(ROOT/b.SOURCE)))


class BreedingTests(unittest.TestCase):
    def test_all_rows_complete_without_direct_or_shared_duplication(self):
        result = b.build(ROOT,SOURCE)
        rows = [json.loads(x) for x in result['nondirect_egg.jsonl'].splitlines()]
        self.assertEqual(len(rows),2394)
        self.assertEqual(len({r['row_key'] for r in rows}),2394)
        self.assertEqual(len({r['species_id'] for r in rows}),92)
        self.assertTrue(all(not r['adopt_as_receiver_direct_egg'] and not r['add_as_shared_egg'] for r in rows))
        original = b.a.load(ROOT/b.a.EVIDENCE/'wiki_nondirect_egg.json')
        self.assertEqual([r['original_wiki_row'] for r in rows],[r for g in original for r in g['wiki_rows']])
        self.assertEqual(json.loads(result['breeding_families.json'])['summary']['note_scopes'],
                         {'HATCH_BASE_REFERENCE':2336,'SAME_FAMILY_INTERMEDIATE_REFERENCE':57,'NO_BREEDING_NOTE':1})

    def test_graph_matches_independent_original_scan_all_species(self):
        source, table = b.read_source(SOURCE)
        reverse = b.reverse_edges(source['evolution']['rows'])
        self.assertTrue(all(b.ancestry(s,reverse)[0][-1] == b.scan_consumer(table,s) for s in range(1,412)))

    def test_first_parent_and_slot_order_is_not_last_parent(self):
        rows = [{'species_id':7,'slot':0,'target_species_id':20},
                {'species_id':2,'slot':4,'target_species_id':20},
                {'species_id':2,'slot':1,'target_species_id':20}]
        self.assertEqual(b.reverse_edges(rows)[20],rows[2])

    def test_cycle_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'cycle'):
            b.ancestry(1,{1:{'species_id':2},2:{'species_id':1}})

    def test_sixth_descent_not_silently_truncated(self):
        with self.assertRaisesRegex(ValueError,'5世代'):
            b.ancestry(7,{n:{'species_id':n-1} for n in range(2,8)})

    def test_species_outside_original_abi(self):
        for value in (0,412,-1,True):
            with self.subTest(value=value), self.assertRaises(ValueError): b.ancestry(value,{})

    def test_intermediate_wiki_recipient_not_wrong_hatch_species(self):
        species={24:{'display_name':'ピチュー'},25:{'display_name':'ピカチュウ'},27:{'display_name':'ゴリチュウ'}}
        result = b.note_scope({'breeding_notes':['親→ピカチュウ']},[27,25,24],species)
        self.assertEqual(result,('SAME_FAMILY_INTERMEDIATE_REFERENCE',[25]))

    def test_plain_species_reference_does_not_invent_arrow(self):
        result = b.note_scope({'breeding_notes':['リープン']},[2,1],{1:{'display_name':'リープン'},2:{'display_name':'リーティン'}})
        self.assertEqual(result,('HATCH_BASE_REFERENCE',[1]))

    def test_missing_wiki_note_is_explicit_not_invented(self):
        self.assertEqual(b.note_scope({'breeding_notes':[]},[1],{1:{'display_name':'リープン'}}),('NO_BREEDING_NOTE',[]))

    def test_unrelated_recipient_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'同系統外'):
            b.note_scope({'breeding_notes':['親→別系統']},[1],{1:{'display_name':'リープン'}})

    def test_source_tamper_fails_before_decode(self):
        with tempfile.TemporaryDirectory() as t:
            dest=Path(t);shutil.copytree(SOURCE,dest,dirs_exist_ok=True)
            p=dest/'original-breeding.json';p.write_bytes(p.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'source anchor'): b.read_source(dest)

    def test_receipt_rehash_or_omission_is_not_new_authority(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);p=root/b.a.EVIDENCE;p.mkdir(parents=True)
            (p/'receipt.json').write_text('{"outputs":{}}')
            with self.assertRaisesRegex(ValueError,'receipt anchor'): b.original_guard(root)

    def test_cli_check_is_pure_and_rejects_generated_drift(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.local') as t:
            out=Path(t)
            for name,raw in b.build(ROOT,SOURCE).items(): (out/name).write_bytes(raw)
            paths=[*out.iterdir(),*SOURCE.iterdir(),*(ROOT/b.a.EVIDENCE).iterdir()]
            snapshot=lambda:{str(p):(p.read_bytes(),p.stat().st_mtime_ns) for p in paths if p.is_file()}
            before=snapshot()
            cmd=[sys.executable,'-B',str(ROOT/'tools/pr16_vega_breeding.py'),'check','--source',str(SOURCE),'--output',str(out)]
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,0)
            self.assertEqual(before,snapshot())
            (out/'nondirect_egg.jsonl').write_bytes(b'{}\n')
            self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)


if __name__ == '__main__': unittest.main()
