"""Circus新規script接続のhost/有限命令モデル。native物理受入とは区別する。"""
import copy
import ctypes as C
import hashlib
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch as replace
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_entry as entry


def node(address, chunks):
    rows=[];at=address
    for raw in chunks:
        row=dict(address=at,opcode=raw[0],bytes=raw.hex())
        if raw[0] in (4,5,6,7):
            pos=1 if raw[0] in (4,5) else 2
            row.update(target=struct.unpack_from('<I',raw,pos)[0],operand_address=at+pos)
        rows.append(row);at+=len(raw)
    return dict(address=address,instructions=rows)


def fixture():
    root=entry.BASE+0x1000;cancel=root+0x100
    nodes=[node(root,[b'\x0f\x00'+entry.ptr(root+0x200),b'\x09\x05',b'\x5d',b'\x5d',b'\x5d',entry.goto(cancel)]),
           node(cancel,[entry.call(root+0x301),b'\x6c',b'\x02'])]
    return nodes,root,cancel


class ScriptContracts(unittest.TestCase):
    def build(self,nodes=None):
        original,root,cancel=fixture()
        return entry.fork_graph(original if nodes is None else nodes,entry.BASE+0x4000,
                                entry.BASE+0x601,entry.DRAW,cancel,root+0x200,entry.BASE+0x7000)

    def test_exact_layout_and_original_graph_is_not_mutated(self):
        nodes,root,cancel=fixture();before=copy.deepcopy(nodes)
        raw,labels,sites,std=self.build(nodes)
        self.assertEqual(nodes,before)
        self.assertEqual((len(sites),len(std)),(3,1))
        self.assertEqual(raw[2:6],entry.ptr(entry.BASE+0x7000))
        self.assertEqual(raw[-12:-7],entry.goto(labels[cancel]))
        self.assertEqual(raw[-7:],entry.call(root+0x301)+b'\x6c\x02')
        for site in sites:
            offset=site['new']-(entry.BASE+0x4000)
            self.assertEqual(raw[offset:offset+site['size']],entry.admission(site['new'],entry.BASE+0x601,entry.DRAW,labels[cancel]))

    def test_finite_script_control_flow_for_rejection_and_zero_to_five_draws(self):
        # emitted実byteの命令モデル。これをmGBA/乱数/実入場の証拠にしない。
        start=entry.BASE+0x5000;select=entry.BASE+0x601;failure=start+0x1000
        raw=entry.admission(start,select,entry.DRAW,failure)
        for selected in (0,1):
            for effects in range(6):
                pc=start;result=0;cmp=False;calls=[];draws=0;launched=False
                for _ in range(70):
                    if pc==failure:break
                    i=pc-start;op=raw[i]
                    if op==0x23:
                        target=struct.unpack_from('<I',raw,i+1)[0];calls.append(target)
                        if target==select:result=selected
                        else:
                            self.assertEqual(target,entry.DRAW);result=int(draws>=effects);draws+=1
                        pc+=5
                    elif op==0x21:
                        self.assertEqual(raw[i+1:i+5],b'\x0d\x80\x01\x00');cmp=result==1;pc+=5
                    elif op==6:
                        self.assertEqual(raw[i+1],1);pc=struct.unpack_from('<I',raw,i+2)[0] if cmp else pc+6
                    elif op==5:pc=struct.unpack_from('<I',raw,i+1)[0]
                    elif op==0x5d:launched=True;break
                    else:self.fail('未知命令')
                else:self.fail('有限モデルが停止しない')
                self.assertEqual(launched,bool(selected))
                self.assertEqual(calls,[select]+([entry.DRAW]*(effects+1) if selected else []))
                if not selected:self.assertEqual(pc,failure)

    def test_old_factory_fallback_and_optional_circus(self):
        at=entry.BASE+0x5000;prompt=at+0x100;circus=at+0x200
        raw=entry.bridge(at,prompt,circus)
        self.assertEqual(raw[:8],b'\x0f\x00'+entry.ptr(prompt)+b'\x09\x05')
        self.assertEqual(raw[8:19],entry.equal(circus))
        self.assertEqual(raw[19:],entry.goto(entry.FACTORY))

    def test_other_prompt_pointer_is_preserved(self):
        nodes,root,_=fixture();nodes[0]['instructions'][0]['bytes']=(b'\x0f\x00'+entry.ptr(root+0x202)).hex()
        self.assertEqual(self.build(nodes)[0][2:6],entry.ptr(root+0x202))

    def test_reject_missing_or_duplicate_cancel(self):
        nodes,_,_=fixture()
        for altered in (nodes[:1],nodes+[nodes[-1]]):
            with self.assertRaises(ValueError):self.build(altered)

    def test_reject_external_script_edge(self):
        nodes,_,_=fixture();row=nodes[0]['instructions'][-1]
        row['bytes']=entry.goto(entry.BASE+0x1234).hex();row['target']=entry.BASE+0x1234
        with self.assertRaises(ValueError):self.build(nodes)

    def test_reject_inconsistent_branch_metadata(self):
        nodes,_,_=fixture();nodes[0]['instructions'][-1]['target']+=1
        with self.assertRaises(ValueError):self.build(nodes)

    def test_reject_dynamic_std(self):
        for opcode,index in ((9,0),(9,6),(8,4),(10,4)):
            nodes,_,_=fixture();row=nodes[0]['instructions'][1]
            row.update(opcode=opcode,bytes=bytes([opcode,index]).hex())
            with self.assertRaises(ValueError):self.build(nodes)

    def test_reject_unknown_and_wrong_lengths(self):
        for raw in (b'\xff',b'\x5d\x00',b'\x24\x01\x00\x00\x08'):
            nodes,_,_=fixture();nodes[0]['instructions'][2].update(opcode=raw[0],bytes=raw.hex())
            with self.assertRaises(ValueError):self.build(nodes)

    def test_reject_shifted_instruction_boundary(self):
        nodes,_,_=fixture();nodes[0]['instructions'][2]['address']+=1
        with self.assertRaises(ValueError):self.build(nodes)

    def test_reject_different_launch_count(self):
        nodes,_,_=fixture();nodes[0]['instructions'][2].update(opcode=39,bytes='27')
        with self.assertRaises(ValueError):self.build(nodes)

    def test_reject_pointer_types_and_bounds(self):
        for value in (True,0,entry.BASE-1,entry.BASE+entry.SIZE,1.5):
            with self.assertRaises(ValueError):entry.ptr(value)
        with self.assertRaises(ValueError):entry.call(entry.BASE+0x100)

    def test_script_pointer_need_not_be_aligned(self):
        self.assertEqual(entry.ptr(entry.BASE+1),b'\x01\x00\x00\x08')

    def test_patch_exact_two_spans_and_parent_immutable(self):
        # synthetic ROM only; parent identity replaced in this test, not production.
        size=0x2000;gate=entry.BASE+0x100;operand=0x101;offset=0x1000
        raw=bytearray(b'\xff'*size);raw[operand:operand+4]=entry.ptr(entry.FACTORY);raw=bytes(raw)
        with replace.object(entry,'SIZE',size),replace.object(entry,'GATE',gate),replace.object(entry,'PARENT_SHA',hashlib.sha256(raw).hexdigest()):
            # Factory is beyond this small synthetic ROM; preserve pointer checking size separately.
            with replace.object(entry,'FACTORY',entry.BASE+0x500):
                raw=bytearray(raw);raw[operand:operand+4]=entry.ptr(entry.FACTORY);raw=bytes(raw)
                with replace.object(entry,'PARENT_SHA',hashlib.sha256(raw).hexdigest()):
                    patched=entry.patch(raw,offset,b'abcde',operand,entry.BASE+offset+1)
                    self.assertEqual(patched[:operand],raw[:operand]);self.assertEqual(patched[operand+4:offset],raw[operand+4:offset])
                    self.assertEqual(patched[offset:offset+5],b'abcde');self.assertEqual(patched[offset+5:],raw[offset+5:])
                    self.assertEqual(raw[offset:offset+5],b'\xff'*5)
                    for args in ((offset+1,b'abc',operand,entry.BASE+offset),(offset,b'a'*8193,operand,entry.BASE+offset),
                                 (offset,b'abc',operand+1,entry.BASE+offset),(offset,b'abc',operand,entry.BASE+offset+3)):
                        with self.assertRaises(ValueError):entry.patch(raw,*args)
                    with self.assertRaises(ValueError):entry.patch(patched,offset,b'abc',operand,entry.BASE+offset)


