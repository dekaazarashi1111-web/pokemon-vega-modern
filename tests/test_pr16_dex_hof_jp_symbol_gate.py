"""公開symbol入力の言語混合拒否。合成例はROM型の受入へ数えない。"""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('jp_gate', ROOT/'scripts/pr16_dex_hof_jp_symbol_gate.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
FIXTURE = None


class SymbolTests(unittest.TestCase):
    def test_english_origin(self):
        row = g.parse_symbols(b'083ddee0 g 00000020 Example\n')['EXAMPLE']
        self.assertEqual((row['address_language'], row['english_length']), ('E', 32))
        self.assertNotIn('end', row)

    def test_case_insensitive_last_symbol_wins(self):
        rows = g.parse_symbols(b'08000000 g 00000002 Foo\n08000004 l 00000004 fOO\n')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows['FOO']['address'], 0x08000004)

    def test_compiler_labels_excluded(self):
        self.assertEqual(g.parse_symbols(b'08000000 l 00000000 .gcc2_compiled.\n'), {})

    def test_empty_patch_is_not_missing_file(self):
        self.assertEqual(g.parse_symbols(b''), {})
        self.assertEqual(g.SOURCE_ROWS['pokefirered.patch.sym'][1], 0)

    def test_malformed_symbol_rejected(self):
        for raw in (b'xyz g 00000001 x\n', b'08000000 g 1 x\n', b'08000000 g 00000001 x extra\n', b'08000000 g 00000001 \n'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                g.parse_symbols(raw)

    def test_language_scalar(self):
        self.assertEqual(g.parse_language_overrides(b'---\n# comment\nFoo:\n  J: 0x8000000\n'), {'FOO': {'J': 0x08000000}})

    def test_language_multiple_addresses(self):
        self.assertEqual(g.parse_language_overrides(b'Foo:\n  J:\n    - 0x8000000\n    - 0x8000010\n')['FOO']['J'], [0x08000000, 0x08000010])

    def test_language_zero_is_not_extent(self):
        rows = g.japanese_symbols({}, g.parse_language_overrides(b'Foo:\n  J: 0x0\n'))
        self.assertIsNone(rows['FOO']['eos_inclusive_extent'])

    def test_duplicate_language_label(self):
        with self.assertRaises(ValueError):
            g.parse_language_overrides(b'Foo:\n  J: 0x1\nfoo:\n  J: 0x2\n')

    def test_duplicate_language(self):
        with self.assertRaises(ValueError):
            g.parse_language_overrides(b'Foo:\n  J: 0x1\n  J: 0x2\n')

    def test_unknown_language_syntax(self):
        for raw in (b'Foo:\n  J: [0x1]\n', b'Foo:\n  J: null\n', b'Foo:\n  E: 0x1\n', b'Foo:\n  J: 0x1 # hint\n'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                g.parse_language_overrides(raw)

    def test_empty_address_list(self):
        with self.assertRaises(ValueError):
            g.parse_language_overrides(b'Foo:\n  J:\n')

    def test_empty_label_rejected(self):
        for raw in (b'Foo:\n', b'Foo:\nBar:\n  J: 0x1\n'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                g.parse_language_overrides(raw)

    def test_multiple_yaml_documents_rejected(self):
        for raw in (b'---\n---\nFoo:\n  J: 0x1\n', b'Foo:\n  J: 0x1\n---\nBar:\n  J: 0x2\n'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                g.parse_language_overrides(raw)

    def test_orphan_language(self):
        with self.assertRaises(ValueError):
            g.parse_language_overrides(b'  J: 0x1\n')

    def test_orphan_address_list(self):
        with self.assertRaises(ValueError):
            g.parse_language_overrides(b'Foo:\n    - 0x1\n')

    def test_list_after_scalar_rejected(self):
        with self.assertRaises(ValueError):
            g.parse_language_overrides(b'Foo:\n  J: 0x1\n    - 0x2\n')

    def test_address_and_extent_provenance_separated(self):
        symbols = g.parse_symbols(b'083ddee0 g 00000020 Example\n')
        jp = g.japanese_symbols(symbols, {'EXAMPLE': {'J': 0x083DDEE4}})
        row = jp['EXAMPLE']
        self.assertEqual(row['addresses'], [0x083DDEE4])
        self.assertEqual(row['inherited_english_length'], 32)
        self.assertIsNone(row['eos_inclusive_extent'])
        self.assertIsNone(row['extent_language'])
        with self.assertRaisesRegex(ValueError, 'serializer/EOS'):
            g.require_jp_extent(row)

    def test_missing_jp_override_not_english_fallback(self):
        self.assertEqual(g.japanese_symbols(g.parse_symbols(b'083ddee0 g 00000020 Example\n'), {'EXAMPLE': {'F': 0x083DDEE4}}), {})

    def test_unknown_label_zero_not_boundary(self):
        row = g.japanese_symbols({}, {'EXAMPLE': {'J': 0x083DDEE4}})['EXAMPLE']
        self.assertEqual(row['inherited_english_length'], 0)
        with self.assertRaises(ValueError):
            g.require_jp_extent(row)

    def test_neighbor_addresses_not_japanese_length(self):
        jp = g.japanese_symbols({}, {'A': {'J': 0x083DDEE0}, 'B': {'J': 0x083DDEE4}})
        with self.assertRaises(ValueError):
            g.require_jp_extent(jp['A'])

    def test_caller_supplied_extent_not_accepted(self):
        row = dict(address_language='J', extent_language='J', eos_inclusive_extent=4)
        with self.assertRaises(ValueError):
            g.require_jp_extent(row)

    def test_non_japanese_address_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Japanese address'):
            g.require_jp_extent({'address_language': 'E'})

    def test_exact_loader_ast(self):
        raw = b'def _load_symbols():\n symbols[label.upper()] = (addr, symbols[label.upper()][1] if label.upper() in symbols else 0)\n'
        self.assertTrue(g.inherited_length_loader(raw))
        with self.assertRaises(ValueError):
            g.inherited_length_loader(raw.replace(b'[1]', b'[0]'))

    def test_duplicate_loader_rejected(self):
        raw = b'def _load_symbols():\n pass\n'
        with self.assertRaises(ValueError):
            g.inherited_length_loader(raw + raw)

    def test_git_blob_identity(self):
        self.assertEqual(g.blob_sha(b''), 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391')

    def test_source_manifest_fixed_ref(self):
        self.assertEqual(len(g.source_manifest()), 4)
        self.assertTrue(all(row['commit'] == g.REF and row['repository'] == g.REPOSITORY for row in g.source_manifest().values()))


class FixedSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = ROOT/'.local/jp-symbol-sources'
        if FIXTURE is not None:
            cls.sources, cls.parent = FIXTURE
        elif directory.is_dir():
            cls.sources, cls.parent = g.fixed_sources(directory), (ROOT/g.PARENT).read_bytes()
        else:
            raise RuntimeError('fixed public source fixture required; never silently skip')

    def test_whole_fixed_source_audit(self):
        result = g.inspect(self.sources, self.parent)
        self.assertEqual((result['english_symbol_count'], result['language_patch_labels'], result['japanese_address_labels'], result['japanese_address_only_extents_rejected']), (50097, 181, 143, 112))
        self.assertEqual((result['newly_classified'], result['classified'], result['unclassified']), (0, 779, 95))
        self.assertEqual(result['typed_regions'], [])
        self.assertEqual(result['requested_rom_windows'], [])

    def test_each_whole_source_mutation_rejected(self):
        for name in self.sources:
            changed = dict(self.sources); changed[name] += b'\n'
            with self.subTest(name=name), self.assertRaises(ValueError):
                g.inspect(changed, self.parent)

    def test_missing_or_extra_source_rejected(self):
        for name in self.sources:
            changed = dict(self.sources); del changed[name]
            with self.subTest(name=name), self.assertRaises(ValueError):
                g.inspect(changed, self.parent)
        with self.assertRaises(ValueError):
            g.inspect(dict(self.sources, unexpected=b'x'), self.parent)

    def test_all_parent_fields_frozen(self):
        parent = json.loads(self.parent); parent['rows'][0]['hit']['target'] += 1
        with self.assertRaisesRegex(ValueError, 'whole independently frozen'):
            g.inspect(self.sources, g.encode(parent))

    def test_fixture_sources_are_not_mutated(self):
        before = copy.deepcopy(self.sources)
        g.inspect(self.sources, self.parent)
        self.assertEqual(before, self.sources)

    def test_source_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            for name, raw in self.sources.items():
                (path/name).write_bytes(raw)
            (path/'game.py').unlink(); (path/'game.py').symlink_to(ROOT/'scripts/pr16_dex_hof_jp_symbol_gate.py')
            with self.assertRaises(ValueError):
                g.fixed_sources(path)

    def test_source_ancestor_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp); (path/'real').mkdir(); (path/'real/cache').mkdir()
            (path/'link').symlink_to(path/'real', target_is_directory=True)
            with self.assertRaises(ValueError):
                g.fixed_sources(path/'link/cache')


if __name__ == '__main__':
    unittest.main()
