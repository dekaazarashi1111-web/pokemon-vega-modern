"""Contracts use synthetic JSON, not manufactured runtime PASS evidence."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("p03_fullslots", ROOT / "scripts/run_modernization_p03_fullslots_e2e.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
r = m.repair


def fixture(mode="replace-0"):
    result = m.expected_result(mode)
    summary = mode.startswith("replace-") or mode == "cancel-summary"
    ask = summary or mode == "reject"
    result["witness"] = {"dialog": 10 if ask else 0, "summary": 20 if summary else 0,
                         "selection": 30 if summary else 0,
                         "stop": 40 if mode in ("reject", "cancel-summary") else 0,
                         "evolution_begin": 50, "evolution_update": 60, "field": 100,
                         "down_presses": int(mode[-1]) if mode.startswith("replace-") else 0}
    return result


def raw(result):
    return json.dumps(result).encode()


class ResultContracts(unittest.TestCase):
    def assert_bad(self, result, mode="replace-0", code=0):
        with self.assertRaises((ValueError, UnicodeError)):
            m.validate_result(raw(result), mode, code)

    def test_unknown_mode(self):
        with self.assertRaises(ValueError): m.validate_result(raw(fixture()), "made-up", 0)

    def test_duplicate_root_json(self):
        with self.assertRaises(ValueError):
            m.validate_result(raw(fixture()).replace(b'"status": "PASS"', b'"status":"FAIL","status":"PASS"'), "replace-0", 0)

    def test_duplicate_nested_json(self):
        with self.assertRaises(ValueError):
            m.validate_result(raw(fixture()).replace(b'"dialog": 10', b'"dialog":0,"dialog":10'), "replace-0", 0)

    def test_malformed_json(self):
        with self.assertRaises(ValueError): m.validate_result(b'{', "replace-0", 0)

    def test_invalid_utf8(self):
        with self.assertRaises(UnicodeError): m.validate_result(b'\xff', "replace-0", 0)

    def test_extra_json(self):
        with self.assertRaises(ValueError): m.validate_result(raw(fixture()) + b'{}', "replace-0", 0)

    def test_nonfinite_json(self):
        with self.assertRaises(ValueError): m.strict_json(b'{"x":NaN}')

    def test_unexpected_key(self):
        result = fixture(); result["extra"] = True; self.assert_bad(result)

    def test_array_root(self): self.assert_bad([])

    def test_witness_not_object(self):
        result = fixture(); result["witness"] = []; self.assert_bad(result)

    def test_reordered_summary(self):
        result = fixture(); result["witness"]["selection"] = 15; self.assert_bad(result)

    def test_missing_evolution(self):
        result = fixture(); result["witness"]["evolution_begin"] = 0; self.assert_bad(result)

    def test_reordered_evolution(self):
        result = fixture(); result["witness"]["evolution_update"] = 40; self.assert_bad(result)

    def test_nonreturning_field(self):
        result = fixture(); result["witness"]["field"] = 55; self.assert_bad(result)

    def test_unexpected_stop_on_replace(self):
        result = fixture(); result["witness"]["stop"] = 35; self.assert_bad(result)

    def test_reject_has_no_summary(self):
        result = fixture("reject"); result["witness"]["summary"] = 20; self.assert_bad(result,"reject")

    def test_cancel_requires_stop(self):
        result = fixture("cancel-summary"); result["witness"]["stop"] = 0; self.assert_bad(result,"cancel-summary")

    def test_reject_requires_stop(self):
        result = fixture("reject"); result["witness"]["stop"] = 0; self.assert_bad(result,"reject")

    def test_empty_cannot_have_summary(self):
        result = fixture("empty"); result["witness"]["summary"] = 20; self.assert_bad(result,"empty")

    def test_below_cannot_learn(self):
        result = fixture("below-level"); result["moves_after"][2] = 535; self.assert_bad(result,"below-level")

    def test_bool_inside_slots(self):
        result = fixture(); result["moves_after"][1] = True; self.assert_bad(result)

    def test_missing_slot(self):
        result = fixture(); result["pp_after"].pop(); self.assert_bad(result)

    def test_parent_failure_expected(self):
        m.validate_parent_failure(b"",b"P03F slot=0 move=535/535 pp=45/20\nmgba-modernization-p02-stage71: move slot PP differs from canonical/retained PP\n",1)

    def test_parent_crash_not_a_regression_success(self):
        with self.assertRaises(ValueError): m.validate_parent_failure(b"",b"segfault",-11)

    def test_parent_pass_is_not_expected_failure(self):
        with self.assertRaises(ValueError): m.validate_parent_failure(raw(fixture()),b"",0)

    def test_parent_other_failure_rejected(self):
        with self.assertRaises(ValueError): m.validate_parent_failure(b"",b"scene timeout",1)

    def test_parent_error_and_pp_failure_rejected(self):
        stderr=b"mGBA[ERROR]\npp=45/20\nmove slot PP differs from canonical/retained PP\n"
        with self.assertRaises(ValueError): m.validate_parent_failure(b"",stderr,1)


def valid_mode(mode):
    def test(self):
        document=fixture(mode)
        self.assertEqual(m.validate_result(raw(document),mode,0),document)
    return test


def missing_field(key):
    def test(self):
        result=fixture(); del result[key]; self.assert_bad(result)
    return test


def wrong_type(key,value):
    def test(self):
        result=fixture(); result[key]=value; self.assert_bad(result)
    return test


for mode in m.MODES:
    setattr(ResultContracts,"test_valid_"+mode.replace("-","_"),valid_mode(mode))
for key,value in m.expected_result("replace-0").items():
    setattr(ResultContracts,"test_missing_"+key,missing_field(key))
    bad = int(value) if type(value) is bool else (str(value) if type(value) is int else None)
    setattr(ResultContracts,"test_type_"+key,wrong_type(key,bad))
for index,code in enumerate([False, True, 0.0, "0", None, -11, 1]):
    def test(self,code=code): self.assert_bad(fixture(),code=code)
    setattr(ResultContracts,f"test_bad_return_code_{index}",test)
for key in m.WITNESS_KEYS:
    def test(self,key=key):
        result=fixture(); result["witness"][key]=False; self.assert_bad(result)
    setattr(ResultContracts,"test_witness_boolean_"+key,test)
    def test(self,key=key):
        result=fixture(); del result["witness"][key]; self.assert_bad(result)
    setattr(ResultContracts,"test_witness_missing_"+key,test)
for mode in ["replace-0","replace-1","replace-2","replace-3","empty"]:
    def test(self,mode=mode):
        result=fixture(mode); result["pp_after"][result["learned_slot"]]=45; self.assert_bad(result,mode)
    setattr(ResultContracts,"test_wrong_native_pp_"+mode.replace("-","_"),test)


class ExecutionContracts(unittest.TestCase):
    def test_embed_requires_exactly_one_entrypoint(self):
        for source in ("", "int main(int argc, char **argv)" * 2):
            with self.assertRaises(ValueError): m.embed(source,"renamed")

    def test_embed_only_renames_entry(self):
        s="prefix int main(int argc, char **argv) suffix"
        self.assertEqual(m.embed(s,"renamed"),"prefix int renamed(int argc, char **argv) suffix")

    def test_timeout_keeps_partial_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            prefix=Path(d)/"case"
            with mock.patch.object(m.subprocess,"run",side_effect=subprocess.TimeoutExpired("runner",1,output=b'partial\xff',stderr=b'error\xfe')):
                out,err,process=m.capture(["runner"],prefix,1)
            self.assertEqual(out,b'partial\xff'); self.assertEqual(err,b'error\xfe')
            self.assertEqual(prefix.with_suffix('.stdout').read_bytes(),out)
            self.assertEqual(prefix.with_suffix('.stderr').read_bytes(),err)
            self.assertIs(process['timed_out'],True)
            with self.assertRaises(ValueError): m.require_exited(process)

    def test_spawn_error_is_recorded(self):
        with tempfile.TemporaryDirectory() as d:
            prefix=Path(d)/"case"
            with mock.patch.object(m.subprocess,"run",side_effect=OSError("cannot execute")):
                _,_,p=m.capture(["runner"],prefix,1)
            self.assertEqual(p['spawn_error'],"cannot execute")
            self.assertTrue(prefix.with_suffix('.process.json').is_file())
            with self.assertRaises(ValueError): m.require_exited(p)

    def test_real_child_pass_then_signal_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            code="import os,signal; print('{}',flush=True); os.kill(os.getpid(),signal.SIGTERM)"
            out,err,p=m.capture([sys.executable,"-c",code],Path(d)/"child",5)
            self.assertEqual(m.require_exited(p),-15)
            with self.assertRaises(ValueError): m.validate_result(out,"replace-0",p['returncode'])

    def test_real_timeout_retains_output(self):
        with tempfile.TemporaryDirectory() as d:
            code="import time; print('partial',flush=True); time.sleep(10)"
            out,err,p=m.capture([sys.executable,"-c",code],Path(d)/"child",2)
            self.assertEqual(out,b'partial\n'); self.assertIs(p['timed_out'],True)

    def test_stale_pass_and_logs_removed_before_input_validation(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(m,"ROOT",Path(d)):
            p=Path(d)/".local/out";p.mkdir(parents=True)
            for name in ("result.json","compile.stdout","replace-0.stdout","parent-empty.stderr"):
                (p/name).write_text("old PASS")
            with self.assertRaises(FileNotFoundError):m.run(p)
            self.assertFalse(any(p.iterdir()))

    def test_output_must_be_private(self):
        with self.assertRaises(ValueError):m.prepare_output(ROOT/"content/not-private")

    def test_output_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d,mock.patch.object(m,"ROOT",Path(d)):
            base=Path(d)/".local";base.mkdir();(base/'actual').mkdir();(base/'link').symlink_to(base/'actual',target_is_directory=True)
            with self.assertRaises(ValueError):m.prepare_output(base/'link')

    def test_identity_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'actual';p.write_bytes(b'original');link=Path(d)/'link';link.symlink_to(p)
            with self.assertRaises(ValueError):m.identity(link)

    def test_scene_has_no_direct_native_calls_or_setters(self):
        source=(ROOT/m.SOURCE).read_text()
        scene=source.split('static struct P03FTrace p03f_scene',1)[1].split('static void p03f_check_mon',1)[0]
        for forbidden in ('call_preserving(', 'p02s_data(', 'p02s_set_data(', 'write8(', 'write16(', 'write32('):
            self.assertNotIn(forbidden,scene)
        self.assertIn('core->setKeys(core, key)',scene)
        self.assertIn('core->runFrame(core)',scene)

    def test_rtc_reservation_precedes_mapping(self):
        source=(ROOT/m.SOURCE).read_text().split('int main(int argc, char **argv)',1)[1]
        self.assertLess(source.index('seed SHA mismatch'),source.index('p03f_rtc_reserve(argv[2])'))
        self.assertLess(source.index('p03f_rtc_reserve(argv[2])'),source.index('qol_open('))
        self.assertIn('core = NULL; qol_log_core = NULL;',source)


class RepairContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent=(ROOT/r.PARENT_PATH).read_bytes()
        cls.candidate,cls.report=r.build(cls.parent)

    def test_deterministic_candidate(self):
        self.assertEqual(r.identity(self.candidate),{"size":33554432,"sha256":r.CANDIDATE_SHA})
        self.assertEqual(self.report['bug_bite_pp'],20)
        self.assertEqual(self.report['modified_bytes'],20)

    def test_original_parent_unchanged(self):
        self.assertEqual(r.identity((ROOT/r.PARENT_PATH).read_bytes())['sha256'],r.PARENT_SHA)

    def test_exactly_classified_sites_change(self):
        rebuilt=bytearray(self.parent)
        for offset,*_ in r.SITES:struct.pack_into('<I',rebuilt,offset,r.CANONICAL_PP)
        self.assertEqual(bytes(rebuilt),self.candidate)

    def test_not_global_literal_replacement(self):
        altered=bytearray(self.parent);struct.pack_into('<I',altered,0x1f00000,r.OLD_PP)
        out=r.patch_sites(bytes(altered))
        self.assertEqual(struct.unpack_from('<I',out,0x1f00000)[0],r.OLD_PP)
        with self.assertRaises(ValueError):r.build(bytes(altered))

    def test_bad_canonical_root(self):
        altered=bytearray(self.parent);struct.pack_into('<I',altered,0x1cc,0x08000000)
        with self.assertRaisesRegex(ValueError,'canonical move root'):r.patch_sites(bytes(altered))

    def test_truncated_parent_rejected(self):
        with self.assertRaises(ValueError):r.build(self.parent[:-1])

    def test_wrong_full_parent_hash_rejected(self):
        altered=bytearray(self.parent);altered[-1]^=1
        with self.assertRaisesRegex(ValueError,'parent identity'):r.build(bytes(altered))

    def test_repeated_application_rejected(self):
        with self.assertRaises(ValueError):r.build(self.candidate)
        with self.assertRaisesRegex(ValueError,'preimage'):r.patch_sites(self.candidate)

    def test_bad_candidate_digest_rejected(self):
        with mock.patch.object(r,'CANDIDATE_SHA','0'*64):
            with self.assertRaisesRegex(ValueError,'Stage81 identity'):r.build(self.parent)

    def test_no_release_or_baseline_promotion(self):
        for key in ('active_baseline_changed','current_stage79_candidate_changed','full_p03_acceptance','release_ready'):
            self.assertIs(self.report[key],False)


for index,(offset,code_offset,_,_) in enumerate(r.SITES):
    def test(self,offset=offset):
        altered=bytearray(self.parent);altered[offset]^=1
        with self.assertRaisesRegex(ValueError,'preimage'):r.patch_sites(bytes(altered))
    setattr(RepairContracts,f'test_site_{index}_literal_guard',test)
    def test(self,offset=code_offset):
        altered=bytearray(self.parent);altered[offset]^=1
        with self.assertRaisesRegex(ValueError,'instruction guard'):r.patch_sites(bytes(altered))
    setattr(RepairContracts,f'test_site_{index}_instruction_guard',test)


if __name__ == '__main__':
    unittest.main()
