"""現行生成元の2署名commit入口をvalidatorも同一集合で監査する。"""
import ast
from pathlib import Path
import unittest
from scripts import build_stage61_display_npc_event_audit as builder

ROOT = Path(__file__).resolve().parents[1]


def declaration(name):
    tree = ast.parse((ROOT / 'tools/stage61_state_namespace_collision_audit.py').read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
        and node.name == '_stage61_custom_save_compatibility_contract')
    for node in ast.walk(function):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError('validator declaration absent')


class SignatureHookManifestTests(unittest.TestCase):
    def test_both_signature_commits_match_generator_addresses_and_preimages(self):
        sources = {f'stage61_save_compatibility::{name}': (address, expected.hex())
                   for name, address, expected, symbol, register in builder.STAGE61_SAVE_COMPATIBILITY_HOOKS
                   if symbol == 'Stage61State_CommitSignatureByte'}
        self.assertEqual(sources, {
            'stage61_save_compatibility::commit_replace_sector_signature_a': (0x080DACD8, '70b50004154e000c'),
            'stage61_save_compatibility::commit_replace_sector_signature_b': (0x080DAD70, '70b50004134e000c'),
        })
        self.assertEqual(declaration('signature_preimages'), sources)

    def test_all_six_generated_save_hooks_have_exact_validator_symbol_and_abi(self):
        expected = {f'stage61_save_compatibility::{name}': (address, symbol, register)
                    for name, address, preimage, symbol, register in builder.STAGE61_SAVE_COMPATIBILITY_HOOKS}
        actual = {name: (address, symbol, register) for name, address, symbol, register in declaration('custom_specs')}
        self.assertEqual(len(expected), 6)
        self.assertEqual(actual, expected)
        self.assertLessEqual(set(expected), set(declaration('patch_names')))
        self.assertIn('Stage61State_CommitSignatureByte', declaration('required_symbols'))

    def test_signature_export_reads_media_before_clearing_damage(self):
        source = (ROOT / 'overlays/stage61_display_npc_event_audit/stage61_display_npc_event_audit.c').read_text()
        body = source.split('u8 Stage61State_CommitSignatureByte(', 1)[1].split('\n}\n', 1)[0]
        fragments = ['stage61_save_mark_damaged(sector)', 'if (program_byte(', 'FN_READ_FLASH_SECTION(',
                     'stage61_save_readback_matches_prepared(', 'stage61_save_reject_written_target_sector(',
                     'stage61_save_clear_damaged(sector)']
        positions = [body.index(fragment) for fragment in fragments]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('one_based_id == 0u || one_based_id > STAGE61_SAVE_SLOT_SECTORS', body)
