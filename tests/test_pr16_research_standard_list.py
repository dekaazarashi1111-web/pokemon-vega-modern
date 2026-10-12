"""新リストだけのhost/event検査。受入済み数値・shop matrixは再実行しない。"""
import ctypes
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_research_standard_list as s

STUB=r'''
#define SL_HOST_TEST
#include "pr16_research_standard_list.c"
#include <string.h>
struct SL_TaskState sl_tasks[16];
volatile u16 sl_result;
static int created,destroyed,removed,printed,suspended,resumed,input_calls,cleared,window_result,task_result,input_value,sound_count,bad_abi,loaded;
u8 SL_CreateTask(void(*f)(u8),u8 p){created++;if(p!=0x50)bad_abi++;if(task_result<16){sl_tasks[task_result].active=1;sl_tasks[task_result].func=f;}return (u8)task_result;}
void SL_DestroyTask(u8 n){destroyed++;sl_tasks[n].active=0;sl_tasks[n].func=0;}
u16 SL_AddWindow(const struct SL_Window*w){if(w->bg||w->left!=9||w->top!=1||w->width!=20||w->height!=6||w->palette!=15||w->base!=640)bad_abi++;return (u16)window_result;}
void SL_RemoveWindow(u8 n){removed++;if(n!=3)bad_abi++;}
void SL_CopyWindow(u8 n,u8 m){if(n!=3||m!=3)bad_abi++;}
void SL_PutWindow(u8 n){if(n!=3)bad_abi++;}
void SL_FillWindow(u8 n,u8 p){if(n!=3||p!=0x11)bad_abi++;}
void SL_Print(u8 n,u8 f,const u8*t,u8 x,u8 y,u8 speed,void*cb){if(n!=3||f!=2||x!=8||y!=1+printed%3*16||speed||cb||t!=SL_ROWS[printed%3])bad_abi++;printed++;}
void SL_Schedule(u8 b){if(b)bad_abi++;}
void SL_LoadFrame(u8 n,u16 tile,u8 palette){if(n!=3||tile!=300||palette!=0xe0)bad_abi++;loaded++;}
void SL_DrawFrame(u8 n,u8 c){if(n!=3||c||loaded!=created)bad_abi++;}
void SL_ClearFrame(u8 n,u8 c){cleared++;if(n!=3||c)bad_abi++;}
u16 SL_BaseTile(void){return 300;}
u8 SL_Cursor(u8 n,u8 f,u8 x,u8 y,u8 step,u8 count,u8 initial){if(n!=3||f!=2||x||y!=1||step!=16||count!=3||initial)bad_abi++;return 0;}
s8 SL_Input(void){input_calls++;return (s8)input_value;}
void SL_Sound(u16 s){sound_count++;if(s!=5)bad_abi++;}
void SL_Suspend(void){suspended++;}
void SL_Resume(void){resumed++;}
void reset(void){memset(sl_tasks,0,sizeof sl_tasks);sl_result=123;created=destroyed=removed=printed=suspended=resumed=input_calls=cleared=sound_count=bad_abi=loaded=0;window_result=3;task_result=0;input_value=-2;}
void settings(int task,int window,int input){task_result=task;window_result=window;input_value=input;}
int value(int i){switch(i){case 0:return sl_result;case 1:return created;case 2:return destroyed;case 3:return removed;case 4:return printed;case 5:return suspended;case 6:return resumed;case 7:return input_calls;case 8:return cleared;case 9:return sound_count;case 10:return bad_abi;case 11:return sl_tasks[0].active;case 12:return sl_tasks[0].data[1];case 13:return loaded;default:return -999;}}
'''

class HostListTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();p=Path(cls.temp.name)
        (p/'pr16_research_standard_list_rows.h').write_text(s.header())
        (p/'host.c').write_text(STUB)
        proc=subprocess.run(['cc','-std=c11','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-I'+str(ROOT/'tools'),'-I'+str(p),str(p/'host.c'),'-o',str(p/'host.so')],capture_output=True)
        if proc.returncode or proc.stderr: raise AssertionError(proc.stderr.decode())
        cls.lib=ctypes.CDLL(str(p/'host.so'))
        cls.lib.value.argtypes=[ctypes.c_int];cls.lib.value.restype=ctypes.c_int
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def setUp(self):self.lib.reset()
    def v(self,i):return self.lib.value(i)
    def open(self):self.lib.SL_Open();self.assertEqual(self.v(0),65535)
    def select(self,c):
        self.open();self.lib.settings(0,3,c)
        for _ in range(3):self.lib.SL_Task(0)
    def test_standard_window_and_three_rows(self):
        self.open();self.assertEqual([self.v(i) for i in (1,4,5,10,11)],[1,3,1,0,1])
    def test_two_frame_open_debounce(self):
        self.open();self.lib.settings(0,3,0)
        self.lib.SL_Task(0);self.lib.SL_Task(0)
        self.assertEqual([self.v(i) for i in (0,7,12)],[65535,0,0])
    def test_no_input_keeps_single_owner(self):
        self.open()
        for _ in range(6):self.lib.SL_Task(0)
        self.assertEqual([self.v(i) for i in (0,1,2,3,7)],[65535,1,0,0,4])
    def test_balance_selection(self):self.select(0);self.assertEqual(self.v(0),0)
    def test_guide_selection(self):self.select(1);self.assertEqual(self.v(0),1)
    def test_exit_row(self):self.select(2);self.assertEqual(self.v(0),2)
    def test_b_cancel(self):self.select(-1);self.assertEqual(self.v(0),2)
    def test_invalid_positive_selection(self):self.select(3);self.assertEqual(self.v(0),65533)
    def test_invalid_negative_selection(self):self.select(-3);self.assertEqual(self.v(0),65533)
    def test_release_exactly_once(self):
        self.select(-1);self.lib.SL_Task(0)
        self.assertEqual([self.v(i) for i in (2,3,6,8,9,10,11)],[1,1,1,1,1,0,0])
    def test_revisit_has_new_owner_reset_cursor_and_debounce(self):
        self.select(1);self.open()
        self.assertEqual([self.v(i) for i in (1,2,3,4,5,6,10,12)],[2,1,1,6,2,1,0,2])
    def test_task_exhaustion_does_not_suspend(self):
        self.lib.settings(16,3,-2);self.lib.SL_Open()
        self.assertEqual([self.v(i) for i in (0,2,4,5)],[65533,0,0,0])
    def test_window_failure_releases_task_without_suspending(self):
        self.lib.settings(0,255,-2);self.lib.SL_Open()
        self.assertEqual([self.v(i) for i in (0,2,3,4,5,11)],[65533,1,0,0,0,0])
    def test_large_window_result_cannot_truncate_into_valid_id(self):
        self.lib.settings(0,256,-2);self.lib.SL_Open();self.assertEqual([self.v(0),self.v(2),self.v(5)],[65533,1,0])
    def test_duplicate_open_does_not_allocate(self):
        self.open();self.lib.SL_Open();self.assertEqual([self.v(0),self.v(1),self.v(4)],[65533,1,3])
    def test_frame_loaded_only_after_window_allocation(self):
        self.lib.settings(0,255,-2);self.lib.SL_Open();self.assertEqual(self.v(13),0)
    def test_each_owned_window_loads_user_frame_once(self):
        self.select(0);self.open();self.assertEqual([self.v(13),self.v(10)],[2,0])
    def test_invalid_task_id_is_noop(self):
        self.lib.SL_Task(16);self.assertEqual([self.v(0),self.v(7),self.v(6)],[123,0,0])


