"""固定R0の新join/表示/リンク/不変性境界。旧ROM/native受入の再走ではない。"""
import copy
import pathlib
import sys
import tempfile
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_wiki_r0_build as b


class R0(unittest.TestCase):
    def fixtures(self):
        sp=[{'key':'S0'},{'key':'S1'}];moves=[{'key':'M0'},{'key':'M1'}]
        row={'move_id':1,'species_id':1,'species_key':'S1','move_key':'M1','condition_id':'c','consumer':'level_up','conditional_egg':False,'meaning':'BASELINE_DATA_NOT_PHYSICAL_SUPPLY_ACCEPTANCE','physical_supply_verified':False,'source_id':'source:1','source_row_sha256':'a'*64}
        return row,sp,moves,{'c':{}}
    def rejected(self,**changes):
        row,sp,moves,c=self.fixtures();row.update(changes)
        with self.assertRaises(ValueError):b.route_validate(row,1,sp,moves,c)
    def test_valid_route(self):
        row,sp,moves,c=self.fixtures();self.assertEqual(b.route_validate(row,1,sp,moves,c),('level_up',1))
    def test_wrong_owner(self):self.rejected(species_id=0)
    def test_wrong_species_key(self):self.rejected(species_key='OTHER')
    def test_wrong_move_key(self):self.rejected(move_key='OTHER')
    def test_missing_condition(self):self.rejected(condition_id='missing')
    def test_unknown_consumer(self):self.rejected(consumer='unknown')
    def test_invalid_move(self):self.rejected(move_id=0)
    def test_boolean_move(self):self.rejected(move_id=True)
    def test_out_of_range_move(self):self.rejected(move_id=2)
    def test_physical_escalation(self):self.rejected(physical_supply_verified=True)
    def test_missing_origin(self):self.rejected(source_id='')
    def test_missing_hash(self):self.rejected(source_row_sha256='bad')
    def test_carry_not_direct(self):self.rejected(consumer='form_change')
    def test_conditional_not_flat(self):self.rejected(consumer='egg',conditional_egg=True)
    def test_valid_conditional(self):
        row,sp,moves,c=self.fixtures();row.update(consumer='egg',conditional_egg=True,meaning='CONDITIONAL_BREEDING_NOT_FLAT_EGG')
        self.assertEqual(b.route_validate(row,1,sp,moves,c)[0],'egg')
    def test_valid_carry(self):
        row,sp,moves,c=self.fixtures();row.update(consumer='form_change',meaning='CARRY_REFERENCE_NOT_DIRECT_GRANT')
        self.assertEqual(b.route_validate(row,1,sp,moves,c)[0],'form_change')
    def test_escaped_markdown(self):
        value=b.esc('A|[x]`\n<script>');self.assertNotIn('|',value);self.assertNotIn('[',value);self.assertNotIn('<script>',value)
    def test_json_fence_injection(self):self.assertEqual(b.block({'x':'```'}).count('```'),2)
    def test_valid_anchor(self):
        self.assertEqual(b.validate_links({'README.md':b'[a](conditions/00.md#x)','conditions/00.md':b'<a id="x"></a>'}),1)
    def test_missing_anchor(self):
        with self.assertRaises(ValueError):b.validate_links({'README.md':b'[a](x.md#x)','x.md':b'no anchor'})
    def test_missing_page(self):
        with self.assertRaises(ValueError):b.validate_links({'README.md':b'[a](missing.md)'})
    def test_external_link(self):
        with self.assertRaises(ValueError):b.validate_links({'README.md':b'[a](https://example.test/)'})
    def test_link_traversal(self):
        with self.assertRaises(ValueError):b.validate_links({'README.md':b'[a](../old.md)'})
    def test_source_code_not_link(self):
        self.assertEqual(b.validate_links({'README.md':b'```json\n{"link":"[x](https://example.test/)"}\n```'}),0)
    def test_roles_use_selected_ids(self):
        moves=[{'type_id':1,'category_id':0,'priority':1,'effect_keys':['EFFECT_HEAL']}]
        self.assertTrue(all(not v for v in b.move_roles({'types':[1]},[],moves).values()))
        self.assertEqual(b.move_roles({'types':[1]},[0],moves)['priority'],[0])
    def test_learning_identity(self):
        with self.assertRaises(ValueError):b.learning_body(b'\nstable key: M')
    def test_no_change_write_preserves_mtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);files={'README.md':b'R0'};b.write_outputs(root,files)
            before=(root/b.OUT/'README.md').stat().st_mtime_ns;b.write_outputs(root,files)
            self.assertEqual(before,(root/b.OUT/'README.md').stat().st_mtime_ns)
    def test_stale_output_not_deleted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);b.write_outputs(root,{'old.md':b'old'})
            with self.assertRaises(ValueError):b.write_outputs(root,{'new.md':b'new'})
            self.assertEqual((root/b.OUT/'old.md').read_bytes(),b'old')

    def test_item_old_alias(self):self.assertEqual(b.item_parameter({'hold_effect_parameter':0,'hold_effect_param':'0'}),0)
    def test_item_conflicting_alias(self):
        with self.assertRaises(ValueError):b.item_parameter({'hold_effect_param':1,'hold_effect_parameter':2})
    def test_item_missing_alias(self):
        with self.assertRaises(ValueError):b.item_parameter({})
    def test_output_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):b.write_outputs(pathlib.Path(tmp),{'../bad.md':b'bad'})
    def test_output_directory_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);(root/b.OUT).mkdir(parents=True);(root/'elsewhere').mkdir();(root/b.OUT/'sub').symlink_to(root/'elsewhere')
            with self.assertRaises(ValueError):b.write_outputs(root,{'sub/bad.md':b'bad'})
            self.assertFalse((root/'elsewhere/bad.md').exists())


if __name__=='__main__':unittest.main()
