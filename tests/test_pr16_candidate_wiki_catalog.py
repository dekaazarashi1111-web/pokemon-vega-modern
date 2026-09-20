"""Wiki限定unit/integration。ROM生成やnative実行は行わない。"""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
import struct
import sys
import unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from pr16_candidate_wiki_inputs import Inputs, BASE, Rom, digest, selected_candidate, registries
from pr16_candidate_wiki_catalog import indexed, history_rows, normal_learnset, old_routes, SUPPLY_UNKNOWN
from pr16_candidate_wiki_render import cell, tree_hash, validate_links


class CandidateWikiCatalogUnitTests(unittest.TestCase):
    def test_duplicate_missing_ids_and_keys(self):
        row={'id':0,'key':'A'}
        for rows in [[row,row],[dict(row,id=1)],[row,dict(row,id=1)]]:
            with self.assertRaises(ValueError):indexed(rows,'fixture')

    def test_history_parameters_not_just_move_presence(self):
        source={'species_id':0,'species_key':'S','move_id':1,'move_key':'M','route':'level_up','source_parameters':{'level':'5'}}
        histories={'groups':{'fixture':[source,source]}}
        learns={0:{'routes':[{'move_id':1,'route':'level_up','level':6},{'move_id':1,'route':'build_learnable_preservation'}]}}
        rows=history_rows(histories,learns)
        self.assertEqual(len(rows),2)
        self.assertTrue(rows[0]['same_move_present']);self.assertTrue(rows[0]['original_route_present'])
        self.assertFalse(rows[0]['original_parameters_present']);self.assertTrue(rows[0]['preservation_history_present'])
        self.assertEqual(rows[0]['current_teaching_routes'],['level_up'])

    def test_multiset_preserves_duplicates_and_excludes_history(self):
        rows=[{'route':'egg','move_id':1},{'route':'egg','move_id':1},{'route':'build_learnable_preservation','move_id':2}]
        self.assertEqual(normal_learnset(rows),Counter({('egg',1,None):2}))

    def test_old_routes_normalize_without_slot_invention(self):
        rows=old_routes({'learnsets':{'machine_runtime':[5,5],'level_up':[{'move_id':2,'level':3}]}})
        self.assertEqual(rows[0],{'route':'machine','move_id':5})
        self.assertEqual(normal_learnset(rows)[('machine',5,None)],2)

    def test_deterministic_tree_includes_paths(self):
        self.assertEqual(tree_hash({'a':b'1','b':b'2'}),tree_hash({'b':b'2','a':b'1'}))
        self.assertNotEqual(tree_hash({'a':b'1'}),tree_hash({'b':b'1'}))

    def test_markdown_escaping(self):
        self.assertEqual(cell('[a](x)|<b>\n'),'&#91;a&#93;(x)&#124;&lt;b&gt;<br>')

    def test_broken_link_and_anchor_rejected(self):
        for content in [b'[x](missing.md)',b'[x](README.md#missing)',b'[x](https://example.invalid/)']:
            with self.assertRaises(ValueError):validate_links({'README.md':content})
        self.assertEqual(validate_links({'README.md':b'<a id="yes"></a>\n[x](#yes)'}),1)

    def test_unsafe_output_path_rejected(self):
        with self.assertRaises(ValueError):validate_links({'../escape.md':b'x'})

    def test_japanese_item_abi(self):
        from pr16_candidate_wiki_details import item_fields
        raw=bytearray(50);raw[:2]=b'\x01\xff';raw[40:42]=b'\x02\xff'
        struct.pack_into('<HHBBI',raw,10,321,400,123,9,BASE+40)
        struct.pack_into('<I',raw,20,0x04010000)
        row=item_fields(Rom(bytes(raw)),BASE,{'1':'名','2':'説'})
        self.assertEqual((row['name'],row['description'],row['price'],row['hold_effect_id'],row['hold_effect_parameter']),('名','説',400,123,9))


class CandidateWikiGeneratedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate=selected_candidate(Inputs(ROOT))
        cls.root=ROOT/'docs/wiki'/('p08-candidate-'+cls.candidate['sha256'][:8])
        if not cls.root.exists():raise unittest.SkipTest('generated Wiki未作成。build後にこのintegrationを必ず実行する。')
        cls.files={p.relative_to(cls.root).as_posix():p.read_bytes() for p in sorted(cls.root.rglob('*')) if p.is_file()}
        cls.index=json.loads(cls.files['data/index.json'])
        cls.data={k:[json.loads(line) for line in cls.files['data/'+k+'.jsonl'].splitlines()] for k in ('species','moves','abilities','items','hidden_abilities','learnsets','megas','z_moves','p07_history')}

    def test_candidate_and_dynamic_counts(self):
        self.assertEqual(self.index['candidate'],self.candidate)
        ids=registries(Inputs(ROOT))
        for domain,plural in [('species','species'),('move','moves'),('ability','abilities'),('item','items')]:
            self.assertEqual(len(self.data[plural]),len(ids[domain]));self.assertEqual(self.index['counts'][domain],len(ids[domain]))

    def test_all_individual_pages_and_indexes(self):
        for domain,folder,index in [('species','pokemon','POKEMON_INDEX'),('moves','moves','MOVE_INDEX'),('abilities','abilities','ABILITY_INDEX'),('items','items','ITEM_INDEX')]:
            self.assertEqual(sum(name.startswith(folder+'/') and name.endswith('.md') for name in self.files),len(self.data[domain]))
            text=self.files[index+'.md'].decode()
            for row in self.data[domain]:
                self.assertIn(f'{folder}/{row["id"]}.md',text);self.assertIn(row['key'],text)

    def test_all_manifest_hashes_and_links(self):
        manifest=self.index['files'];self.assertEqual(set(manifest),set(self.files)-{'data/index.json'})
        for name,meta in manifest.items():self.assertEqual(meta,{'size':len(self.files[name]),'sha256':digest(self.files[name])})
        self.assertEqual(self.index['payload_tree_sha256'],tree_hash({k:v for k,v in self.files.items() if k!='data/index.json'}))
        self.assertGreater(validate_links(self.files),len(self.data['species']))

    def test_source_bindings_current(self):
        inputs=Inputs(ROOT)
        for name,meta in self.index['source_bindings'].items():
            raw=inputs.raw(name);self.assertEqual(meta,{'size':len(raw),'sha256':digest(raw)},name)

    def test_mega_forward_reverse_and_native_scope(self):
        for row in self.data['megas']:
            self.assertTrue(row['reverse_verified']);self.assertEqual(self.data['items'][row['item_id']]['key'],row['item_key'])
            self.assertEqual(self.data['species'][row['mega_species_id']]['key'],row['mega_species_key'])
            for kind in ('front','back','icon','palette','shiny_palette'):self.assertIn(kind,row['assets'])
        self.assertTrue(any(r['native_status']=='IMPLEMENTED_NOT_NATIVE_ACCEPTED' for r in self.data['megas']))

    def test_z_mapping_eevee_and_mimikyu_not_name_search(self):
        zs=self.data['z_moves']
        self.assertTrue(any(r['species_key']=='SPECIES_KEY_EEVEE' and r['z_move_key']=='MOVE_KEY_EXTREME_EVOBOOST' for r in zs))
        self.assertTrue(any('MIMIKYU_BUSTED' in r['species_key'] for r in zs))
        for r in zs:
            self.assertTrue(r['mapping_proof']['matches'])
            self.assertEqual(self.data['moves'][r['base_move_id']]['key'],r['base_move_key'])
            self.assertEqual(self.data['moves'][r['z_move_id']]['key'],r['z_move_key'])
            self.assertNotEqual(r['native_e2e'],'NATIVE_ACCEPTED')

    def test_hidden_slot_is_not_supply(self):
        for row in self.data['hidden_abilities']:
            self.assertEqual(row['assigned'],bool(row['ability_id']));self.assertEqual(row['slot_evidence'],'EXACT_CANDIDATE_ROM')
            if row['assigned']:self.assertIn(row['first_supply'],(SUPPLY_UNKNOWN,'GENERATED_CANONICAL','INHERITED_ACCEPTED'))
        text=self.files['HIDDEN_ABILITY_INDEX.md'].decode();self.assertIn('夢特性未設定',text);self.assertIn('初回供給記録未発見',text)

    def test_p07_original_rows_complete(self):
        source=json.loads((ROOT/'content/modernization/pr16_candidate_wiki_p07_source_rows.json').read_bytes())
        expected=Counter({k:len(v) for k,v in source['groups'].items() if v})
        self.assertEqual(Counter(r['group'] for r in self.data['p07_history']),expected)
        self.assertTrue(all(r['same_move_present'] for r in self.data['p07_history']))

    def test_text_only_and_no_generation_clock(self):
        for name,raw in self.files.items():
            self.assertTrue(name.endswith(('.md','.json','.jsonl')));self.assertNotIn(b'\0',raw);raw.decode('utf-8')
            for forbidden in (b'/home/runner/',b'/mnt/data/',b'GITHUB_TOKEN=',b'generated_at',b'github_pat_'):
                self.assertNotIn(forbidden,raw,name)


if __name__=='__main__':unittest.main()
