"""Stage61正本へのpin更新が、採択済み二つのhotfixだけであることを検証する。"""
import hashlib
from pathlib import Path
import unittest
from tools import stage61_cyclic_decision_contracts as cyclic
from tools import stage61_interaction_oracle as oracle

ROOT = Path(__file__).resolve().parents[1]


class MoveMemorySourceProvenanceTests(unittest.TestCase):
    def test_runtime_delta_is_only_stale_battle_flag_hotfix(self):
        name = 'overlays/move_memory/move_memory.c'
        current = (ROOT / name).read_text()
        delta = '''    /* field-use item入口そのものが戦闘中の呼出しを遮断する。gBattleTypeFlagsは
     * 戦闘終了後も直前の種別を保持するため、フィールド判定には使わない。 */
    (void)battle_type_flags;
    return facility == 0 && raid == 0;'''
        self.assertEqual(current.count(delta), 1)
        previous = current.replace(delta, '    return battle_type_flags == 0 && facility == 0 && raid == 0;', 1)
        self.assertEqual(hashlib.sha256(previous.encode()).hexdigest(),
                         'ccf816ba5a7fff11a2f370cb90f55846444ccccec5b65fe53f6f8cfbc051b3a5')
        actual = hashlib.sha256(current.encode()).hexdigest()
        self.assertEqual(actual, '369f46588477ec7a2a581ec938ccbbab42992ec7cde444ca5920889f5639e1c3')
        self.assertEqual(cyclic._SOURCE_BINDINGS[name], actual)
        self.assertEqual(oracle.PARTY_MOVE_MODEL_SOURCE_SHA256[name], actual)

    def test_builder_delta_is_only_field_item_return_path_hotfix(self):
        name = 'scripts/build_move_memory.py'
        current = (ROOT / name).read_text()
        comment = '''    # フィールド用たいせつなものはfield-item復帰経路を使う。BAG_MENU (4)は
    # CB2_ReturnToFieldWithOpenMenuを先に登録し、Bag終了後にgFieldCallbackより
    # 優先されるため、VegaMoveMemory_FieldUseが呼ばれず破棄される。
'''
        self.assertEqual(current.count(comment), 1)
        self.assertEqual(current.count('bytes((1, 1, 2, 2))'), 2)
        previous = current.replace(comment, '', 1).replace('bytes((1, 1, 2, 2))', 'bytes((1, 1, 2, 4))')
        self.assertEqual(hashlib.sha256(previous.encode()).hexdigest(),
                         '579976cacf8b75638e1c053db68ecfe1d4a5a804c8773e5bab11b8658f074c13')
        actual = hashlib.sha256(current.encode()).hexdigest()
        self.assertEqual(actual, '374dcfc9e40d36f9fd3019c0191d52e278e495760fad666f445fb57d99d30817')
        self.assertEqual(cyclic._SOURCE_BINDINGS[name], actual)
        self.assertEqual(oracle.PARTY_MOVE_MODEL_SOURCE_SHA256[name], actual)
