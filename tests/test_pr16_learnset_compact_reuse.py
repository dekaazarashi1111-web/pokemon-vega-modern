"""ARM専用compiler-option変更の限定試験。旧codec/native試験は呼ばない。"""
import unittest
from scripts.pr16_learnset_compact_reuse import compile_args


class CompileArgsTests(unittest.TestCase):
    def test_arm_compile(self):
        self.assertEqual(compile_args(['arm-none-eabi-gcc','-c','x.c']),
                         ['arm-none-eabi-gcc','-c','x.c','-fno-jump-tables'])
    def test_link_unchanged(self):
        args=['arm-none-eabi-gcc','-nostdlib','x.o','-o','x.elf']
        self.assertEqual(compile_args(args),args)
    def test_host_compile_unchanged(self):
        args=['cc','-c','x.c']; self.assertEqual(compile_args(args),args)
    def test_idempotent(self):
        args=['arm-none-eabi-gcc','-c','x.c','-fno-jump-tables']
        self.assertEqual(compile_args(args),args)
    def test_input_unchanged(self):
        args=['arm-none-eabi-gcc','-c','x.c']; before=args.copy()
        result=compile_args(args); self.assertEqual(args,before); self.assertIsNot(result,args)
    def test_empty_unchanged(self):
        self.assertEqual(compile_args([]),[])


if __name__ == '__main__': unittest.main()
