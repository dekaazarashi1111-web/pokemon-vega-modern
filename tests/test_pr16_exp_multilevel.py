"""低レベルEXP fixtureのHP/max HP不整合を拒否する新規試験。"""
import struct
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_exp_multilevel as x


def raw(hp=32,maximum=32,level=18):
    output=[]
    for label,lev,h,m in [('fixture',10,hp,maximum),('returned',level,50,50),('saved',level,50,50),('continued',level,50,50)]:
        data=bytearray(100);data[84]=lev;struct.pack_into('<HH',data,86,h,m)
        output.append(f'NATURAL_PARTY stage={label} counter={2 if label in ("fixture","returned") else 3} hex={data.hex()}\n')
    return ''.join(output).encode()


class HealthTests(unittest.TestCase):
    def test_native_health_across_growth(self):self.assertEqual(x.health(raw())['phases']['returned']['level'],18)
    def test_inflated_999_rejected(self):
        with self.assertRaises(ValueError):x.health(raw(999,999))
    def test_hp_above_maximum_rejected(self):
        with self.assertRaises(ValueError):x.health(raw(1001,34))
    def test_fainted_fixture_rejected(self):
        with self.assertRaises(ValueError):x.health(raw(0,32))
    def test_fixture_not_full_rejected(self):
        with self.assertRaises(ValueError):x.health(raw(31,32))
    def test_single_level_rejected(self):
        with self.assertRaises(ValueError):x.health(raw(level=11))
    def test_missing_continue_rejected(self):
        with self.assertRaises(ValueError):x.health(raw().replace(b'stage=continued',b'stage=missing'))
    def test_native_fixture_writes_only_combat_stats(self):
        source=(x.x.ROOT/x.x.C).read_text()
        self.assertIn('offset=90;offset<=98',source)
        self.assertIn('"native EXP health bounds"',source)
        self.assertIn('!log_problem_count',source)


if __name__=='__main__':unittest.main()
