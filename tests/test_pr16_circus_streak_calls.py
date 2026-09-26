"""既存Factoryの2つのconfigure呼出しと固定literalの限定契約。"""
import unittest
from tests.test_pr16_circus_streak_build import b

class InheritedPolicyTests(unittest.TestCase):
    def fixture(self):
        import struct
        addresses = {'configure_facility': 0x09100000, 'generate_rentals': 0x09101000,
                     'generate_trainer': 0x09102000}
        link = {'symbols': {k: {'address': v, 'kind': 'T'} for k, v in addresses.items()}}
        raw = b''.join(struct.pack('<I', addresses[k] | 1) for k in
                      ('configure_facility', 'generate_rentals', 'configure_facility', 'generate_trainer'))
        return raw, link

    def test_two_configure_calls_are_required_not_one(self):
        raw, link = self.fixture()
        policy, counts = b.inherited_policy(raw, link)
        self.assertEqual(counts, {'configure_facility': 2, 'generate_rentals': 1, 'generate_trainer': 1})
        self.assertEqual(policy, {k: v['address'] | 1 for k, v in link['symbols'].items()})

    def test_missing_or_extra_literal_is_rejected(self):
        raw, link = self.fixture()
        for altered in (raw[4:], raw + raw[:4], raw[:-4]):
            with self.assertRaisesRegex(ValueError, 'multiplicity differs'):
                b.inherited_policy(altered, link)

    def test_unknown_and_non_thumb_symbols_are_rejected(self):
        import copy
        raw, link = self.fixture()
        for field, value in (('kind', 'D'), ('address', 0x09100001), ('address', 0x02000000)):
            bad = copy.deepcopy(link)
            bad['symbols']['configure_facility'][field] = value
            with self.assertRaises(ValueError): b.inherited_policy(raw, bad)
        bad = copy.deepcopy(link)
        bad['symbols']['unknown'] = bad['symbols']['configure_facility']
        with self.assertRaises(ValueError): b.inherited_policy(raw, bad)

if __name__ == "__main__": unittest.main()
