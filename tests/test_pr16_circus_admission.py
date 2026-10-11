"""Circusの新しいpending接続だけを、mockでない現行CFRU所有APIと検証する。"""
import ctypes as C
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Command(C.Structure):
    _fields_ = [(key, C.c_uint8) for key in (
        'active', 'facility_active', 'ai_profile', 'mechanic_mode', 'facility_format',
        'facility_rule', 'mirage_mask', 'raid_active', 'raid_boss_party_index',
        'raid_partner_mask', 'raid_shield_count', 'raid_turn_limit',
        'raid_capture_allowed', 'reserved')] + [
        ('facility_state', C.c_uint16 * 11), ('mirage_virtual_items', C.c_uint16 * 6)]


class Shadow(C.Structure):
    _fields_ = [('magic', C.c_uint32), ('command', Command)]


class CircusAdmissionContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cc = shutil.which('cc')
        if not cc:
            raise RuntimeError('必須のhost C compilerがない')
        cls.work = tempfile.TemporaryDirectory(prefix='circus-admission-')
        target = Path(cls.work.name) / 'admission.so'
        subprocess.run([cc, '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
            '-fPIC', '-shared', str(ROOT/'overlays/circus_admission/circus_admission.c'),
            str(ROOT/'overlays/cfru/integration.c'), str(ROOT/'overlays/cfru/runtime.c'),
            '-o', str(target)], check=True, capture_output=True)
        cls.lib = C.CDLL(str(target))
        cls.lib.cfru_integration_pending_configure_facility.argtypes = [C.c_int]*3
        cls.lib.cfru_integration_pending_configure_facility.restype = C.c_uint8
        cls.lib.VegaCircusAdmissionSelectPending.argtypes = []
        cls.lib.VegaCircusAdmissionSelectPending.restype = C.c_uint8
        cls.lib.cfru_integration_pending_take.argtypes = [C.POINTER(Command)]
        cls.lib.cfru_integration_pending_take.restype = C.c_uint8
        cls.lib.cfru_integration_battle_begin.argtypes = [C.c_uint8, C.c_uint8]
        cls.lib.cfru_integration_battle_begin.restype = C.c_uint8
        cls.lib.cfru_integration_battle_end.argtypes = [C.c_int]
        cls.lib.cfru_integration_battle_end.restype = C.c_uint8
        cls.shadow = Shadow.in_dll(cls.lib, 'gCfruPendingBattleShadow')

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def setUp(self):
        self.lib.cfru_integration_battle_end(6)
        C.memset(C.addressof(self.shadow), 0, C.sizeof(self.shadow))

    def prepare(self, fmt=0, rule=0):
        self.assertEqual(self.lib.cfru_integration_pending_configure_facility(fmt, rule, 0), 1)
        return self.shadow.command

    def rejected_unchanged(self):
        old = bytes(self.shadow)
        self.assertEqual(self.lib.VegaCircusAdmissionSelectPending(), 0)
        self.assertEqual(bytes(self.shadow), old)

    def test_abi_unchanged(self):
        self.assertEqual((C.sizeof(Command), C.sizeof(Shadow)), (48, 52))
        self.assertEqual(Command.facility_state.offset, 14)

    def test_unprepared_and_ordinary_policy_rejected_without_writes(self):
        self.rejected_unchanged()
        self.assertEqual(self.lib.cfru_integration_pending_configure(1, 0), 1)
        self.rejected_unchanged()

    def test_all_supported_formats_rules_preserve_every_other_byte(self):
        for fmt in range(3):
            for rule in range(8):
                with self.subTest(format=fmt, rule=rule):
                    self.setUp()
                    p = self.prepare(fmt, rule)
                    p.facility_state[8:11] = (17, 29, 31)
                    expected = bytearray(bytes(self.shadow))
                    offset = Shadow.command.offset + Command.facility_state.offset
                    expected[offset:offset+2] = b'\x03\x00'
                    self.assertEqual(self.lib.VegaCircusAdmissionSelectPending(), 1)
                    self.assertEqual(bytes(self.shadow), bytes(expected))

    def test_already_selected_is_idempotent(self):
        self.prepare()
        self.assertEqual(self.lib.VegaCircusAdmissionSelectPending(), 1)
        old = bytes(self.shadow)
        self.assertEqual(self.lib.VegaCircusAdmissionSelectPending(), 1)
        self.assertEqual(bytes(self.shadow), old)

    def test_other_facilities_are_not_hijacked(self):
        for number in (1, 2, 4, 255, 65535):
            self.prepare().facility_state[0] = number
            self.rejected_unchanged()

    def test_each_nonstandard_mechanic_is_rejected(self):
        for mode in range(1, 256):
            self.prepare().mechanic_mode = mode
            self.rejected_unchanged()

    def test_raid_mirage_reserved_and_invalid_enum_metadata_fail_closed(self):
        for field in ('active', 'facility_active', 'ai_profile', 'facility_format',
                      'facility_rule', 'mirage_mask', 'raid_active', 'reserved',
                      'raid_boss_party_index', 'raid_partner_mask',
                      'raid_shield_count', 'raid_turn_limit', 'raid_capture_allowed'):
            with self.subTest(field=field):
                self.setUp()
                setattr(self.prepare(), field, 255)
                self.rejected_unchanged()
        for index in range(6):
            self.setUp()
            self.prepare().mirage_virtual_items[index] = 580
            self.rejected_unchanged()

    def test_inconsistent_facility_fields_rejected(self):
        for index in range(1, 5):
            self.setUp()
            self.prepare().facility_state[index] = 65535
            self.rejected_unchanged()

    def test_taken_transferred_and_active_battle_reject_admission(self):
        self.prepare()
        command = Command()
        self.assertEqual(self.lib.cfru_integration_pending_take(C.byref(command)), 1)
        self.rejected_unchanged()
        self.assertEqual(self.lib.cfru_integration_pending_mark_transferred(), 1)
        self.rejected_unchanged()
        self.assertEqual(self.lib.cfru_integration_battle_begin(1, 5), 1)
        self.rejected_unchanged()

    def test_owner_take_preserves_selected_number_and_next_trial_resets_it(self):
        self.prepare()
        self.assertEqual(self.lib.VegaCircusAdmissionSelectPending(), 1)
        command = Command()
        self.assertEqual(self.lib.cfru_integration_pending_take(C.byref(command)), 1)
        self.assertEqual(command.facility_state[0], 3)
        self.rejected_unchanged()
        self.assertEqual(self.prepare().facility_state[0], 0)


if __name__ == '__main__':
    unittest.main()
