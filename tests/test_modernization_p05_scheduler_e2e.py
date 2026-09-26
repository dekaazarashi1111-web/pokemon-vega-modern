"""対照差・抑制・終了コード・偽PASS・途中ログ・書込ガード契約の回帰。"""
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import run_modernization_p05_scheduler_e2e as m


class SchedulerResultTests(unittest.TestCase):
    def record(self, case='dragonize', mode='active'):
        ability, pm, em = m.CASES[case]
        active, final, double = mode == 'active', case == 'eelevate_final_ko', case == 'eelevate_remaining_foe_ko'
        player_hp, enemy_hp = 500, 500
        if case in ('dragonize', 'mega_sol', 'piercing_drill') and active:
            enemy_hp = 491
        elif case == 'eelevate_ground' and not active:
            player_hp = 491
        elif case == 'fire_mane':
            enemy_hp = 476 if active else 483
        elif case == 'spicy_spray':
            player_hp, enemy_hp = 486, 469 if active else 500
        elif final or double:
            enemy_hp = 0
        return dict(schema_version=1, status='OBSERVED', scope=m.SCOPE, rom_sha256=m.ROM_SHA,
                    case=case, mode=mode, ability_id=ability, ability_after=ability if mode != 'absent' else 0,
                    player_move=pm, enemy_move=em, battlers=4 if double else 2, frames=600, key_presses=12,
                    player_hp=player_hp, enemy_hp=enemy_hp, player_pp=19, enemy_pp=20 if final or double else 19,
                    player_status=0, enemy_status=16 if case == 'spicy_spray' and active else 0,
                    attack_stage=7 if double and active else 6, remaining_foe_hp=500 if double else 0,
                    remaining_foe_pp=19 if double else 0, partner_pp=19 if double else 0,
                    end_phase_seen=not final, battle_outcome=1 if final else 0,
                    fixture_boundary='PRE_FIRST_ACTION', host_write_guard=True, normal_battle_input=True,
                    full_p05_acceptance=False, release_ready=False, warnings_errors=0)

    def validate(self, record, code=0):
        return m.validate_result(json.dumps(record).encode(), record['case'], record['mode'], code)

    def matrix(self):
        return [self.record(*pair) for pair in m.PAIRS]

    def test_all_24_conditions_and_matrix(self):
        records = self.matrix()
        for record in records:
            self.validate(record)
        m.validate_matrix(records)

    def test_each_fixed_contract_field_rejects_changes(self):
        for key, value in self.record().items():
            if key in m.NUMERIC or key in ('case', 'mode'):
                continue
            bad = self.record(); bad[key] = not value if type(value) is bool else str(value) + '_bad'
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate(bad)

    def test_bool_int_coercion_rejected_in_every_numeric_and_boolean_field(self):
        for key, value in self.record().items():
            if type(value) not in (int, bool):
                continue
            bad = self.record(); bad[key] = int(value) if type(value) is bool else True
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate(bad)

    def test_missing_extra_and_duplicate_json_keys(self):
        for key in self.record():
            bad = self.record(); del bad[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.validate_result(json.dumps(bad).encode(), 'dragonize', 'active', 0)
        bad = self.record(); bad['scheduler_e2e'] = True
        with self.assertRaises(ValueError): self.validate(bad)
        raw = json.dumps(self.record()).encode().replace(b'{', b'{"status":"PASS",', 1)
        with self.assertRaises(ValueError): m.validate_result(raw, 'dragonize', 'active', 0)

    def test_nonzero_or_signal_exit_cannot_be_hidden_by_json(self):
        for code in (1, 2, -11, -15, True, '0'):
            with self.subTest(code=code), self.assertRaises(ValueError): self.validate(self.record(), code)

    def test_malformed_json_and_unknown_condition(self):
        for raw in (b'', b'PASS', b'[]', b'{}', b'{}{}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError): m.validate_result(raw, 'dragonize', 'active', 0)
        for case, mode in (('other', 'active'), ('dragonize', 'other')):
            with self.assertRaises(ValueError): m.validate_result(b'{}', case, mode, 0)

    def test_timeout_and_no_input_not_accepted(self):
        for key, value in (('frames', 0), ('frames', 8000), ('key_presses', 0), ('key_presses', 600)):
            bad = self.record(); bad[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError): self.validate(bad)

    def test_one_turn_pp_bounds_reject_two_turn_solar_beam(self):
        for key, value in (('player_pp', 20), ('player_pp', 18), ('enemy_pp', 18)):
            bad = self.record('mega_sol', 'absent'); bad[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError): self.validate(bad)
        bad = self.record('mega_sol', 'absent'); bad['enemy_hp'] = 489
        with self.assertRaises(ValueError): self.validate(bad)

    def test_active_effect_required_and_controls_must_not_activate(self):
        for case in ('dragonize', 'mega_sol', 'piercing_drill'):
            for mode in m.MODES:
                bad = self.record(case, mode); bad['enemy_hp'] = 500 if mode == 'active' else 491
                with self.subTest(case=case, mode=mode), self.assertRaises(ValueError): self.validate(bad)

    def test_eelevate_ground_immunity_and_suppression(self):
        for mode in m.MODES:
            bad = self.record('eelevate_ground', mode); bad['player_hp'] = 491 if mode == 'active' else 500
            with self.subTest(mode=mode), self.assertRaises(ValueError): self.validate(bad)

    def test_eelevate_requires_actual_ko_and_remaining_foe(self):
        for field, value in (('enemy_hp', 1), ('remaining_foe_hp', 0), ('attack_stage', 6), ('partner_pp', 20)):
            bad = self.record('eelevate_remaining_foe_ko'); bad[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): self.validate(bad)
        for mode in m.MODES:
            bad = self.record('eelevate_final_ko', mode); bad['attack_stage'] = 7
            with self.subTest(mode=mode), self.assertRaises(ValueError): self.validate(bad)

    def test_spicy_requires_damage_burn_and_residual(self):
        for key, value in (('player_hp', 500), ('enemy_status', 0), ('enemy_hp', 500)):
            bad = self.record('spicy_spray'); bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): self.validate(bad)
        bad = self.record('spicy_spray', 'circus'); bad['enemy_status'] = 16
        with self.assertRaises(ValueError): self.validate(bad)

    def test_hp_and_numeric_ranges(self):
        for key in m.NUMERIC:
            bad = self.record(); bad[key] = -1
            with self.subTest(key=key), self.assertRaises(ValueError): self.validate(bad)
        for key in ('player_hp', 'enemy_hp'):
            bad = self.record(); bad[key] = 501
            with self.subTest(key=key), self.assertRaises(ValueError): self.validate(bad)

    def test_matrix_rejects_missing_and_duplicate_conditions(self):
        for records in (self.matrix()[:-1], self.matrix() + [self.record()], [self.record()] * 24):
            with self.assertRaises(ValueError): m.validate_matrix(records)

    def test_fire_mane_requires_positive_boost_not_merely_damage(self):
        for hp in (483, 490):
            records = self.matrix()
            next(r for r in records if (r['case'], r['mode']) == ('fire_mane', 'active'))['enemy_hp'] = hp
            with self.assertRaises(ValueError): m.validate_matrix(records)
        records = self.matrix()
        next(r for r in records if (r['case'], r['mode']) == ('fire_mane', 'circus'))['enemy_hp'] = 476
        with self.assertRaises(ValueError): m.validate_matrix(records)

    def test_source_embedding_requires_unique_entrypoint(self):
        original = '/*keep*/\nint main(int argc, char **argv) { return 0; }\n'
        self.assertEqual(m.embed_p02(original), original.replace('int main(', 'int p05_existing_p02_main('))
        for raw in ('', original + original):
            with self.assertRaises(ValueError): m.embed_p02(raw)


class SchedulerExecutionTests(unittest.TestCase):
    def test_output_preparation_invalidates_old_pass_and_all_case_logs(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(m, 'ROOT', Path(temp)):
            output = Path(temp) / '.local/out'; output.mkdir(parents=True)
            files = ['result.json', 'compile.stderr', 'dragonize--active.stdout', 'guard-bus8.stderr']
            for name in files: (output / name).write_text('OLD PASS')
            (output / 'unrelated.txt').write_text('keep')
            m.prepare_output(output)
            for name in files: self.assertFalse((output / name).exists())
            self.assertEqual((output / 'unrelated.txt').read_text(), 'keep')

    def test_output_outside_local_and_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(m, 'ROOT', Path(temp)):
            local = Path(temp) / '.local'; local.mkdir()
            outside = Path(temp) / 'elsewhere'; outside.mkdir()
            link = local / 'link'; link.symlink_to(outside, target_is_directory=True)
            for path in (local, outside, link, link / 'nested'):
                with self.subTest(path=path), self.assertRaises(ValueError): m.prepare_output(path)

    def test_failed_preflight_does_not_leave_previous_pass(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(m, 'ROOT', Path(temp)):
            out = Path(temp) / '.local/out'; out.mkdir(parents=True)
            (out / 'result.json').write_text('OLD PASS')
            with self.assertRaises(FileNotFoundError): m.run(out)
            self.assertFalse((out / 'result.json').exists())

    def test_timeout_preserves_partial_binary_output(self):
        error = subprocess.TimeoutExpired(['runner'], 1, output=b'partial\xff', stderr=b'failure\x80')
        with tempfile.TemporaryDirectory() as temp, patch.object(m.subprocess, 'run', side_effect=error):
            out = Path(temp)
            with self.assertRaises(subprocess.TimeoutExpired): m.capture(['runner'], out, 'case', 1)
            self.assertEqual((out / 'case.stdout').read_bytes(), b'partial\xff')
            self.assertEqual((out / 'case.stderr').read_bytes(), b'failure\x80')

    def test_capture_retains_failed_exit_without_turning_it_into_pass(self):
        completed = subprocess.CompletedProcess(['runner'], -11, b'{"status":"PASS"}', b'crash')
        with tempfile.TemporaryDirectory() as temp, patch.object(m.subprocess, 'run', return_value=completed):
            out = Path(temp)
            self.assertEqual(m.capture(['runner'], out, 'case', 1).returncode, -11)
            self.assertEqual((out / 'case.stderr').read_bytes(), b'crash')

    def test_identity_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'source'; path.write_bytes(b'abc')
            link = Path(temp) / 'link'; link.symlink_to(path)
            self.assertEqual(m.identity(path)['size'], 3)
            with self.assertRaises(ValueError): m.identity(link)

    def test_observation_source_has_no_injected_rom_calls_or_writes(self):
        source = (m.ROOT / m.SOURCE).read_text()
        body = source.split('static struct P05Observation p05_observe_turn(', 1)[1].split('\nint main(', 1)[0]
        for forbidden in ('write8(', 'write16(', 'write32', 'call_rom', 'call_bounded', 'call_preserving',
                          'restore_snapshot(', 'writeRegister', '->step(', '->loadState(', '->reset('):
            self.assertNotIn(forbidden, body)
        self.assertIn('core->runFrame(core)', body)
        self.assertIn('o.end_phase && main==P05_ACTION', body)
        self.assertLess(source.index('p05_arm_write_guard(core);'), source.index('p05_observe_turn(core,c);'))
        self.assertGreater(source.index('p05_restore_write_apis(core,&saved_apis);'), source.index('p05_observe_turn(core,c);'))
        for field in ('busWrite8', 'busWrite16', 'busWrite32', 'rawWrite8', 'rawWrite16', 'rawWrite32', 'writeRegister'):
            self.assertIn('c->' + field + '=p05_deny', source)


if __name__ == '__main__': unittest.main()
