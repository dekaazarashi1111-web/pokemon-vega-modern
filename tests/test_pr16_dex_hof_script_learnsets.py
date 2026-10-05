"""同じ現0641 bytesを親ActionsのFIXTUREから受ける有限窓反証。"""
import copy
import json
import pathlib
import struct
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
HERE=pathlib.Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'scripts'),str(HERE)]
import pr16_dex_hof_script_learnsets as v

FIXTURE=None
RAW=REVIEW=SOURCES=None


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global RAW,REVIEW,SOURCES
        if FIXTURE is None:
            raise RuntimeError('same-current-candidate fixture must be bound by scoped Actions')
        RAW,REVIEW,SOURCES=FIXTURE

    def check(self,review=None,raw=None,sources=None):
        return v._regions(RAW if raw is None else raw,
                          REVIEW if review is None else review,ROOT,
                          SOURCES if sources is None else sources)

    def reject_review(self,change):
        r=copy.deepcopy(REVIEW);change(r)
        with self.assertRaises(ValueError):self.check(r)

    def test_exact_nine_source_numeric_boundaries(self):
        regions,proof=self.check()
        self.assertEqual(len(regions),9)
        self.assertEqual(len(proof['root_role_windows']),18)
        self.assertTrue(proof['historical_typing_only'])
        for key in ('current_runtime_reachability_claimed','current_reference_absence_claimed',
                    'retirement_completeness_claimed','donor_eligible'):
            self.assertFalse(proof[key])

    def test_wrong_rom_never_current_acceptance(self):
        with self.assertRaisesRegex(ValueError,'current whole candidate'):
            v.regions(b'not-current',REVIEW,ROOT,SOURCES)

    def test_wrong_target_current(self):
        self.reject_review(lambda r:r['required_candidate'].update(sha256='0'*64))

    def test_modern_table_not_old_root(self):
        self.reject_review(lambda r:r['historical_root_table'].update(address=0x09596F00))

    def test_wrong_root_count(self):
        self.reject_review(lambda r:r['historical_root_table'].update(count=1671))

    def test_wrong_root_digest(self):
        self.reject_review(lambda r:r['historical_root_table'].update(sha256='0'*64))

    def test_missing_left_source_selector(self):
        self.reject_review(lambda r:r['sequences'].pop('1344'))

    def test_wrong_species_pointer_offset(self):
        self.reject_review(lambda r:r['sequences']['1344']['pointer'].update(address=v.ROOT_ADDRESS+1343*4))

    def test_source_symbol_name_not_evidence(self):
        self.reject_review(lambda r:r['sequences']['1344'].update(array_symbol='sOtherLearnset'))

    def test_wrong_public_source_line(self):
        self.reject_review(lambda r:r['sequences']['1344'].update(source_line=1))

    def test_wrong_scalar_extent(self):
        self.reject_review(lambda r:r['sequences']['1344'].update(row_count=13))

    def test_wrong_source_receipt(self):
        self.reject_review(lambda r:r['sources'][v.DPE+'src/Learnsets.c'].update(sha256='0'*64))

    def test_source_code_drift(self):
        s=dict(SOURCES);s[v.DPE+'src/Learnsets.c']+=b'\n'
        with self.assertRaisesRegex(ValueError,'whole pinned source'):self.check(sources=s)

    def test_wrong_pair_is_not_adjacent_numeric_proof(self):
        self.reject_review(lambda r:r['boundaries'][0].update(right_species_id=1181))

    def test_expanded_boundary_may_capture_untyped_byte(self):
        self.reject_review(lambda r:r['boundaries'][0]['typed_window'].update(size=7))

    def test_hit_must_keep_original_classification(self):
        self.reject_review(lambda r:r['boundaries'][0]['hit'].update(accepted=True))

    def test_current_sequence_mutation_even_with_resigned_review(self):
        r=copy.deepcopy(REVIEW);raw=bytearray(RAW)
        span=r['sequences']['1344']['span'];at=span['address']-v.d.BASE
        raw[at]^=1;span.update(v.identity(raw[at:at+span['size']]))
        with self.assertRaisesRegex(ValueError,'equals actual public source'):self.check(r,raw)

    def test_mutated_pointer_and_resigned_root_still_reject(self):
        r=copy.deepcopy(REVIEW);raw=bytearray(RAW)
        row=r['sequences']['1344'];p=row['pointer'];address=r['sequences']['1343']['span']['address']
        at=p['address']-v.d.BASE;struct.pack_into('<I',raw,at,address)
        p.update(v.identity(raw[at:at+4]),target=address)
        table=r['historical_root_table'];at=table['address']-v.d.BASE
        table.update(v.identity(raw[at:at+table['size']]))
        with self.assertRaisesRegex(ValueError,'actual exact species-indexed'):self.check(r,raw)

    def test_initializer_rejects_pointer_expression(self):
        with self.assertRaises(ValueError):v.parse_array('LEVEL_UP_MOVE(1, (u32)gPointer), LEVEL_UP_END',{})

    def test_initializer_rejects_trailing_fragment(self):
        with self.assertRaises(ValueError):v.parse_array('LEVEL_UP_END, 1',{})

    def test_initializer_rejects_missing_terminator(self):
        with self.assertRaises(ValueError):v.parse_array('LEVEL_UP_MOVE(1, MOVE_A)',{'MOVE_A':1})

    def test_initializer_rejects_early_terminator(self):
        with self.assertRaises(ValueError):v.parse_array('LEVEL_UP_END, LEVEL_UP_MOVE(1, MOVE_A)',{'MOVE_A':1})

    def test_initializer_rejects_move_outside_u16(self):
        with self.assertRaises(ValueError):v.parse_array('LEVEL_UP_MOVE(1, MOVE_A), LEVEL_UP_END',{'MOVE_A':65536})

    def test_initializer_rejects_level_outside_domain(self):
        with self.assertRaises(ValueError):v.parse_array('LEVEL_UP_MOVE(101, MOVE_A), LEVEL_UP_END',{'MOVE_A':1})

    def test_initializer_exact_u16_u8_and_terminal(self):
        raw,count=v.parse_array('LEVEL_UP_MOVE(0, MOVE_A), LEVEL_UP_END',{'MOVE_A':513})
        self.assertEqual(raw,struct.pack('<HBHB',513,0,0,255));self.assertEqual(count,1)

if __name__=='__main__':unittest.main(verbosity=2)
