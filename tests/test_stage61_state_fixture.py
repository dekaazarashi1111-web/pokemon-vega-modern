import ast
from pathlib import Path
import unittest
from tools.stage61_state_fixture import covered, SCOPE


class Stage61StateFixtureTests(unittest.TestCase):
    def test_adjacent_declarations_cover_one_span(self):
        self.assertTrue(covered([{'start': 1, 'end_exclusive': 8}],
            [{'start': 1, 'end_exclusive': 4}, {'start': 4, 'end_exclusive': 8}]))

    def test_single_undeclared_byte_rejects_whole_span(self):
        self.assertFalse(covered([{'start': 1, 'end_exclusive': 8}],
            [{'start': 1, 'end_exclusive': 4}, {'start': 5, 'end_exclusive': 8}]))

    def test_overlapping_declared_union_and_invalid_ranges(self):
        self.assertTrue(covered([{'start': 2, 'end_exclusive': 9}],
            [{'start': 1, 'end_exclusive': 6}, {'start': 3, 'end_exclusive': 10}]))
        with self.assertRaises(ValueError):
            covered([], [{'start': 5, 'end_exclusive': 4}])

    def test_fixture_is_explicit_not_the_default_strict_gate(self):
        self.assertEqual(SCOPE, 'STATE_NAMESPACE_UNIT_FIXTURE_ONLY')
        source = (Path(__file__).resolve().parents[1] / 'scripts/build_stage61_display_npc_event_audit.py').read_text()
        tree = ast.parse(source)
        build = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'build')
        self.assertEqual(build.args.kw_defaults[0].value, 'STRICT')
        self.assertIn('require_complete=True', ast.get_source_segment(source, build))
