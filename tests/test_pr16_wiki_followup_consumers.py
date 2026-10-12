"""Issue18 consumer結合の差分試験。保存済みtext以外の候補生成・nativeを呼ばない。"""
from __future__ import annotations
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from pr16_candidate_wiki_inputs import Inputs
from pr16_candidate_wiki_consumers import Source, generic_z, hidden_supply, load, z_effects
from pr16_wiki_source_snapshot import OUTPUT, function_unit, defines, mask_c
from pr16_wiki_followup_sources import unpack


class ConsumerSourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads((ROOT / OUTPUT).read_text())
        data = ROOT / 'docs/wiki/p08-candidate-46487d98/data'
        cls.base = {name: [json.loads(x) for x in (data / (name + '.jsonl')).read_text().splitlines()]
                    for name in ('moves', 'items', 'species', 'z_moves')}

    def source(self):
        return Source(copy.deepcopy(self.snapshot))

    def model(self):
        return copy.deepcopy(self.base)

    def test_current_local_bindings_and_units(self):
        source = load(Inputs(ROOT))
        self.assertEqual(source.number('Z_EFFECT_CURSE'), 5)

    def test_function_extraction_ignores_comments_literals_and_prototype(self):
        text = 'void f(void);\n// f() { }\nvoid f(void) { char *s="}"; /* } */ if (1) { x(); } }\n'
        unit = function_unit(text, 'f')
        self.assertEqual((unit['start_line'], unit['end_line']), (3, 3))
        self.assertIn('x();', unit['text'])

    def test_ambiguous_missing_and_unclosed_function_rejected(self):
        for text in ('void f() {}\nvoid f() {}', 'void g() {}', 'void f() {'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                function_unit(text, 'f')

    def test_mask_preserves_offsets_and_newlines(self):
        text = '/*{\n}*/\n"x\\\"}"\n\'{\''
        masked = mask_c(text)
        self.assertEqual(len(masked), len(text))
        self.assertEqual(masked.count('\n'), text.count('\n'))
        self.assertNotIn('{', masked)

    def test_commented_defines_are_not_enabled(self):
        rows = defines('// #define A 9\n/* #define A 8 */\n#define A 7 // active\n', ('A',))
        self.assertEqual(rows, [{'symbol': 'A', 'expression': '7', 'line': 3}])

    def test_changed_unit_hash_rejected(self):
        data = copy.deepcopy(self.snapshot)
        data['sources']['src/set_z_effect.c']['units'][0]['text'] += '// changed'
        with self.assertRaises(ValueError):
            Source(data)

    def test_define_cycle_code_and_unknown_rejected(self):
        for definitions in ({'A': 'B', 'B': 'A'}, {'A': '__import__("os")'}, {}):
            source = self.source(); source.symbols = definitions
            with self.assertRaises(ValueError):
                source.number('A')

    def test_candidate_id_remapping_is_not_upstream_id(self):
        result = generic_z(self.model(), self.source())
        row = next(r for r in result['generic_z_type_mappings'] if r['type_id'] == 0 and r['category_id'] == 0)
        self.assertEqual(row['move_key'], 'MOVE_KEY_BREAKNECK_BLITZ_P')
        self.assertEqual(row['upstream_move_id_not_candidate_id'], 767)
        self.assertEqual(row['move_id'], 838)

    def test_exact_type_split_grid(self):
        result = generic_z(self.model(), self.source())
        rows = result['generic_z_type_mappings']
        self.assertEqual(len(rows), 36)
        self.assertEqual(len({(r['type_id'], r['category_id']) for r in rows}), 36)
        self.assertNotIn(9, {r['type_id'] for r in rows})

    def test_changed_target_category_and_id_fail_closed(self):
        for field, value in [('category_id', 2), ('id', 9000)]:
            model = self.model()
            next(r for r in model['moves'] if r['key'] == 'MOVE_KEY_BREAKNECK_BLITZ_P')[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                generic_z(model, self.source())

    def test_special_crystals_not_generic_fallback(self):
        model = self.model(); result = generic_z(model, self.source())
        special = {r['item_id'] for r in model['z_moves']}
        self.assertFalse(special & {i for r in result['generic_z_type_mappings'] for i in r['crystal_item_ids']})

    def test_status_sentinel_and_retained_base_move(self):
        result = generic_z(self.model(), self.source())
        rows = [r for r in result['records'] if r['status'] == 'STATUS_MOVE_WITH_ADDITIONAL_EFFECT']
        self.assertTrue(rows)
        self.assertTrue(all(r['return_sentinel'] == '0xFFFF' and r['base_move_retained'] and not r['targets'] for r in rows))

    def test_max_shared_field_not_mislabelled_z_status_effect(self):
        result = generic_z(self.model(), self.source())
        rows = [r for r in result['records'] if r['shared_effect_field'] > 28]
        self.assertTrue(rows)
        self.assertTrue(all(r['status'] == 'INTERNAL_Z_MAX_ROW_NOT_ORDINARY_BASE_MOVE' and r['status_effect'] is None for r in rows))

    def test_none_not_a_base_move(self):
        row = generic_z(self.model(), self.source())['records'][0]
        self.assertEqual(row['status'], 'MOVE_NONE_NOT_A_BASE_MOVE')
        self.assertFalse(row['targets'])

    def test_dynamic_type_moves_are_explicit(self):
        rows = generic_z(self.model(), self.source())['records']
        keys = {r['move_key'] for r in rows if r.get('dynamic_type')}
        self.assertEqual(keys, {'MOVE_KEY_WEATHERBALL', 'MOVE_KEY_AURAWHEEL', 'MOVE_KEY_TERRAINPULSE'})

    def test_status_effects_cover_29_only_and_curse_branches(self):
        rows = z_effects(self.source())
        self.assertEqual([r['id'] for r in rows], list(range(29)))
        self.assertIn('ゴースト', rows[5]['description_ja'])
        self.assertIn('命中・回避を除く', rows[2]['description_ja'])

    def test_inheritance_is_not_first_supply(self):
        model = self.model(); before = [r['hidden_ability']['first_supply'] for r in model['species']]
        rules = hidden_supply(model, self.source())
        self.assertEqual(rules['breeding']['percent'], 60)
        self.assertFalse(rules['breeding']['is_first_supply'])
        self.assertEqual(before, [r['hidden_ability']['first_supply'] for r in model['species']])
        self.assertTrue(rules['dexnav']['requires_previously_caught'])

    def test_no_native_acceptance_promotion(self):
        result = generic_z(self.model(), self.source())
        self.assertTrue(all(r['candidate_native_acceptance'] == 'DEFERRED_AUDIT' for r in result['records']))

    def test_repeat_projection_is_deterministic(self):
        self.assertEqual(generic_z(self.model(), self.source()), generic_z(self.model(), self.source()))

    def test_artifact_path_traversal_and_binary_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            for name, content in [('../bad.c', b'x'), ('/bad.c', b'x'), ('bad.gba', b'x'), ('bad.c', b'\0')]:
                raw = io.BytesIO()
                with zipfile.ZipFile(raw, 'w') as archive:
                    archive.writestr(name, content)
                with self.subTest(name=name), self.assertRaises(ValueError):
                    unpack(raw.getvalue(), Path(temp))

if __name__ == '__main__':
    unittest.main()
