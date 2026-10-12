"""特殊野生通常UI準備の境界。旧受入unit/nativeは呼ばない。"""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
SPEC = importlib.util.spec_from_file_location('gameplay', Path(__file__).resolve().parents[1]/'scripts/pr16_special_wild_gameplay.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class GameplayPreparationTests(unittest.TestCase):
    def test_initial_scope_is_not_gameplay(self):
        m.no_promotion(m.initial_verification('a'*40, 1))

    def test_false_must_be_boolean(self):
        v = m.initial_verification('a'*40, 1)
        v['gameplay_accepted'] = 0
        with self.assertRaises(ValueError): m.no_promotion(v)

    def test_each_promotion_is_rejected(self):
        for key in ('gameplay_accepted', 'capture_save_continue_accepted', 'release_ready', 'issue19_complete', 'active_baseline_changed'):
            with self.subTest(key=key):
                v = m.initial_verification('a'*40, 1); v[key] = True
                with self.assertRaises(ValueError): m.no_promotion(v)

    def test_each_old_rerun_is_rejected(self):
        for key in ('native_processes', 'arm_compiles', 'accepted_case_reruns', 'rom_semantic_changes'):
            with self.subTest(key=key):
                v = m.initial_verification('a'*40, 1); v[key] = 1
                with self.assertRaises(ValueError): m.no_promotion(v)

    def test_boolean_counter_is_rejected(self):
        v = m.initial_verification('a'*40, 1); v['native_processes'] = False
        with self.assertRaises(ValueError): m.no_promotion(v)

    def recipe(self):
        parent = bytearray(256)
        offsets = [(32, 'fff767ff'), (96, 'fff753ff')]
        for off, value in offsets: parent[off:off+4] = bytes.fromhex(value)
        parent = bytes(parent); result = bytearray(parent)
        patches = []
        for off, value in offsets:
            patches.append({'offset': off, 'before': value, 'after': 'c046c046', 'surrounding': m.identity(parent[off-14:off+18])})
            result[off:off+4] = bytes.fromhex('c046c046')
        r = {'parent': m.identity(parent), 'candidate': m.identity(bytes(result)), 'patches': patches,
             'arm_compiles': 0, 'outside_declared_changes': 0, 'changed_bytes': 8, 'rollback_verified': True,
             'land_adapter_changed': False, 'shared_initializer_changed': False}
        return parent, bytes(result), offsets, r

    def run_recipe(self, mutation=None, parent_mutation=False):
        parent, result, offsets, r = self.recipe(); expected = copy.deepcopy(r)
        if mutation: mutation(r)
        if parent_mutation: parent = b'X'+parent[1:]
        with patch.object(m, 'PARENT', expected['parent']), patch.object(m, 'CANDIDATE', expected['candidate']), patch.object(m, 'PATCHES', offsets):
            return m.replay(parent, r), result

    def test_saved_recipe_exact_replay(self):
        actual, expected = self.run_recipe(); self.assertEqual(actual, expected)

    def test_parent_mismatch(self):
        with self.assertRaises(ValueError): self.run_recipe(parent_mutation=True)

    def test_third_patch_rejected(self):
        with self.assertRaises(ValueError): self.run_recipe(lambda r: r['patches'].append(copy.deepcopy(r['patches'][0])))

    def test_reordered_patches_rejected(self):
        with self.assertRaises(ValueError): self.run_recipe(lambda r: r['patches'].reverse())

    def test_modified_postimage_rejected(self):
        with self.assertRaises(ValueError): self.run_recipe(lambda r: r['patches'][0].update(after='00000000'))

    def test_context_mismatch_rejected(self):
        with self.assertRaises(ValueError): self.run_recipe(lambda r: r['patches'][0].update(surrounding={'size':32,'sha256':'0'*64}))

    def test_candidate_mismatch_rejected(self):
        with self.assertRaises(ValueError): self.run_recipe(lambda r: r.update(candidate={'size':256,'sha256':'0'*64}))

    def test_scope_mutation_rejected(self):
        with self.assertRaises(ValueError): self.run_recipe(lambda r: r.update(shared_initializer_changed=True))

    def rows(self):
        return 'item_key,id,pocket,name_ja\nITEM_KEY_SUPER_ROD,264,POCKET_KEY_ITEMS,すごいつりざお\nITEM_KEY_SCANNER,900,POCKET_KEY_ITEMS,スキャナー\n'

    def test_manifest_ids_are_resolved(self):
        self.assertEqual(m.item_rows(self.rows())['hidden']['id'], '900')

    def test_missing_item_rejected(self):
        with self.assertRaises(ValueError): m.item_rows(self.rows().split('ITEM_KEY_SCANNER')[0])

    def test_duplicate_item_rejected(self):
        with self.assertRaises(ValueError): m.item_rows(self.rows()+self.rows().splitlines()[-1]+'\n')

    def test_wrong_pocket_rejected(self):
        with self.assertRaises(ValueError): m.item_rows(self.rows().replace('POCKET_KEY_ITEMS', 'POCKET_ITEMS'))

    def test_japanese_scanner_binding_is_unique(self):
        self.assertEqual(m.item_rows(self.rows().replace('ITEM_KEY_SCANNER', 'ITEM_KEY_VEGA_SCANNER'))['hidden']['id'], '900')


if __name__ == '__main__': unittest.main()
