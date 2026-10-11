"""新しい転送境界の人工試験。旧Berry限定測定/旧readerは実行しない。"""
import copy
import unittest
from types import SimpleNamespace

import pr16_berry_transfer as m


def symbols_fixture():
    rows = []
    for index, name in enumerate(sorted(m.CODE_NAMES)):
        rows.append('\t'.join(('x', f'{m.BASE + index * 32:08x}', 'x', 'x', name, 'x', 'x', 'x')))
    rows.append('\t'.join(('x', f'{m.BASE + len(m.CODE_NAMES) * 32:08x}', 'x', 'x', 'next', 'x', 'x', 'x')))
    for index, name in enumerate(sorted(m.RAM_NAMES)):
        rows.append('\t'.join(('x', f'{0x03000100 + index * 128:08x}', 'x', 'x', name, 'x', 'x', 'x')))
    return ('\n'.join(rows) + '\n').encode()


class TransferTests(unittest.TestCase):
    def test_actual_interval(self):
        value = m.interval(m.START, m.END)
        self.assertEqual((value['payload_size'], value['rounded_payload_size'], value['tail_beyond_label_bytes']),
                         (13260, 13264, 4))
        self.assertEqual(value['transfer_end_exclusive'], 0x086C7D3C)
        self.assertFalse(value['rounded_tail_reader_proven'])

    def test_exact_aligned(self):
        self.assertEqual(m.interval(m.BASE, m.BASE + 192 + 256)['tail_beyond_label_bytes'], 0)

    def test_round_to_minimum(self):
        self.assertEqual(m.interval(m.BASE, m.BASE + 192 + 241)['rounded_payload_size'], 256)

    def test_below_minimum(self):
        with self.assertRaises(ValueError): m.interval(m.BASE, m.BASE + 192 + 240)

    def test_maximum(self):
        self.assertEqual(m.interval(m.BASE, m.BASE + 192 + 262144)['rounded_payload_size'], 262144)

    def test_over_maximum(self):
        with self.assertRaises(ValueError): m.interval(m.BASE, m.BASE + 192 + 262145)

    def test_boolean_rejected(self):
        with self.assertRaises(ValueError): m.interval(True, m.END)

    def test_float_rejected(self):
        with self.assertRaises(ValueError): m.interval(float(m.START), m.END)

    def test_reversed(self):
        with self.assertRaises(ValueError): m.interval(m.END, m.START)

    def test_unaligned(self):
        with self.assertRaises(ValueError): m.interval(m.START + 1, m.END)

    def test_wrong_header(self):
        with self.assertRaises(ValueError): m.interval(m.START, m.END, 191)

    def test_rom_end_round_overflow(self):
        with self.assertRaises(ValueError): m.interval(0x09FFEF04, 0x0A000000)

    def test_layout_exact(self):
        self.assertEqual(m.layout_checked(m.EXPECTED_LAYOUT), m.EXPECTED_LAYOUT)

    def test_layout_wrong_offset(self):
        layout = dict(m.EXPECTED_LAYOUT, boot_srcp=36)
        with self.assertRaises(ValueError): m.layout_checked(layout)

    def test_layout_boolean(self):
        layout = dict(m.EXPECTED_LAYOUT, size=True)
        with self.assertRaises(ValueError): m.layout_checked(layout)

    def test_layout_extra(self):
        with self.assertRaises(ValueError): m.layout_checked(dict(m.EXPECTED_LAYOUT, extra=0))

    def test_layout_missing(self):
        layout = dict(m.EXPECTED_LAYOUT); del layout['task_data']
        with self.assertRaises(ValueError): m.layout_checked(layout)

    def test_symbols_closed(self):
        result = m.parse_symbols(symbols_fixture())
        self.assertEqual(set(result), m.RAM_NAMES | m.CODE_NAMES)
        self.assertTrue(all(result[n]['end_exclusive'] - result[n]['address'] == 32 for n in m.CODE_NAMES))

    def test_symbols_duplicate(self):
        raw = symbols_fixture()
        with self.assertRaises(ValueError): m.parse_symbols(raw + raw.splitlines()[0] + b'\n')

    def test_symbols_missing(self):
        with self.assertRaises(ValueError): m.parse_symbols(b'\n'.join(symbols_fixture().splitlines()[1:]))

    def test_symbols_wrong_memory(self):
        raw = symbols_fixture().replace(b'03000100', b'080f0000')
        with self.assertRaises(ValueError): m.parse_symbols(raw)

    def test_symbols_unaligned_global(self):
        raw = symbols_fixture().replace(b'03000100', b'03000101')
        with self.assertRaises(ValueError): m.parse_symbols(raw)

    def test_json_deterministic(self):
        self.assertEqual(m.encode({'b': 2, 'a': 1}), m.encode({'a': 1, 'b': 2}))

    def test_no_payload_read_claim(self):
        machine = SimpleNamespace(reads={}, trace=[], calls=[], edges=[], writes=[])
        proof = m.public_profile(machine, 'synthetic', 'RETURNED')
        self.assertEqual(proof['target_bytes_read'], 0)
        self.assertFalse(proof['claims']['target_actual_reader_proven'])
        self.assertFalse(proof['claims']['serial_transfer_observed'])

    def test_payload_read_not_silently_accepted(self):
        machine = SimpleNamespace(reads={(m.START, 1): {'address': m.START, 'size': 1}},
                                  trace=[], calls=[], edges=[], writes=[])
        with self.assertRaises(ValueError): m.public_profile(machine, 'synthetic', 'RETURNED')

    def test_no_claim_mutation(self):
        before = copy.deepcopy(m.CLAIMS)
        machine = SimpleNamespace(reads={}, trace=[], calls=[], edges=[], writes=[])
        proof = m.public_profile(machine, 'synthetic', 'RETURNED')
        proof['claims']['target_actual_reader_proven'] = True
        self.assertEqual(before, m.CLAIMS)


if __name__ == '__main__':
    unittest.main()