def walk(status=0,choices=(2,),opened=True):
    """イベントbyteを独立解釈。script producerのlabel情報は使わない。"""
    raw,_=s.event(s.BASE|1);pc=0;result=0;cmp=False;messages=[];calls=[];buffers={};waits=0;locked=False;choices=iter(choices)
    def u16(at):return struct.unpack_from('<H',raw,at)[0]
    def u32(at):return struct.unpack_from('<I',raw,at)[0]
    for _ in range(300):
        op=raw[pc];pc+=1
        if op==0x6a:locked=True
        elif op==0x5a:pass
        elif op==0x0f:
            assert raw[pc]==0;messages.append(u32(pc+1));pc+=5
        elif op==9:assert raw[pc]==4;pc+=1
        elif op==0x23:
            address=u32(pc);pc+=4;calls.append(address)
            result={0x093BE8A1:status,s.BASE|1:65535 if opened else 65533,0x093BE033:123,0x093BE057:3}[address]
        elif op==0x21:assert u16(pc)==0x800d;cmp=result==u16(pc+2);pc+=4
        elif op==6:
            assert raw[pc]==1;target=u32(pc+1)-s.EVENT;pc+=5
            if cmp:pc=target
        elif op==5:pc=u32(pc)-s.EVENT
        elif op==0x27:waits+=1;result=next(choices)
        elif op==0x83:buffers[raw[pc]]=result;assert u16(pc+1)==0x800d;pc+=3
        elif op==0x16:assert u16(pc)==0x800d;result=u16(pc+2);pc+=4
        elif op==0x6c:locked=False
        elif op==2:return messages,calls,buffers,waits,result,locked
        else:raise AssertionError('unexpected event opcode')
    raise AssertionError('nonterminating scripted input')

class EventListTests(unittest.TestCase):
    def test_select_balance_then_cancel(self):
        m,c,b,w,r,locked=walk(choices=(0,2));self.assertEqual(m,[0x093C003D,s.numeric.TEXT,0x093C008E]);self.assertEqual(b,{0:123,1:3});self.assertEqual((w,r,locked),(2,0,False))
    def test_select_guide_then_cancel(self):
        m,c,b,w,r,locked=walk(choices=(1,2));self.assertEqual(m,[0x093C003D,0x093C005A,0x093C006D,0x093C008E]);self.assertEqual((b,w,r,locked),({},2,0,False))
    def test_both_rows_and_reopening(self):self.assertEqual(walk(choices=(0,1,0,2))[3:],(4,0,False))
    def test_exit_without_getter_or_guide(self):self.assertEqual(walk()[0],[0x093C003D,0x093C008E])
    def test_cap_preserved_without_open(self):
        m,c,b,w,r,l=walk(4);self.assertEqual((m,c,w,r,l),([0x093C003D,0x093C007E],[0x093BE8A1],0,4,False))
    def test_save_failure_preserved_without_open(self):
        m,c,b,w,r,l=walk(13);self.assertEqual((m,c,w,r,l),([0x093C003D,0x093C009E],[0x093BE8A1],0,13,False))
    def test_other_rejection_preserved(self):self.assertEqual(walk(5)[3:],(0,5,False))
    def test_open_failure_never_waits(self):self.assertEqual(walk(opened=False)[3:],(0,65533,False))
    def test_invalid_menu_result_releases(self):self.assertEqual(walk(choices=(65533,))[3:],(1,65533,False))
    def test_thumb_entry_required(self):
        for bad in (s.BASE,s.EVENT|1,0,True):
            with self.subTest(bad=bad),self.assertRaises(ValueError):s.event(bad)
    def test_rows_bound_to_canonical_glyphs(self):self.assertEqual([x.hex() for x in s.rows()],['9f527e6414777e58ff','9f527e64190112220610ff','052c29ff'])
    def test_glyph_conflict_rejected(self):
        model=json.loads((ROOT/s.MODEL).read_bytes());model['dialogue'].append(dict(model['dialogue'][0],encoded_hex='00'+model['dialogue'][0]['encoded_hex'][2:]))
        with self.assertRaises(ValueError):s.rows(model)
    def test_missing_terminator_rejected(self):
        model=json.loads((ROOT/s.MODEL).read_bytes());model['dialogue'][0]['encoded_hex']=model['dialogue'][0]['encoded_hex'][:-2]+'00'
        with self.assertRaises(ValueError):s.rows(model)
    def test_event_partition(self):
        raw,labels=s.event(s.BASE|1);self.assertLessEqual(len(raw),512);self.assertTrue(all(s.EVENT<=p<s.BASE+s.WINDOW for p in labels.values()))

if __name__=='__main__':unittest.main()
