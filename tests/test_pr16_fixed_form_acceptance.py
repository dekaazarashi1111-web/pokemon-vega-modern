"""Source-only adversarial validator tests. These are NOT emulator receipts."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fixed_acceptance', ROOT / 'scripts/pr16_fixed_form_acceptance.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
# Synthetic oracle inputs for validator tests; runtime resolves actual IDs
# from the canonical manifest and preserves that manifest in sources.zip.
AUX = {'photon_geyser': 733, 'iron_head': 442}


def sample(name):
    row = m.expected(name, AUX)
    row.update(automatic_saves=0, save_counter_before=2,
               save_counter_after=2 + row['manual_saves'], total_frames=100,
               witness={key: 0 for key in m.WITNESS})
    if row['kind'] == 'necrozma-roundtrip':
        order = ('interaction', 'first_save', 'first_continue', 'menu', 'party',
                 'selection', 'transition', 'second_save', 'second_continue')
    elif row['kind'] == 'necrozma-decline':
        order = ('interaction', 'decline_dusk', 'menu', 'party', 'decline_dawn')
    else:
        order = ('project_move_seen', 'project_move_spent', 'first_battle_exit',
                 'item_replaced', 'second_battle', 'second_battle_exit',
                 'first_save', 'first_continue')
    for i, key in enumerate(order, 1):
        row['witness'][key] = i * 10
    row['witness'][order[-1]] = 100
    if row['kind'] == 'necrozma-roundtrip':
        row['witness']['reversion'] = row['witness']['transition']
        row['witness']['interaction'] = 1
        row['fusion_witness'] = {key: i for i, key in enumerate(m.FUSION_WITNESS, 1)}
        row['fusion_witness']['defuse_entry'] = 35
        row['fusion_witness']['restored_party_menu'] = 74
        row['fusion_witness']['restored_party_field'] = 76
    elif row['kind'] == 'crowned-battle-roundtrip':
        row['witness']['first_battle'] = row['witness']['project_move_seen']
    return row


class FixedFormAcceptanceTests(unittest.TestCase):
    def validate(self, row, code=0, stderr=b''):
        return m.validate(json.dumps(row).encode(), stderr, row['case'], code, AUX)

    def test_exact_five_case_set(self):
        self.assertEqual(len(m.CASES), 5)
        for name in m.CASES:
            with self.subTest(name=name):
                self.assertEqual(self.validate(sample(name)), sample(name))

    def test_each_required_field_is_fail_closed(self):
        for name in m.CASES:
            for key in sample(name):
                row = sample(name)
                del row[key]
                with self.subTest(case=name, key=key), self.assertRaises((ValueError, KeyError)):
                    m.validate(json.dumps(row).encode(), b'', name, 0, AUX)

    def test_no_extra_fields(self):
        row = sample(next(iter(m.CASES)))
        row['unreviewed_success'] = True
        with self.assertRaises(ValueError):
            self.validate(row)

    def test_strict_boolean_types(self):
        for name in m.CASES:
            for key, value in sample(name).items():
                if type(value) is bool:
                    row = sample(name)
                    row[key] = int(value)
                    with self.subTest(case=name, key=key), self.assertRaises(ValueError):
                        self.validate(row)

    def test_all_claim_flags_are_fixed(self):
        for name in m.CASES:
            for key in (*m.FLAGS, 'aggregate_gap_closed', 'full_p03_acceptance', 'release_ready'):
                row = sample(name)
                row[key] = not row[key]
                with self.subTest(case=name, key=key), self.assertRaises(ValueError):
                    self.validate(row)

    def test_exit_and_stderr(self):
        row = sample(next(iter(m.CASES)))
        for code in (True, False, 0.0, '0', None, -1, 1):
            with self.subTest(code=code), self.assertRaises(ValueError):
                self.validate(row, code=code)
        for stderr in ('', b'mGBA[warning]'):
            with self.assertRaises(ValueError):
                self.validate(row, stderr=stderr)

    def test_duplicate_and_nonfinite_json(self):
        name = next(iter(m.CASES))
        raw = json.dumps(sample(name)).encode()
        for bad in (raw[:-1] + b', "status":"PASS"}', raw.replace(b'"total_frames": 100', b'"total_frames": NaN'), raw + b'{}'):
            with self.assertRaises(ValueError):
                m.validate(bad, b'', name, 0, AUX)
        with self.assertRaises(ValueError):
            m.strict_json(b'{"witness":{"party":1,"party":2}}')

    def test_counters_and_identity(self):
        for name in m.CASES:
            for key, value in (('fresh_cores', 99), ('rom_sha256', '0' * 64),
                               ('save_counter_after', 900), ('total_frames', 0),
                               ('total_frames', 600001), ('total_frames', True),
                               ('automatic_saves', 3), ('auxiliary_move', 0)):
                row = sample(name)
                row[key] = value
                with self.subTest(case=name, key=key), self.assertRaises(ValueError):
                    self.validate(row)

    def test_lifecycle_witnesses(self):
        for name in m.CASES:
            original = sample(name)
            for key, value in original['witness'].items():
                row = copy.deepcopy(original)
                row['witness'][key] = 0 if value else 1
                with self.subTest(case=name, witness=key), self.assertRaises(ValueError):
                    self.validate(row)
            row = sample(name)
            row['witness']['extra'] = 1
            with self.assertRaises(ValueError):
                self.validate(row)

    def test_wrong_auxiliary_oracle(self):
        name = next(iter(m.CASES))
        with self.assertRaises(ValueError):
            m.validate(json.dumps(sample(name)).encode(), b'', name, 0, dict(AUX, photon_geyser=734))

    def test_no_partial_or_duplicate_closeout(self):
        results = [dict(name=name, result=sample(name), process=dict(schema_version=1, returncode=0, spawn_error=None, timed_out=False)) for name in m.CASES]
        guards = list(m.GUARDS)
        self.assertTrue(m.complete(results, [], guards, 5, AUX))
        for rows, failures, checks, attempts in (
            (results[:-1], [], guards, 5),
            (results[:-1] + results[:1], [], guards, 5),
            (results, [{'error': 'native failed'}], guards, 5),
            (results, [], guards[:-1], 5),
            (results, [], guards, True),
            (results, [], guards, 4),
        ):
            self.assertFalse(m.complete(rows, failures, checks, attempts, AUX))

    def test_aggregate_revalidates_process_and_payload(self):
        results = [dict(name=name, result=sample(name), process=dict(schema_version=1, returncode=0, spawn_error=None, timed_out=False)) for name in m.CASES]
        for envelope in ('result', 'process'):
            broken = copy.deepcopy(results)
            broken[0][envelope] = {}
            self.assertFalse(m.complete(broken, [], list(m.GUARDS), 5, AUX))
        self.assertFalse(m.complete([{'name': n} for n in m.CASES], [], list(m.GUARDS), 5, AUX))
        for key, value in (('returncode', True), ('timed_out', 0), ('spawn_error', 'failure')):
            broken = copy.deepcopy(results)
            broken[0]['process'][key] = value
            self.assertFalse(m.complete(broken, [], list(m.GUARDS), 5, AUX))

    def test_selected_cases_do_not_duplicate_old_successes(self):
        names = list(m.CASES)
        self.assertEqual(m.selected_cases(None), names)
        self.assertEqual(m.selected_cases(names[-2:]), names[-2:])
        for invalid in ([], names + names[:1], ['missing'], names[::-1]):
            with self.assertRaises(ValueError):
                m.selected_cases(invalid)

    def test_fusion_witnesses_are_required_ordered_and_bound(self):
        for name in list(m.CASES)[:2]:
            for key in m.FUSION_WITNESS:
                for value in (0, True, -1, 1000):
                    row = sample(name)
                    row['fusion_witness'][key] = value
                    with self.subTest(name=name, key=key, value=value), self.assertRaises(ValueError):
                        self.validate(row)
                row = sample(name)
                del row['fusion_witness'][key]
                with self.assertRaises(ValueError):
                    self.validate(row)
            for key, value in (('item_entry', 2), ('defuse_entry', 25), ('transformed', 25),
                               ('restored_party_menu', 69), ('restored_party_field', 81)):
                row = sample(name)
                row['fusion_witness'][key] = value
                with self.assertRaises(ValueError):
                    self.validate(row)

    def test_fusion_semantics_are_not_legacy_service_or_photon_restoration(self):
        for name in list(m.CASES)[:2]:
            for key, value in (('entry_kind', 'FORM_SERVICE'),
                               ('form_service_selection_claimed', True),
                               ('fusion_partner_restored_exact', False),
                               ('native_restored_party_view', False),
                               ('defusion_party_count_before_native_party_menu', 3),
                               ('defusion_party_count_after_native_party_menu', 2),
                               ('forgotten_move_not_restored', False),
                               ('defusion_signature_removed_and_compacted', False),
                               ('chosen_replacement_slot', 0),
                               ('fusion_item_id', 0), ('fusion_partner_species', 0)):
                row = sample(name)
                row[key] = value
                with self.subTest(name=name, key=key), self.assertRaises(ValueError):
                    self.validate(row)
            row = sample(name)
            row['automatic_saves'] = 1
            row['save_counter_after'] += 1
            with self.assertRaises(ValueError):
                self.validate(row)

    def test_fusion_manifest_bindings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'manifests').mkdir()
            item = root / 'manifests/item_ids.csv'
            species = root / 'manifests/species_ids.csv'
            item.write_text('id,cfru_symbol\n697,ITEM_N_SOLARIZER\n698,ITEM_N_LUNARIZER\n')
            species.write_text('id,dpe_symbol\n1189,SPECIES_SOLGALEO\n1190,SPECIES_LUNALA\n')
            m.verify_fusion_ids(root)
            item.write_text(item.read_text() + '697,ITEM_N_SOLARIZER\n')
            with self.assertRaises(ValueError):
                m.verify_fusion_ids(root)
            item.write_text('id,cfru_symbol\n0,ITEM_N_SOLARIZER\n698,ITEM_N_LUNARIZER\n')
            with self.assertRaises(ValueError):
                m.verify_fusion_ids(root)

    def test_fusion_ids_match_actual_repository_manifests(self):
        m.verify_fusion_ids(ROOT)

    def test_historical_probe_is_not_accepted(self):
        name = next(iter(m.CASES))
        row = sample(name)
        row.update(status='PASS_DIAGNOSTIC_ONLY', scope='PR16_P03_FIXED_FORM_TRANSITION_NATIVE_PROBE')
        with self.assertRaises(ValueError):
            self.validate(row)


if __name__ == '__main__':
    unittest.main()
