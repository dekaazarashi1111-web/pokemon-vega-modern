"""Fail-closed Stage82 recipe and native archive result contracts.

Synthetic witness mutations are unit tests, never mGBA acceptance evidence.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tools')]
import run_modernization_p03_archive_ui_e2e as suite
import modernization_p03_archive_ui_repair as recipe


def good(c):
    out = suite.expected_result(c)
    w = {k: 0 for k in suite.WITNESS}
    w.update(bag=1, mode_menu=2, mode_choice=3, field=100)
    a = c['action']
    if a <= 5:
        w['party'] = 4
        if c['family'] == 3:
            w.update(page_menu=5, page_choice=6)
    if a < 5:
        w['list'] = 7
    if a < 4:
        w['ask'] = 8
    if a in (0, 3):
        w.update(delete_ask=9, summary=10, selection=11)
    if a == 0:
        w.update(replaced=12, learned=13)
    if a == 1:
        w['learned'] = 13
    if a in (2, 3, 4):
        w['giveup'] = 20
    if a == 6:
        w['locked'] = 20
    out['witness'] = w
    return out


def raw(value):
    return json.dumps(value).encode()


class ArchiveContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = suite.vectors()

    def test_all_twenty_five_modes(self):
        for c in self.cases:
            with self.subTest(c=c['name']):
                suite.validate_result(raw(good(c)), c, 0)

    def test_no_boolean_exit_zero(self):
        for code in (False, True, None, 0.0, '0', -11, -15, 1, 2):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    suite.validate_result(raw(good(self.cases[0])), self.cases[0], code)

    def test_json_strictness(self):
        for data in (b'', b'null', b'[]', b'{"status":"PASS","status":"PASS"}', b'{"x":NaN}', b'{}{}', b'\xff'):
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    suite.validate_result(data, self.cases[0], 0)

    def test_no_schema_changes(self):
        c = self.cases[0]
        for key in good(c):
            value = good(c)
            del value[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                suite.validate_result(raw(value), c, 0)
        value = good(c); value['skip'] = True
        with self.assertRaises(ValueError):
            suite.validate_result(raw(value), c, 0)

    def test_scalar_type_or_value_changes(self):
        c = self.cases[0]
        for key, expected in suite.expected_result(c).items():
            value = good(c)
            if type(expected) is bool:
                value[key] = int(expected)
            elif type(expected) is int:
                value[key] = float(expected)
            elif type(expected) is str:
                value[key] = expected+'-wrong'
            else:
                continue
            with self.subTest(key=key), self.assertRaises(ValueError):
                suite.validate_result(raw(value), c, 0)

    def test_every_slot_and_pp_is_bound(self):
        for c in self.cases:
            for key in ('moves_before', 'pp_before', 'moves_after', 'pp_after'):
                for slot in range(4):
                    value = good(c); value[key][slot] += 1
                    with self.subTest(case=c['name'], key=key, slot=slot), self.assertRaises(ValueError):
                        suite.validate_result(raw(value), c, 0)

    def test_every_witness_is_required_or_forbidden(self):
        for c in self.cases:
            for key, stamp in good(c)['witness'].items():
                value = good(c); value['witness'][key] = 0 if stamp else 1
                with self.subTest(case=c['name'], key=key), self.assertRaises(ValueError):
                    suite.validate_result(raw(value), c, 0)

    def test_witness_types_and_bounds(self):
        for v in (False, 1.0, '1', None, -1, 20001):
            value = good(self.cases[0]); value['witness']['bag'] = v
            with self.subTest(v=v), self.assertRaises(ValueError):
                suite.validate_result(raw(value), self.cases[0], 0)

    def test_witness_order_is_not_just_presence(self):
        for left, right in [('bag','mode_menu'), ('mode_choice','party'), ('party','page_menu'),
                            ('page_choice','list'), ('list','ask'), ('ask','delete_ask'),
                            ('delete_ask','summary'), ('summary','selection'),
                            ('selection','replaced'), ('replaced','learned'), ('learned','field')]:
            value = good(self.cases[0]); w = value['witness']; w[left], w[right] = w[right], w[left]
            with self.subTest(pair=(left,right)), self.assertRaises(ValueError):
                suite.validate_result(raw(value), self.cases[0], 0)

    def test_false_release_promotion_rejected(self):
        for key in ('breeding_e2e','full_p03_acceptance','release_ready'):
            v = good(self.cases[0]); v[key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                suite.validate_result(raw(v), self.cases[0], 0)

    def test_negative_controls_are_specific(self):
        reasons = {'parent-gate': b'P03 archive: unlocked archive denied by stale comparison\n',
                   'gate-only-list': b'mGBA[GBA][0x04] pc=081c7a60: Illegal opcode: 0000efff\nP03 archive: native list corrupted selected party metadata\n'}
        for name, reason in reasons.items():
            suite.validate_negative(b'', reason, 1, name)
            for stdout, stderr, code in [(b'{}',reason,1), (b'',reason,True), (b'',reason,-11),
                                          (b'',b'timeout\n',1), (b'',b'mGBA[warning]\n'+reason,1), (b'',reason,0)]:
                with self.subTest(name=name,code=code), self.assertRaises(ValueError):
                    suite.validate_negative(stdout,stderr,code,name)

    def test_stale_pass_removed_before_input_failure(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as d:
            p = Path(d); (p/'result.json').write_text('{"status":"PASS"}')
            (p/'old.stdout').write_bytes(b'old PASS')
            with patch.object(suite, 'vectors', side_effect=ValueError('broken inputs')):
                with self.assertRaises(ValueError): suite.run(p)
            self.assertFalse((p/'result.json').exists()); self.assertFalse((p/'old.stdout').exists())

    def test_output_cannot_leave_private_area(self):
        with self.assertRaises(ValueError): suite.prepare_output(ROOT / 'content/archive-illegal-test')
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as d:
            p=Path(d); (p/'link').symlink_to(p, target_is_directory=True)
            with self.assertRaises(ValueError): suite.prepare_output(p/'link'/'nested')

    def test_partial_timeout_output_and_no_success_result(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as d:
            prefix=Path(d)/'timeout'
            with patch.object(suite.previous.subprocess, 'run', side_effect=subprocess.TimeoutExpired('test',1,output=b'partial\xff',stderr=b'err\xfe')):
                stdout,stderr,process=suite.previous.capture(['test'],prefix,1)
            self.assertEqual(stdout,b'partial\xff');self.assertEqual(stderr,b'err\xfe')
            self.assertEqual(prefix.with_suffix('.stdout').read_bytes(),stdout)
            self.assertEqual(prefix.with_suffix('.stderr').read_bytes(),stderr)
            with self.assertRaises(ValueError):suite.previous.require_exited(process)

    def test_guard_apis_are_seven_distinct_boundaries(self):
        self.assertEqual(set(suite.GUARDS), {'bus8','bus16','bus32','raw8','raw16','raw32','register'})
        source=(ROOT/suite.SOURCE).read_text()
        self.assertEqual(source.count('a_guard(c);'),3)
        self.assertNotIn('HW_RTC)',source)
        self.assertIn('memcmp(before,s->data,0x20000)',source)


class ArchiveRecipe(unittest.TestCase):
    def test_native_abi_nonoverlap(self):
        recipe.validate_layout()
        for key in recipe.LAYOUT:
            for value in (False,-1,recipe.LAYOUT[key]+1):
                changed=recipe.LAYOUT.copy();changed[key]=value
                with self.subTest(key=key,value=value), self.assertRaises(ValueError):recipe.validate_layout(changed)

    def test_source_and_reviewed_payload_identity(self):
        self.assertEqual(recipe.sha((ROOT/recipe.ASM).read_bytes()),recipe.ASM_SHA)
        payload=next(bytes.fromhex(new) for name,_,_,new in recipe.SITES if name=='native_list_builder')
        self.assertEqual(recipe.sha(payload[:recipe.PAYLOAD_SIZE]),recipe.PAYLOAD_SHA)
        self.assertEqual(payload[recipe.PAYLOAD_SIZE:], bytes.fromhex('c046')*44)

    def test_reject_non_parent_or_already_repaired_rom(self):
        for data in (None,b'',b'bad',bytearray(b'bad')):
            with self.subTest(data=data), self.assertRaises(ValueError):recipe.build(data)
        original=(ROOT/recipe.parent.PARENT_PATH).read_bytes()
        parent,_=recipe.parent.build(original)
        candidate,report=recipe.build(parent)
        self.assertEqual(recipe.sha(candidate),recipe.CANDIDATE_SHA)
        self.assertEqual(report['changed_byte_count'],317)
        self.assertEqual(len(report['repairs']),6)
        self.assertTrue(report['hall_of_fame_required'])
        self.assertFalse(report['learnsets_changed']);self.assertFalse(report['release_ready'])
        for invalid in (candidate, parent[:100]+bytes([parent[100]^1])+parent[101:]):
            with self.assertRaises(ValueError):recipe.build(invalid)
        spans=[(o,o+len(bytes.fromhex(a))) for _,o,a,_ in recipe.SITES]
        self.assertTrue(all(any(start<=i<end for start,end in spans) for i,(a,b) in enumerate(zip(parent,candidate)) if a!=b))

    def test_gate_keeps_flag_and_conditional_branch(self):
        for name,_,old,new in recipe.SITES:
            if name.endswith('GateScript'):
                self.assertEqual(old,'210d800100');self.assertEqual(new,'0000000000')
        self.assertEqual(sum(n.endswith('GateScript') for n,*_ in recipe.SITES),2)

    def test_missing_assembler_is_failure_not_skip(self):
        with patch.object(recipe.shutil,'which',return_value=None):
            with self.assertRaises(ValueError):recipe.verify_assembly()


if __name__=='__main__': unittest.main()