class ScriptAdapterHost(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work=tempfile.TemporaryDirectory();p=Path(cls.work.name)
        (p/'result.c').write_text('volatile unsigned short VegaCircusScriptResult;\n')
        subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-fPIC','-shared',
            str(ROOT/entry.SOURCE),str(ROOT/'overlays/circus_admission/circus_admission.c'),
            str(ROOT/'overlays/cfru/integration.c'),str(ROOT/'overlays/cfru/runtime.c'),str(p/'result.c'),'-o',str(p/'adapter.so')],check=True,capture_output=True)
        cls.lib=C.CDLL(str(p/'adapter.so'));cls.slot=C.c_uint16.in_dll(cls.lib,'VegaCircusScriptResult')
        cls.lib.VegaCircusAdmissionSelectScript.restype=None
        cls.lib.cfru_integration_pending_configure_facility.argtypes=[C.c_int]*3
        cls.lib.cfru_integration_pending_configure_facility.restype=C.c_uint8
        cls.lib.cfru_integration_pending_take.argtypes=[C.c_void_p]
        cls.lib.cfru_integration_pending_take.restype=C.c_uint8
        cls.lib.cfru_integration_battle_end.argtypes=[C.c_int]
    @classmethod
    def tearDownClass(cls):cls.work.cleanup()
    def setUp(self):
        self.lib.cfru_integration_battle_end(6)
        shadow=(C.c_ubyte*52).in_dll(self.lib,'gCfruPendingBattleShadow');C.memset(C.addressof(shadow),0,52)
        self.slot.value=0xa55a
    def test_rejection_overwrites_stale_script_result(self):
        self.lib.VegaCircusAdmissionSelectScript();self.assertEqual(self.slot.value,0)
    def test_prepared_command_returns_one_and_transfers_number_three(self):
        self.assertEqual(self.lib.cfru_integration_pending_configure_facility(0,0,0),1)
        self.lib.VegaCircusAdmissionSelectScript();self.assertEqual(self.slot.value,1)
        command=(C.c_ubyte*48)();self.assertEqual(self.lib.cfru_integration_pending_take(command),1)
        self.assertEqual(bytes(command)[14:16],b'\x03\x00')
    def test_taken_command_cannot_return_stale_success(self):
        self.lib.cfru_integration_pending_configure_facility(0,0,0);self.lib.VegaCircusAdmissionSelectScript()
        command=(C.c_ubyte*48)();self.lib.cfru_integration_pending_take(command)
        self.lib.VegaCircusAdmissionSelectScript();self.assertEqual(self.slot.value,0)
    def test_next_trial_is_not_implicitly_selected(self):
        self.lib.cfru_integration_pending_configure_facility(0,0,0);self.lib.VegaCircusAdmissionSelectScript()
        self.lib.cfru_integration_pending_configure_facility(0,0,0)
        command=(C.c_ubyte*48)();self.lib.cfru_integration_pending_take(command)
        self.assertEqual(bytes(command)[14:16],b'\x00\x00')

if __name__=='__main__':unittest.main()
