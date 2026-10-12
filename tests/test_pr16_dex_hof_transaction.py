"""合成保存形式だけの新規host試験。実ROM/旧native/入力saveを使用しない。"""
import hashlib
import pathlib
import struct
import sys
import unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_dex_hof_transaction as t

NEW_HOF = bytes((i * 19 + 29) % 251 for i in range(t.HOF_PAYLOAD))
NEW_MAIN = bytes((i * 17 + 7) % 251 for i in range(t.MAIN_PAYLOAD))
MEASUREMENTS = {}


def key(value):
    return value['binding'], value['counter'], value['main'], value['hof']


class TransactionTests(unittest.TestCase):
    def test_01_actual_capacity_rejected_before_io(self):
        with self.assertRaisesRegex(t.ContractError, 'capacity'):
            t.Flash(t.Layout(32 * t.SECTOR))
        self.assertEqual(34 * t.SECTOR - 32 * t.SECTOR, 8192)
        with self.assertRaisesRegex(t.ContractError, 'overlap'):
            t.Layout(34 * t.SECTOR, hof=(28 * t.SECTOR, 30 * t.SECTOR)).validate()
        with self.assertRaises(t.ContractError):
            t.Layout(34 * t.SECTOR, hof=(28 * t.SECTOR,) * 2).validate()
        with self.assertRaises(t.ContractError):
            t.Layout(34 * t.SECTOR, main=(1, 14 * t.SECTOR)).validate()

    def test_02_exact_roundtrip_and_complete_record_integrity(self):
        f = t.fixture(); original = t.recover(f)
        self.assertEqual(original['counter'], 101)
        for kind, addr, size in [(b'MFT1', 0, t.MAIN_BANK), (b'HFT1', f.layout.hof[0], t.HOF_BANK)]:
            data = bytes(f.data[addr:addr + size])
            self.assertIsNotNone(t.parse(data, kind))
            for offset in (0, 4, 6, 8, 16, 48, 52, 56, 60, 64, size - 2, size - 1):
                corrupted = bytearray(data); corrupted[offset] ^= 1
                self.assertIsNone(t.parse(corrupted, kind), (kind, offset))
        for epoch, digest in [(0, b'x' * 32), (t.MAX_EPOCH + 1, b'x' * 32), (1, b'x' * 31)]:
            with self.assertRaises(t.ContractError): t.Binding(epoch, digest)

    def test_03_every_durable_byte_boundary_recovers_exact_old_or_new(self):
        f = t.fixture(); old = t.recover(f); before = bytes(f.data)
        newkey = (t.Binding(2, hashlib.sha256(NEW_HOF).digest()), 102, NEW_MAIN, NEW_HOF)
        points = {'program': 0, 'before_erase': 0, 'after_erase': 0, 'old': 0, 'new': 0}
        def observe(flash, kind, address):
            # selectorは永続bytesと固定layoutだけから再実行。save()のlive local変数を参照しない。
            got = key(t.recover(flash))
            self.assertIn(got, (key(old), newkey))
            points['new' if got == newkey else 'old'] += 1; points[kind] += 1
        f.observe = observe
        self.assertEqual(t.save(f, NEW_MAIN, NEW_HOF), 'COMMITTED')
        self.assertEqual(key(t.recover(f)), newkey)
        self.assertEqual(f.data[:t.MAIN_BANK], before[:t.MAIN_BANK])
        a = f.layout.hof[0]; self.assertEqual(f.data[a:a + t.HOF_BANK], before[a:a + t.HOF_BANK])
        a, size = f.layout.auxiliary; self.assertEqual(f.data[a:a + size], before[a:a + size])
        self.assertEqual(points['before_erase'], 16); self.assertEqual(points['after_erase'], 16)
        self.assertEqual(points['new'], 1)
        self.assertGreater(points['program'], 65000)
        MEASUREMENTS['blank_shadow_durable_boundaries'] = dict(points, total=f.operations)

    def test_04_reported_and_silent_program_faults(self):
        cases = 0
        for label, bank, size in [('hof', 32 * t.SECTOR, t.HOF_BANK), ('main', 14 * t.SECTOR, t.MAIN_BANK)]:
            for offset in (0, 8, 16, 60, 64, 1000, size - 1):
                for mode in ('raise', 'omit'):
                    f = t.fixture(); old = key(t.recover(f)); target = bank + offset
                    f.fault = lambda kind, addr, target=target, mode=mode: mode if kind == 'program' and addr == target else None
                    self.assertEqual(t.save(f, NEW_MAIN, NEW_HOF), 'OLD_GENERATION_RETAINED', (label, offset, mode))
                    self.assertEqual(key(t.recover(f)), old); cases += 1
        MEASUREMENTS['program_fault_cases'] = cases

    def test_05_erase_failure_and_stale_shadow_readback(self):
        cases = 0
        for address in (32 * t.SECTOR, 33 * t.SECTOR, 14 * t.SECTOR, 27 * t.SECTOR):
            for mode in ('raise', 'omit'):
                f = t.fixture(); old = key(t.recover(f))
                f.data[address:address + t.SECTOR] = b'\0' * t.SECTOR
                f.fault = lambda kind, addr, address=address, mode=mode: mode if kind == 'erase' and addr == address else None
                self.assertEqual(t.save(f, NEW_MAIN, NEW_HOF), 'OLD_GENERATION_RETAINED')
                self.assertEqual(key(t.recover(f)), old); cases += 1
        MEASUREMENTS['erase_fault_cases'] = cases

    def test_06_last_commit_byte_truthful_after_error(self):
        for bank, size, expected in [(32 * t.SECTOR, t.HOF_BANK, 'OLD_GENERATION_RETAINED'), (14 * t.SECTOR, t.MAIN_BANK, 'COMMITTED_AFTER_IO_ERROR')]:
            f = t.fixture(); end = bank + size - 1
            f.fault = lambda kind, addr: 'after_raise' if kind == 'program' and addr == end else None
            self.assertEqual(t.save(f, NEW_MAIN, NEW_HOF), expected)
            self.assertEqual(t.recover(f)['counter'], 102 if bank == 14 * t.SECTOR else 101)

    def test_07_orphan_never_becomes_authoritative_after_normal_saves(self):
        f = t.fixture(); old = t.recover(f); target = 14 * t.SECTOR
        f.fault = lambda kind, addr: 'raise' if kind == 'erase' and addr == target else None
        self.assertEqual(t.save(f, NEW_MAIN, NEW_HOF), 'OLD_GENERATION_RETAINED')
        self.assertIsNotNone(t.parse(f.data[32 * t.SECTOR:34 * t.SECTOR], b'HFT1'))
        f.fault = None
        for _ in range(4):
            self.assertEqual(t.save(f, NEW_MAIN), 'COMMITTED')
            got = t.recover(f); self.assertEqual((got['binding'], got['hof']), (old['binding'], old['hof']))
        self.assertEqual(t.recover(f)['counter'], 105)
        self.assertEqual(t.save(f, NEW_MAIN, NEW_HOF), 'COMMITTED')
        self.assertEqual(t.recover(f)['binding'].epoch, 2)

    def test_08_counter_wrap_and_epoch_exhaustion(self):
        f = t.fixture(counter=0xffffffff)
        self.assertEqual(t.save(f, NEW_MAIN, NEW_HOF), 'COMMITTED')
        self.assertEqual(t.recover(f)['counter'], 0)
        f = t.fixture(epoch=t.MAX_EPOCH); before = bytes(f.data)
        with self.assertRaises(t.ContractError): t.save(f, NEW_MAIN, NEW_HOF)
        self.assertEqual(f.operations, 0); self.assertEqual(f.data, before)
        self.assertEqual(t.save(f, NEW_MAIN), 'COMMITTED')
        self.assertEqual(t.recover(f)['binding'].epoch, t.MAX_EPOCH)

    def test_09_main_counter_ambiguity_fails_closed(self):
        for counter in (101, (101 + 0x80000000) & 0xffffffff):
            f = t.fixture(); old = t.recover(f)
            image = t.encode(b'MFT1', old['binding'], counter, NEW_MAIN, t.MAIN_BANK)
            f.data[t.MAIN_BANK:2 * t.MAIN_BANK] = image
            with self.assertRaises(t.ContractError): t.recover(f)

    def test_10_same_epoch_wrong_payload_and_absent_bound_hof_rejected(self):
        f = t.fixture(); old = t.recover(f)
        other = t.Binding(old['binding'].epoch, hashlib.sha256(NEW_HOF).digest())
        a = f.layout.hof[0]; f.data[a:a + t.HOF_BANK] = t.encode(b'HFT1', other, 1, NEW_HOF, t.HOF_BANK)
        with self.assertRaisesRegex(t.ContractError, 'exact durable'): t.recover(f)
        with self.assertRaises(t.ContractError): t.encode(b'HFT1', old['binding'], 101, NEW_HOF, t.HOF_BANK)

    def test_11_invalid_input_has_zero_io(self):
        for main, hof in [(b'', NEW_HOF), (NEW_MAIN, b''), (NEW_MAIN[:-1], None)]:
            f = t.fixture(); before = bytes(f.data)
            with self.assertRaises(t.ContractError): t.save(f, main, hof)
            self.assertEqual(f.operations, 0); self.assertEqual(f.data, before)

    def test_12_interrupted_real_erase_call_of_every_reused_target_sector(self):
        seed = t.fixture(); self.assertEqual(t.save(seed, NEW_MAIN, NEW_HOF), 'COMMITTED')
        snapshot = bytes(seed.data); old = key(t.recover(seed)); cases = 0
        for sector in (*range(0, 14), 28, 29):
            for cut in (0, 1, 127, 2048, 4095, 4096):
                f = t.Flash(seed.layout); f.data[:] = snapshot; target = sector * t.SECTOR
                f.fault = lambda kind, addr, target=target, cut=cut: 'partial:' + str(cut) if kind == 'erase' and addr == target else None
                with self.assertRaises(t.PowerCut): t.save(f, NEW_MAIN, NEW_HOF)
                self.assertEqual(key(t.recover(f)), old)
                self.assertEqual(f.data[target:target + cut], b'\xff' * cut)
                f.fault = None
                self.assertEqual(t.save(f, NEW_MAIN, NEW_HOF), 'COMMITTED'); cases += 1
        MEASUREMENTS['reused_partial_erase_and_restart_cases'] = cases

    def test_13_power_loss_has_no_in_process_recovery_and_retry_is_safe(self):
        cases = 0
        for point in (1, 4, 32, 1000, 8000, 8200, 32000, 65000):
            f = t.fixture(); old = key(t.recover(f))
            def observe(flash, kind, address):
                if flash.operations == point: raise t.PowerCut()
            f.observe = observe
            with self.assertRaises(t.PowerCut): t.save(f, NEW_MAIN, NEW_HOF)
            self.assertEqual(f.operations, point); self.assertEqual(key(t.recover(f)), old)
            f.observe = None
            self.assertEqual(t.save(f, NEW_MAIN, NEW_HOF), 'COMMITTED'); cases += 1
        MEASUREMENTS['power_loss_restart_cases'] = cases

    def test_14_existing_shadow_commit_without_main_commit_is_not_success(self):
        f = t.fixture(); old = t.recover(f)
        pending = t.Binding(2, hashlib.sha256(NEW_HOF).digest())
        a = f.layout.hof[1]; f.data[a:a + t.HOF_BANK] = t.encode(b'HFT1', pending, 102, NEW_HOF, t.HOF_BANK)
        self.assertEqual(key(t.recover(f)), key(old))
        self.assertEqual(t.save(f, NEW_MAIN, NEW_HOF), 'COMMITTED')
        self.assertEqual(t.recover(f)['binding'], pending)

    def test_15_every_byte_boundary_with_reused_valid_banks(self):
        f = t.fixture(); self.assertEqual(t.save(f, NEW_MAIN, NEW_HOF), 'COMMITTED')
        old = t.recover(f); before = bytes(f.data)
        body = bytes(reversed(NEW_HOF)); main = bytes(reversed(NEW_MAIN))
        newkey = (t.Binding(3, hashlib.sha256(body).digest()), 103, main, body)
        points = {'program': 0, 'before_erase': 0, 'after_erase': 0, 'old': 0, 'new': 0}
        f.operations = 0
        def observe(flash, kind, address):
            got = key(t.recover(flash)); self.assertIn(got, (key(old), newkey))
            points['new' if got == newkey else 'old'] += 1; points[kind] += 1
        f.observe = observe
        self.assertEqual(t.save(f, main, body), 'COMMITTED')
        self.assertEqual(points['new'], 1)
        self.assertEqual(f.data[t.MAIN_BANK:2 * t.MAIN_BANK], before[t.MAIN_BANK:2 * t.MAIN_BANK])
        a = f.layout.hof[1]; self.assertEqual(f.data[a:a + t.HOF_BANK], before[a:a + t.HOF_BANK])
        a, size = f.layout.auxiliary; self.assertEqual(f.data[a:a + size], before[a:a + size])
        MEASUREMENTS['reused_valid_bank_durable_boundaries'] = dict(points, total=f.operations)

    def test_16_unknown_record_kind_is_closed(self):
        f = t.fixture(); data = bytearray(f.data[:t.MAIN_BANK]); data[:4] = b'XYZ1'
        struct.pack_into('<I', data, 60, t.crc(data[:60]))
        self.assertIsNone(t.parse(data, b'XYZ1'))

    def test_17_powercut_immediately_after_main_commit_and_next_save(self):
        f = t.fixture(); target = 2 * t.MAIN_BANK - 1
        def observe(flash, kind, address):
            if kind == 'program' and address == target: raise t.PowerCut()
        f.observe = observe
        with self.assertRaises(t.PowerCut): t.save(f, NEW_MAIN, NEW_HOF)
        f.observe = None; self.assertEqual(t.recover(f)['counter'], 102)
        self.assertEqual(t.recover(f)['hof'], NEW_HOF)
        self.assertEqual(t.save(f, NEW_MAIN), 'COMMITTED')
        self.assertEqual(t.recover(f)['counter'], 103)

    def test_18_failed_orphan_then_different_hof_retry(self):
        f = t.fixture(); f.fault = lambda kind, addr: 'raise' if kind == 'erase' and addr == t.MAIN_BANK else None
        self.assertEqual(t.save(f, NEW_MAIN, NEW_HOF), 'OLD_GENERATION_RETAINED')
        f.fault = None; different = bytes(reversed(NEW_HOF))
        self.assertEqual(t.save(f, NEW_MAIN, different), 'COMMITTED')
        self.assertEqual(t.recover(f)['hof'], different)
        self.assertNotEqual(t.recover(f)['binding'].digest, hashlib.sha256(NEW_HOF).digest())

    def test_19_normal_save_all_boundaries_through_counter_wrap(self):
        f = t.fixture(counter=0xffffffff); old = t.recover(f); hof_before = bytes(f.data[28 * t.SECTOR:])
        newkey = (old['binding'], 0, NEW_MAIN, old['hof']); points = {'old': 0, 'new': 0}
        def observe(flash, kind, address):
            got = key(t.recover(flash)); self.assertIn(got, (key(old), newkey))
            points['new' if got == newkey else 'old'] += 1
        f.observe = observe
        self.assertEqual(t.save(f, NEW_MAIN), 'COMMITTED')
        self.assertEqual(points['new'], 1)
        self.assertEqual(f.data[28 * t.SECTOR:], hof_before)
        MEASUREMENTS['normal_save_wrap_durable_boundaries'] = dict(points, total=f.operations)

    def test_20_current_source_bound_capacity_audit(self):
        import pr16_dex_hof_capacity as capacity
        result = capacity.audit()
        self.assertEqual(result['main_tail_potential_bytes_per_bank'], 1740)
        self.assertEqual(result['sector31_remaining_candidate_bytes'], 578)
        self.assertEqual(result['current_scheduler_free_bytes'], 186)
        self.assertEqual(result['simple_dual_hof_deficit_bytes'], 8192)
        self.assertFalse(result['runtime_cross_store_atomicity'])

    def test_21_closed_publication_contract(self):
        import pr16_dex_publication as publication
        publication.contract(ROOT, '.github/workflows/pr16-dex-hof-generation.yml', ROOT / 'public-dex-hof-generation', 'pr16-dex-hof-generation-text-only', 'scripts/pr16_dex_hof_generation_actions.py')


if __name__ == '__main__':
    unittest.main()
