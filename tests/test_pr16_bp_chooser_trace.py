import unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_bp_chooser_trace as trace
import pr16_bp_trial_native as native
class ChooserTraceTests(unittest.TestCase):
    def original(self):return (ROOT/native.control.SOURCE).read_text()
    def test_exact_reversible_source_changes(self):
        original=self.original();text,changes=trace.instrument(original,native.transform)
        self.assertEqual(len(changes),2)
        for change in reversed(changes):
            self.assertEqual(text.count(change['after']),1)
            text=text.replace(change['after'],change['before'],1)
        self.assertEqual(text,original)
    def test_no_host_or_key_writes(self):
        for token in ('write8(', 'write16(', 'write32(', 'setKeys(', 'call_preserving(', 'b_frame(', 'b_press(', 'busWrite', 'rawWrite', 'writeRegister'):
            self.assertNotIn(token,trace.C_TRACE)
    def test_pointer_read_bounded_to_rom(self):
        self.assertIn('pointer>=0x08000000U && pointer<=0x09FFFFA0U',trace.C_TRACE)
        self.assertIn('pointer,96U',trace.C_TRACE)
    def test_context_anchor_is_not_legacy_incorrect_address(self):
        self.assertIn('0x03000EB0U',trace.C_TRACE);self.assertNotIn('B_CONTEXT',trace.C_TRACE)
    def test_only_seven_sampling_points(self):
        text,changes=trace.instrument(self.original(),native.transform)
        added=changes[1]['after'][len(changes[1]['before']):]
        self.assertEqual(added.count('f=='),7)
        self.assertEqual(text.count('for(unsigned f=0;f<12000U;++f)'),1)
    def test_wrong_template_rejected(self):
        with self.assertRaises(ValueError):trace.instrument('wrong controller',native.transform)
