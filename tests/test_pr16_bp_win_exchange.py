"""native勝利/単体交換の証拠境界。旧受入の再実行は行わない。"""
import json
import subprocess
import tempfile
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts'),str(Path(__file__).resolve().parents[1])]
import pr16_bp_win_exchange as p
import pr16_bp_selection_native as launch
from tests import test_pr16_bp_battle_return as historical

TRACE=(b'BP_WIN_SWITCH_ID label=matched \nBP_WIN_SWITCH_OPENING label=returned \nBP_WIN_RESERVE \nBP_CTRL label=fixture \nBP_READ name=cfru_selected_order \nBP_LAUNCH label=before-confirm \n'
       b'BP_LAUNCH label=launch-stop \nBP_READ name=enemy_party_generated \nBP_PROGRESS move=\n'
       b'BP_CTRL label=first-turn-return \nBP_RETURN label=extension-start \nBP_RETURN label=facility-stop \n'
       b'BP_WIN_TEAM \nBP_WIN_MOVE \nBP_CTRL label=exchange-single-menu \n'
       b'BP_CTRL label=exchange-single-selected \nBP_CTRL label=exchange-committed \n'
       b'BP_CTRL label=exchange-next-action \nBP_READ name=exchange_cached_original \n'
       b'BP_READ name=exchange_party_committed ')

