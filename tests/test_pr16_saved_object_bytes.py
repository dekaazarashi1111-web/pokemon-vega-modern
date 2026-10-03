"""objdump OBJECT定数表の読み落とし回帰。未影響の既受入契約は実行しない。"""
import unittest
import pr16_saved_recipe as s


class ObjectBytesTests(unittest.TestCase):
    TEXT = ' 9ff0000:\tb510      \tpush {r4, lr}\n 9ff0002:\t1234      \tmov\n 9ff0004:\t01060400 05070302                       ........\n'
    RAW = bytes.fromhex('10b534120004060102030705')

    def test_instruction_and_object_words_are_complete(self):
        self.assertEqual(s.disassembly_bytes(self.TEXT,0x9ff0000,s.identity(self.RAW)),self.RAW)
        with self.assertRaises(s.RecipeError):
            s.disassembly_bytes(self.TEXT,0x9ff0000,s.identity(self.RAW[:4]))

    def test_duplicate_malformed_and_missing_object_words_fail_closed(self):
        for bad in [self.TEXT+self.TEXT.splitlines()[-1]+'\n',
                    self.TEXT.replace('01060400','xxxxxxxx'),
                    self.TEXT.replace('9ff0004','9ff0008')]:
            with self.subTest(text=bad),self.assertRaises(s.RecipeError):
                s.disassembly_bytes(bad,0x9ff0000,s.identity(self.RAW))

if __name__=='__main__':unittest.main()
