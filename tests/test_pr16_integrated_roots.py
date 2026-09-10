"""Synthetic ROMs test the real unchanged root validator, not native acceptance."""
from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_integrated_domains as m
import run_modernization_stage79_cumulative_mgba as engine

class IntegratedRootContract(unittest.TestCase):
    def config(self):
        cfg=json.loads((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_text())
        cfg['p03_contract']=m.candidate_p03_contract(cfg['p03_contract'])
        return cfg

    def image(self,cfg):
        raw=bytearray(engine.ROM_SIZE)
        args=cfg['p03_contract']['arguments']
        for row in cfg['p03_contract']['root_bindings']:
            address=engine._integer(args[row['site_argument']],'address')
            value=engine._integer(args[row['value_argument']],'value')
            struct.pack_into('<I',raw,address-engine.ROM_BASE,value)
        return raw

    def test_exact_three_argument_projection_preserves_all_other_contracts(self):
        old=json.loads((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_text())['p03_contract']
        before=deepcopy(old);new=m.candidate_p03_contract(old)
        self.assertEqual(old,before)
        self.assertEqual({k for k in old['arguments'] if old['arguments'][k]!=new['arguments'][k]},set(m.P03_RELOCATIONS))
        new['arguments']=old['arguments'];self.assertEqual(new,old)

    def test_wrong_parent_value_or_type_is_not_rebased(self):
        original=json.loads((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_text())['p03_contract']
        for key in m.P03_RELOCATIONS:
            for wrong in (None,True,0,'0x00000000'):
                bad=deepcopy(original);bad['arguments'][key]=wrong
                with self.subTest(key=key,wrong=wrong),self.assertRaises(ValueError):m.candidate_p03_contract(bad)

    def test_real_engine_keeps_all_seven_root_checks(self):
        cfg=self.config();raw=self.image(cfg)
        result=engine._validate_p03(cfg,raw)
        self.assertEqual(result['root_binding_count'],7)
        for row in cfg['p03_contract']['root_bindings']:
            bad=bytearray(raw);off=engine._integer(cfg['p03_contract']['arguments'][row['site_argument']],'site')-engine.ROM_BASE
            bad[off]^=1
            with self.subTest(root=row),self.assertRaisesRegex(RuntimeError,'P03 latest root mismatch'):
                engine._validate_p03(cfg,bad)

    def test_old_pointer_cannot_pass_new_candidate_contract(self):
        cfg=self.config();raw=self.image(cfg)
        for row in cfg['p03_contract']['root_bindings']:
            key=row['value_argument']
            if key not in m.P03_RELOCATIONS:continue
            bad=bytearray(raw);off=engine._integer(cfg['p03_contract']['arguments'][row['site_argument']],'site')-engine.ROM_BASE
            struct.pack_into('<I',bad,off,engine._integer(m.P03_RELOCATIONS[key][0],'old'))
            with self.subTest(root=row),self.assertRaisesRegex(RuntimeError,'P03 latest root mismatch'):
                engine._validate_p03(cfg,bad)

    def test_projection_report_requires_exact_candidate_roots_and_limit(self):
        report={'candidate':{'size':33554432,'sha256':m.native.ROM_SHA},
                'parent':{'size':33554432,'sha256':m.prior.SHA},
                'roots':{'level':'0x095D5FF0','egg':'0x095D9EFC'},
                'allocation':{'allocations':[{'name':'modernization-p07-preserved-egg','size':15396}]}}
        m.validate_root_projection(report)
        for mutation in ('candidate','parent','level','egg','limit'):
            bad=deepcopy(report)
            if mutation in ('candidate','parent'):bad[mutation]['sha256']='0'*64
            elif mutation=='limit':bad['allocation']['allocations'][0]['size']-=2
            else:bad['roots'][mutation]='0x08000000'
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):m.validate_root_projection(bad)

if __name__=='__main__':unittest.main()
