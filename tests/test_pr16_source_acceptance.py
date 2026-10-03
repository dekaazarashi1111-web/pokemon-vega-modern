"""Mutations for reproduced blank-UI and named-alias defects, not native passes."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_source_acceptance as m


class SourceAliasAudit(unittest.TestCase):
    def records(self):
        rows = []
        for route, count in m.OLD_COUNTS.items():
            member = 'level_up_final.csv' if route == 'level_up' else 'egg_moves_final.csv'
            for i in range(count):
                rows.append(dict(route=route, source_class='CURRENT_PRESERVED',
                                 source_member=member, source_csv_line=10000+i,
                                 move_key='MOVE_KEY_VEGA_457'))
        keys = {spec[0]: key for key, spec in m.ALIASES.items()}
        for member, entries in m.ALIAS_POSITIONS.items():
            for line, (species, mid) in entries.items():
                rows.append(dict(route='level_up' if member.startswith('level') else 'egg',
                                 source_class='CURRENT_PRESERVED', source_member=member,
                                 source_csv_line=line, species_key='SPECIES_KEY_'+species,
                                 move_key=keys[mid], move_id=mid))
        return rows

    def test_old_472_and_named_27_are_distinct_and_no_new_adoption(self):
        r = m.reconcile_legacy_count(self.records())
        self.assertEqual(r['historical_prefix_projection']['rows'], 472)
        self.assertEqual(r['previously_unaccounted_named_aliases']['rows'], 27)
        self.assertEqual(r['canonical_legacy_preservation']['rows'], 499)
        self.assertEqual(r['new_adoptions'], 0)
        self.assertFalse(r['rom_or_native_acceptance_implied'])

    def test_not_just_accepting_any_499_rows(self):
        for key, value in [('source_csv_line', 1), ('species_key', 'SPECIES_KEY_EEVEE'),
                           ('move_id', 1), ('move_key', 'MOVE_KEY_UNKNOWN_ALIAS'),
                           ('source_class', 'V3_ADDED'), ('route', 'machine')]:
            rows = self.records(); rows[-1][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.reconcile_legacy_count(rows)

    def test_missing_or_duplicate_original_rejected(self):
        original = self.records()
        for rows in (original[:-1], original[1:], original+[copy.deepcopy(original[-1])]):
            with self.assertRaises(ValueError): m.reconcile_legacy_count(rows)

    def test_timing_route_cannot_be_reclassified(self):
        rows = self.records(); rows[-1]['route'] = 'level_up'
        with self.assertRaises(ValueError): m.reconcile_legacy_count(rows)


class NativeScreenshotChecks(unittest.TestCase):
    def image(self, value=1):
        return b'P6\n240 160\n255\n' + bytes([value, 2, 3]) + b'\x00'*(240*160*3-3)

    def test_nonblank_native_ppm(self):
        r = m.inspect_ppm(self.image())
        self.assertEqual(r['distinct_colors'], 2)
        self.assertEqual(r['size'], 115215)

    def test_reproduced_blank_and_constant_colors_rejected(self):
        for color in (0, 127, 255):
            with self.subTest(color=color), self.assertRaisesRegex(ValueError, 'single-color'):
                m.inspect_ppm(b'P6\n240 160\n255\n' + bytes([color])*115200)

    def test_malformed_truncated_oversized_ppm_rejected(self):
        for raw in (self.image()[:-1], self.image()+b'x', self.image().replace(b'240', b'241', 1)):
            with self.assertRaises(ValueError): m.inspect_ppm(raw)

    def test_all_six_required_images_and_transition(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for index, case in enumerate(m.SUMMARY_CASES):
                for page, suffix in enumerate(('summary-entry', 'skills')):
                    (root/(case+'-'+suffix+'.ppm')).write_bytes(self.image(index*2+page+1))
            self.assertEqual(len(m.validate_summary_screenshots(root)), 6)
            a = root/'summary-220-0-summary-entry.ppm'
            b = root/'summary-220-0-skills.ppm'
            b.write_bytes(a.read_bytes())
            with self.assertRaisesRegex(ValueError, 'transition'):
                m.validate_summary_screenshots(root)
            b.unlink()
            with self.assertRaisesRegex(ValueError, 'missing'):
                m.validate_summary_screenshots(root)


if __name__ == '__main__': unittest.main()
