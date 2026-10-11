"""文字列境界とZ/技分類の証拠区分。nativeを起動しない。"""
from pathlib import Path
import sys
import unittest
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from pr16_candidate_wiki_inputs import BASE, Rom
from pr16_candidate_wiki_details import text_at, locate


class CandidateWikiDetailsTest(unittest.TestCase):
    def test_text_terminator_and_controls(self):
        row=text_at(Rom(bytes([1,254,2,247,255])),BASE,{'1':'あ','2':'い'})
        self.assertEqual(row['text'],'あ\nい<0xF7>')
        self.assertEqual(row['size'],5)
        self.assertEqual(row['evidence'],'EXACT_CANDIDATE_ROM')

    def test_unterminated_text_and_bounds(self):
        for raw,limit in [(b'\1\1',2),(b'\1',2)]:
            with self.assertRaises(ValueError):text_at(Rom(raw),BASE,{},limit)

    def test_no_match_is_not_rom_proof(self):
        row=locate(bytes(20),b'abcdefgh','fixture')
        self.assertEqual(row['matches'],[])
        self.assertEqual(row['evidence'],'GENERATED_CANONICAL')

    def test_matching_table_does_not_claim_consumer_acceptance(self):
        row=locate(b'abcdefghXabcdefgh',b'abcdefgh','fixture')
        self.assertEqual(row['matches'],['0x08000000','0x08000009'])
        self.assertEqual(row['consumer_proof'],'DEFERRED_AUDIT')
        self.assertTrue(row['byte_match_only'])

    def test_short_signature_rejected(self):
        with self.assertRaises(ValueError):locate(bytes(20),b'xx','fixture')


if __name__=='__main__':unittest.main()
