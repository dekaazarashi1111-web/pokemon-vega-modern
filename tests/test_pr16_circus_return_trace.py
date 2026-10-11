"""限定診断をnative受入と混同せず、時間・schema・byte境界を検証。"""
import importlib.util
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('return_trace',ROOT/'scripts/pr16_circus_return_trace.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ReturnTraceTests(unittest.TestCase):
    def rows(self):
        result=[]
        for at in list(range(32))+list(range(60,1201,60)):
            r=dict(frame=17060+at,elapsed=at,dispcnt=0,bldcnt=0,bldalpha=0,bldy=0)
            r.update({k:'00'*size for k,size in dict(main=16,field=8,script=124,fade=32,tasks=640,owner=64).items()});result.append(r)
        return result
    def raw(self,rows):return ''.join('CIRCUS_RETURN '+json.dumps(r)+'\n' for r in rows).encode()
    def test_bounded_trace(self):self.assertEqual(len(m.parse(self.raw(self.rows()))),52)
    def test_short_trace_rejected(self):
        with self.assertRaises(ValueError):m.parse(self.raw(self.rows()[:-1]))
    def test_duplicate_frame_rejected(self):
        rows=self.rows();rows[2]=rows[1].copy()
        with self.assertRaises(ValueError):m.parse(self.raw(rows))
    def test_extra_key_rejected(self):
        rows=self.rows();rows[0]['accepted']=True
        with self.assertRaises(ValueError):m.parse(self.raw(rows))
    def test_wrong_bytes_rejected(self):
        rows=self.rows();rows[-1]['script']='00'
        with self.assertRaises(ValueError):m.parse(self.raw(rows))
    def test_bool_integer_rejected(self):
        rows=self.rows();rows[-1]['bldy']=True
        with self.assertRaises(ValueError):m.parse(self.raw(rows))
if __name__=='__main__':unittest.main()
