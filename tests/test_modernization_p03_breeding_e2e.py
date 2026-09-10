"""Contract negatives use synthetic JSON, never counted as emulator executions."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import run_modernization_p03_breeding_e2e as b


def synthetic(name='lightball-father'):
    value = b.expected_result(name)
    value.update(generation_steps=509, hatch_clock_start=22, hatch_steps=2793,
                 hatch_callback_frames=528, hatch_state_mask=(1 << 6) | (1 << 10),
                 total_frames=200000, witness={key: (i+1)*100 for i, key in enumerate(b.WITNESS)})
    return value


def encoded(value):
    return json.dumps(value).encode()


def synthetic_rom():
    data = bytearray(33554432)
    def u32(address, value):
        struct.pack_into('<I', data, address-0x08000000, value)
    u32(0x0804346C, 0x0958B95C); u32(0x09FDA1F8, 0x0958B95C)
    u32(0x0958B95C+24*4, 0x09FDA498)
    struct.pack_into('<HBHB', data, 0x01FDA498, 39, 1, 84, 1)
    u32(0x08045214, 0x09FF0BD4); u32(0x0804528C, 0x09FF0BD4)
    u32(0x08045288, 7507)
    words = [20024, 175, 217, 252, 268, 273, 321, 549, 20025] + [65535]*(7507-9)
    struct.pack_into('<7507H', data, 0x01FF0BD4, *words)
    u32(0x080001CC, 0x090421F4)
    for move, pp in {39: 30, 84: 30, 175: 15, 273: 10, 344: 15}.items():
        data[0x010421F4+12*move+4] = pp
    return data


class BreedingResultTests(unittest.TestCase):
    def rejects(self, value):
        with self.assertRaises(ValueError):
            b.validate_result(encoded(value), 'lightball-father', 0)

    def test_eight_distinct_contracts(self):
        self.assertEqual(len(b.CASES), 8)
        for name in b.CASES:
            with self.subTest(name=name):
                self.assertEqual(b.validate_result(encoded(synthetic(name)), name, 0)['case'], name)

    def test_rejects_abnormal_exit_even_with_pass(self):
        for code in (-11, -15, 1, 2, None, False, True, 0.0, '0'):
            with self.subTest(code=code), self.assertRaises(ValueError):
                b.validate_result(encoded(synthetic()), 'lightball-father', code)

    def test_rejects_duplicate_and_nonfinite_json(self):
        for raw in (b'{"status":"PASS","status":"FAIL"}', b'NaN', b'Infinity', b'{', b'\xff', b'{}{}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                b.validate_result(raw, 'lightball-father', 0)

    def test_rejects_wrong_schema_and_case(self):
        for key in ('scope', 'case', 'rom_sha256', 'schema_version', 'status'):
            value=synthetic(); value[key]='wrong'; self.rejects(value)
        value=synthetic(); value['extra']=0; self.rejects(value)
        value=synthetic(); del value['witness']; self.rejects(value)

    def test_rejects_wrong_moves_and_pp_in_each_slot(self):
        for field in ('moves', 'pp'):
            for index in range(4):
                value=synthetic(); value[field][index]+=1; self.rejects(value)
                value=synthetic(); value[field][index]=False; self.rejects(value)

    def test_rejects_lightball_condition_changes(self):
        for field in ('father_item', 'mother_item'):
            value=synthetic(); value[field]=0 if value[field] else 202; self.rejects(value)
        no_item=synthetic('both-parents'); no_item['moves'][-1]=344
        with self.assertRaises(ValueError):b.validate_result(encoded(no_item),'both-parents',0)

    def test_requires_each_real_route_boolean(self):
        for field in ('ordinary_deposit', 'ordinary_claim', 'native_hatch',
                      'egg_and_hatched_save_reload', 'parent_queue_byte_identity'):
            value=synthetic(); value[field]=False; self.rejects(value)
            value=synthetic(); value[field]=1; self.rejects(value)

    def test_does_not_promote_representative_to_release(self):
        for field in ('all_breeding_paths_accepted', 'full_p03_acceptance', 'release_ready'):
            value=synthetic(); value[field]=True; self.rejects(value)
        value=synthetic(); value['parent_fixture_only']=False; self.rejects(value)

    def test_requires_three_cores_two_saves_and_guards(self):
        for field in ('fresh_cores','manual_save_counter_delta','native_hatch_save_counter_delta','total_save_counter_delta','host_write_barriers','rtc_flash_bytes_preserved'):
            value=synthetic(); value[field]-=1; self.rejects(value)

    def test_rejects_warning_and_integer_bool_confusion(self):
        for invalid in (False, True, 0.0, 1, '0'):
            value=synthetic(); value['warnings_errors']=invalid; self.rejects(value)

    def test_requires_every_witness(self):
        for field in b.WITNESS:
            value=synthetic(); value['witness'][field]=0; self.rejects(value)
            value=synthetic(); del value['witness'][field]; self.rejects(value)

    def test_requires_each_temporal_edge(self):
        for before, after in zip(b.WITNESS,b.WITNESS[1:]):
            value=synthetic(); value['witness'][after]=value['witness'][before]; self.rejects(value)

    def test_rejects_nonnumeric_and_out_of_frame_witness(self):
        for invalid in (False, True, 1.0, '1', -1, 600001):
            value=synthetic(); value['witness']['generated']=invalid; self.rejects(value)

    def test_bounds_each_runtime_counter(self):
        for field in b.DYNAMIC[:-1]:
            for invalid in (False, 0.0, '0', -1, 600001):
                value=synthetic(); value[field]=invalid; self.rejects(value)

    def test_requires_generation_steps(self):
        for count in (0,4097):
            value=synthetic(); value['generation_steps']=count; self.rejects(value)

    def test_requires_exact_native_cycle_cadence(self):
        for field in ('hatch_steps','hatch_clock_start','initial_egg_cycles'):
            value=synthetic(); value[field]+=1; self.rejects(value)
        value=synthetic(); value['hatch_clock_start']=256; self.rejects(value)

    def test_requires_animation_nickname_and_bounded_callback(self):
        for field,value in [('hatch_state_mask',1<<6),('hatch_state_mask',1<<10),
                            ('hatch_state_mask',1<<16),('hatch_callback_frames',0),
                            ('hatch_callback_frames',9001)]:
            result=synthetic(); result[field]=value; self.rejects(result)

    def test_guard_checks_require_actual_expected_rejection(self):
        process={'schema_version':1,'returncode':1,'timed_out':False,'spawn_error':None}
        message=b'P03 archive: host write after observation barrier\n'
        b.validate_guard(b'',message,process)
        for key,value in [('returncode',0),('returncode',False),('returncode',-11),
                          ('timed_out',True),('spawn_error','permission denied')]:
            altered=process|{key:value}
            with self.assertRaises(ValueError):b.validate_guard(b'',message,altered)
        with self.assertRaises(ValueError):b.validate_guard(b'PASS',message,process)
        with self.assertRaises(ValueError):b.validate_guard(b'',b'different failure\n',process)

    def test_unique_embedding_accepts_real_source_spacing(self):
        for source,_ in b.EMBEDDED:
            actual=(ROOT/source).read_text()
            self.assertIn('int test_entry(',b.embed(actual,'test_entry'))
        for source in ('void other(void){}','int main(){} int main(){}'):
            with self.assertRaises(ValueError):b.embed(source,'test_entry')


class BreedingOracleTests(unittest.TestCase):
    def test_existing_rows_not_conditional_move_union(self):
        oracle=b.audit_oracle(synthetic_rom())
        self.assertEqual(oracle['level_one_moves'],[39,84])
        self.assertNotIn(344,oracle['ordinary_egg_moves'])

    def test_rejects_stale_level_or_egg_root_and_bounds(self):
        for address in (0x0804346C,0x09FDA1F8,0x08045214,0x0804528C,0x08045288,0x080001CC):
            data=synthetic_rom(); struct.pack_into('<I',data,address-0x08000000,0)
            with self.subTest(address=address),self.assertRaises(ValueError):b.audit_oracle(data)

    def test_rejects_generic_volt_tackle_and_wrong_level_one(self):
        for offset in (0x01FF0BD4+2,0x01FDA498):
            data=synthetic_rom();struct.pack_into('<H',data,offset,344)
            with self.assertRaises(ValueError):b.audit_oracle(data)

    def test_rejects_wrong_canonical_pp(self):
        data=synthetic_rom();data[0x010421F4+12*344+4]=45
        with self.assertRaises(ValueError):b.audit_oracle(data)

    def test_rejects_wrong_rom_length(self):
        with self.assertRaises(ValueError):b.audit_oracle(b'')


class BreedingOutputTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);(self.root/'.local').mkdir()
        self.patch=mock.patch.object(b,'ROOT',self.root);self.patch.start();self.addCleanup(self.patch.stop)

    def test_stale_pass_cleared_before_argument_failure(self):
        output=self.root/'.local/run';output.mkdir()
        for name in ('result.json','candidate.json','lightball-father.stdout','compile.process.json'):
            (output/name).write_text('old PASS')
        with self.assertRaises(ValueError):b.run(output,0)
        self.assertFalse(any(output.iterdir()))

    def test_cannot_use_local_root_or_external_directory(self):
        for path in (self.root/'.local',self.root/'outside'):
            with self.assertRaises(ValueError):b.prepare_output(path)

    def test_rejects_symlink_directory_ancestor_and_product(self):
        target=self.root/'.local/real';target.mkdir()
        link=self.root/'.local/link';link.symlink_to(target,target_is_directory=True)
        with self.assertRaises(ValueError):b.prepare_output(link/'nested')
        secret=self.root/'secret';secret.write_text('unchanged')
        (target/'result.json').symlink_to(secret)
        with self.assertRaises(ValueError):b.prepare_output(target)
        self.assertEqual(secret.read_text(),'unchanged')

    def test_preserves_unrelated_files(self):
        output=self.root/'.local/run';output.mkdir();p=output/'unrelated.txt';p.write_text('keep')
        b.prepare_output(output);self.assertEqual(p.read_text(),'keep')


if __name__=='__main__':
    unittest.main()