class WinExchangeTests(unittest.TestCase):
    def sample(self):
        row=historical.ReturnTests().sample()
        row.update(status=p.STATUS,case=p.CASE,scope=p.SCOPE,candidate_sha256=p.SHA,total_frames=14000,
            exchange_menu_frame=9500,exchange_selected_frame=10000,exchange_confirm_frame=10001,
            exchange_commit_frame=10400,next_battle_struct_frame=11000,next_battle_action_frame=14000,
            exchange_slot=2,exchange_selected_order=3,exchange_preserved_bytes=500,exchange_replaced_bytes=100,
            native_exchange_observed=True,native_exchange_accepted=False,opening_native_switches=1,forced_identity_checks=row['forced_switches'])
        return row
    def check(self,row,stderr=TRACE,code=0):
        with patch.object(launch,'SHA',p.SHA):
            return p.validate(json.dumps(row).encode(),stderr,code)
    def test_complete_bounded_chain(self):
        row=self.check(self.sample())
        self.assertTrue(row['native_exchange_observed'])
        self.assertFalse(row['native_bp_earning_accepted'])
    def test_boolean_and_one_based_slots(self):
        for key,value in [('forced_identity_checks',True),('forced_identity_checks',0),('opening_native_switches',True),('opening_native_switches',2),('exchange_slot',True),('exchange_slot',3),('exchange_selected_order',0),
                          ('exchange_selected_order',2),('exchange_commit_frame',True)]:
            with self.subTest(key=key,value=value):
                row=self.sample();row[key]=value
                with self.assertRaises(ValueError):self.check(row)
    def test_order_and_timeout_fail_closed(self):
        for key,value in [('exchange_menu_frame',9000),('exchange_confirm_frame',10000),
                          ('exchange_commit_frame',10000),('next_battle_action_frame',35001),('total_frames',35001)]:
            with self.subTest(key=key,value=value):
                row=self.sample();row[key]=value
                with self.assertRaises(ValueError):self.check(row)
    def test_loss_is_not_victory(self):
        row=self.sample();row['battle_outcome']=2
        with self.assertRaises(ValueError):self.check(row)
    def test_bytes_and_acceptance_cannot_be_inflated(self):
        for key,value in [('exchange_preserved_bytes',499),('exchange_replaced_bytes',99),
                          ('native_exchange_observed',1),('native_exchange_accepted',True),
                          ('bp_earned',9),('host_write_barriers',6),('native_bp_earning_accepted',True),
                          ('release_ready',True),('candidate_sha256','0'*64)]:
            with self.subTest(key=key,value=value):
                row=self.sample();row[key]=value
                with self.assertRaises(ValueError):self.check(row)
    def test_missing_extra_and_duplicate_fields(self):
        row=self.sample();del row['exchange_slot']
        with self.assertRaises(ValueError):self.check(row)
        row=self.sample();row['fabricated']=True
        with self.assertRaises(ValueError):self.check(row)
        raw=json.dumps(self.sample())[:-1]+',"exchange_slot":2}'
        with self.assertRaises(ValueError):p.validate(raw.encode(),TRACE,0)
    def test_every_exchange_trace_is_required(self):
        for marker in (b'BP_WIN_SWITCH_ID label=matched ',b'BP_WIN_SWITCH_OPENING label=returned ',b'BP_WIN_RESERVE ',b'BP_WIN_TEAM ',b'BP_WIN_MOVE ',b'exchange-single-menu ',b'exchange-single-selected ',
                       b'exchange-committed ',b'exchange-next-action ',b'exchange_cached_original ',b'exchange_party_committed '):
            with self.subTest(marker=marker):
                with self.assertRaises(ValueError):self.check(self.sample(),TRACE.replace(marker,b'absent'))
    def test_native_process_failure_is_not_success(self):
        with self.assertRaises(ValueError):self.check(self.sample(),code=1)
    def test_historical_pins_guard_and_unchanged_bounds(self):
        text=p.assemble_controller()
        self.assertEqual(text.count('struct BPReturn finish=br_battle_return(c,party,counter);'),1)
        self.assertEqual(text.count('struct WXResult exchange=wx_exchange_next(c,party,counter,finish.outcome);'),1)
        self.assertIn('wx_team(c);',text)
        self.assertIn('b_frames-w.start<90000U',text)
        self.assertIn('f<18000U',text)
        extension=(p.ROOT/p.SOURCE).read_text()
        after=text.split('a_guard(c);bp_open(c);',1)[1]
        for term in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'busWrite', 'rawWrite'):
            self.assertNotIn(term,extension);self.assertNotIn(term,after)
        self.assertIn('memcmp(expected,actual,sizeof(actual))',extension)
        self.assertIn('0x092CF72CU',extension)
    def test_type_policy_host_c_vectors(self):
        text=(p.ROOT/p.SOURCE).read_text()
        helper=text[text.index('static unsigned wx_effect('):text.index('static unsigned wx_move_slot(')]
        vectors=[(10,11,5),(12,12,5),(12,3,5),(3,12,20),(3,3,5),
                 (17,14,20),(14,17,0),(13,4,0),(16,18,0),(7,8,10),(99,1,10)]
        checks=''.join('if(wx_effect(%dU,%dU)!=%dU)return 1;' % v for v in vectors)
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/'policy.c';exe=Path(tmp)/'policy'
            src.write_text(helper+'\nint main(void){'+checks+'return 0;}\n')
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(src),'-o',str(exe)],check=True,capture_output=True)
            subprocess.run([str(exe)],check=True,capture_output=True)
    def test_actual_native_types_and_protect_keep_old_gate(self):
        text=p.assemble_controller()
        self.assertIn('BATTLE_MON_SIZE+BATTLE_CORE_MON_TYPE1',text)
        self.assertIn('score=score*effect/100U',text)
        self.assertIn('==182U',text)
        self.assertIn('w.returned>w.spent',text)
        self.assertIn('win extension ended in native loss; retain failure',text)
        self.assertIn('if(w.outcome==1U || ++stable==30U)',text)
        self.assertIn('exchange requires observed native victory and ledger',text)
    def test_one_voluntary_switch_keeps_global_and_forced_bounds(self):
        text=p.assemble_controller()
        self.assertEqual(text.count('if(!wx_voluntary_count){wx_opening_switch(c);continue;}'),1)
        self.assertIn('target=wx_reserve(c,active)',text)
        self.assertIn('w.switches<2U',text)
        self.assertIn('w.turns<48U',text)
        self.assertIn('b_frames-w.start<90000U',text)
        self.assertIn('native voluntary PKMN menu absent',text)
    def test_selected_individual_not_ui_battle_index(self):
        source=p.IDENTITY_C[:p.IDENTITY_C.index('static struct WXIdentity wx_party_identity')]
        source=source.replace('static unsigned wx_identity_checks;','')
        vectors='''int main(void){
          struct WXIdentity a={.personality=42,.ot=7,.species=63,.moves={94,347,115,182}},b=a;
          if(!wx_identity_equal(a,b))return 1;
          b.personality++;if(wx_identity_equal(a,b))return 2;b=a;
          b.ot++;if(wx_identity_equal(a,b))return 3;b=a;
          b.species++;if(wx_identity_equal(a,b))return 4;b=a;
          b.moves[3]++;if(wx_identity_equal(a,b))return 5;
          return 0;
        }'''
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/'identity.c';exe=Path(tmp)/'identity'
            src.write_text('#include <stdint.h>\n#include <stdbool.h>\n'+source+vectors)
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(src),'-o',str(exe)],check=True,capture_output=True)
            subprocess.run([str(exe)],check=True,capture_output=True)
        text=p.assemble_controller()
        self.assertIn('wx_identity_equal(selected,wx_battle_identity(c))',text)
        self.assertNotIn('&& read16(c,ADDR_BATTLER_PARTY_INDEXES)==target',text)
        self.assertIn('f<1800U',text)
        self.assertIn('n_action(c) && read16(c,ADDR_BATTLER_PARTY_INDEXES)<3U',text)
    def test_derivation_refuses_ambiguous_anchor(self):
        for text in ('','xx'):
            with self.assertRaises(ValueError):p.replace_once(text,'x','y')

if __name__=='__main__':unittest.main()
