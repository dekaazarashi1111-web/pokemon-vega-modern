"""Only new allocator-transfer, address, veneer and publication boundaries."""
import copy,json,os,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_placement as p

def fixture():
    payload=bytearray(384+24*4);symbols={}
    for i,name in enumerate(p.EXPORTS):
        a=p.BASE+384+i*4
        symbols[name]=dict(address=a,size=4,kind='T')
        symbols['DexEntry_'+name]=dict(address=p.BASE+i*16,size=16,kind='T')
        struct.pack_into('<6HI',payload,i*16,0xB408,0x4B02,0x469C,0xBC08,0x4760,0x46C0,a|1)
    return bytes(payload),symbols

class Veneers(unittest.TestCase):
    def test_exact_24_slots(self):
        b,s=fixture();self.assertEqual(len(p.validate_link(b,s)),24)
    def test_wrong_vma_rejected(self):
        b,s=fixture();s[p.EXPORTS[0]]['address']=0x08000100
        with self.assertRaises(ValueError):p.validate_link(b,s)
    def test_preserved_r3_instruction_required(self):
        b,s=fixture();b=bytearray(b);b[0]^=1
        with self.assertRaisesRegex(ValueError,'register-preserving'):p.validate_link(bytes(b),s)
    def test_stack_restore_instruction_required(self):
        b,s=fixture();b=bytearray(b);b[6]^=1
        with self.assertRaises(ValueError):p.validate_link(bytes(b),s)
    def test_thumb_literal_required(self):
        b,s=fixture();b=bytearray(b);b[12]^=1
        with self.assertRaisesRegex(ValueError,'Thumb destination'):p.validate_link(bytes(b),s)
    def test_wrong_implementation_literal_rejected(self):
        b,s=fixture();b=bytearray(b);b[13]^=1
        with self.assertRaises(ValueError):p.validate_link(bytes(b),s)
    def test_entry_slot_shift_rejected(self):
        b,s=fixture();s['DexEntry_'+p.EXPORTS[0]]['address']+=2
        with self.assertRaisesRegex(ValueError,'fixed ABI'):p.validate_link(b,s)
    def test_missing_export_rejected(self):
        b,s=fixture();s.pop(p.EXPORTS[7])
        with self.assertRaises(ValueError):p.validate_link(b,s)
    def test_non_code_export_rejected(self):
        b,s=fixture();s[p.EXPORTS[7]]['kind']='R'
        with self.assertRaises(ValueError):p.validate_link(b,s)
    def test_zero_function_rejected(self):
        b,s=fixture();s[p.EXPORTS[0]]['size']=0
        with self.assertRaises(ValueError):p.validate_link(b,s)
    def test_function_overrun_rejected(self):
        b,s=fixture();s[p.EXPORTS[-1]]['size']=100
        with self.assertRaises(ValueError):p.validate_link(b,s)
    def test_payload_overrun_rejected(self):
        b,s=fixture()
        with self.assertRaises(ValueError):p.validate_link(b+b'\0'*6484,s)
    def test_payload_header_only_rejected(self):
        b,s=fixture()
        with self.assertRaises(ValueError):p.validate_link(b[:384],s)
    def test_mutable_linker_symbols_rejected(self):
        for kind in 'BbCcDdGgSs':
            with self.assertRaises(ValueError):p.parse_symbols('09fc1000 00000004 '+kind+' variable')
    def test_assembly_has_24_tail_calls(self):
        a=p.assembly();self.assertEqual(a.count('push {r3}'),24);self.assertEqual(a.count('pop {r3}'),24);self.assertEqual(a.count('bx ip'),24)
    def test_linker_retains_all_apis(self):
        a=p.linker_script();self.assertIn(hex(p.BASE),a);self.assertIn('KEEP(*(.text*))',a);self.assertIn('KEEP(*(.dex_exports))',a)

class Allocation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=Path(os.environ['VEGA_DEX_ROM_PATH']).read_bytes();cls.source=p.allocation_source()
        cls.after=cls.raw[:p.lease.START]+b'PLACEMENT-UNIT'+cls.raw[p.lease.START+14:]
    def test_exact_canonical_report(self):self.assertEqual(p.rebuild_allocation(self.source),self.source)
    def test_transfer_replaces_only_parent(self):
        out=p.transfer_allocation(self.source,self.raw,self.after)
        self.assertEqual(out['summaries'],self.source['summaries']);self.assertEqual(len(out['allocations']),107)
        changed=[(a,b)for a,b in zip(self.source['allocations'],out['allocations'])if a!=b]
        self.assertEqual(len(changed),1);a,b=changed[0];self.assertEqual((b['start'],b['end_exclusive'],b['size']),(a['start'],a['end_exclusive'],6484));self.assertEqual(b['owner'],p.OWNER)
    def test_input_report_is_immutable(self):
        old=copy.deepcopy(self.source);p.transfer_allocation(self.source,self.raw,self.after);self.assertEqual(old,self.source)
    def test_stale_allocation_rejected(self):
        s=copy.deepcopy(self.source);s['allocations'][0]['owner']='UNKNOWN'
        with self.assertRaisesRegex(ValueError,'exact latest'):p.transfer_allocation(s,self.raw,self.after)
    def test_duplicate_owner_rejected(self):
        s=copy.deepcopy(self.source);s['allocations'].append(s['allocations'][19])
        with self.assertRaises(ValueError):p.transfer_allocation(s,self.raw,self.after)
    def test_lost_owner_rejected(self):
        s=copy.deepcopy(self.source);s['allocations'].pop()
        with self.assertRaises(ValueError):p.transfer_allocation(s,self.raw,self.after)
    def test_changed_preimage_rejected(self):
        b=bytearray(self.raw);b[p.lease.START]^=1
        with self.assertRaisesRegex(ValueError,'whole donor'):p.transfer_allocation(self.source,b,self.after)
    def test_truncated_rom_rejected(self):
        with self.assertRaises(ValueError):p.transfer_allocation(self.source,self.raw[:-1],self.after)
    def test_publication_is_guarded(self):
        wf=(ROOT/'.github/workflows/pr16-dex-placement.yml').read_text();self.assertIn("if: ${{ always() && steps.publication_guard.outcome == 'success' }}",wf)
    def test_formal_inputs_not_outputs(self):
        source=(ROOT/'scripts/pr16_dex_placement_actions.py').read_text();self.assertIn('game_hooks_installed=False',source);self.assertIn('formal_save_changed=False',source)

if __name__=='__main__':unittest.main()
