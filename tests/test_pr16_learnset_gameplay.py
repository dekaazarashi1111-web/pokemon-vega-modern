"""新しい原本vector/通常操作受入境界だけ。既受入native/Wikiは実行しない。"""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_learnset_gameplay as m


class GameplayContracts(unittest.TestCase):
    def setUp(self):
        self.case=m.vector('positive',list(range(100,231)),page=3)
        c=self.case
        self.row=dict(schema_version=1,status='PASS',scope=m.SCOPE,case=c['name'],rom_sha256=m.CANDIDATE['sha256'],
                      **{k:c[k] for k in ('family','species','page','index','action','slot','hof')},
                      candidate_count=c['count'],selected_move=c['expected'],canonical_pp=c['canonical_pp'],
                      moves_before=c['known'],pp_before=c['pp'],moves_after=c['after'],pp_after=c['after_pp'],
                      normal_bag_input=True,normal_save_menu=True,fresh_core_normal_continue=True,mode_reset=True,
                      host_write_barriers=3,core_instances=2,party_mon_bytes_preserved=100,save_counters=[2,3,3],
                      mgba_version='0.10.2',warnings_errors=0,story_acquisition_verified=False,battle_verified=False,
                      issue19_complete=False,release_ready=False,
                      witness=dict(bag=1,mode_menu=2,mode_choice=3,party=4,page_menu=5,page_choice=6,list=7,
                                   ask=8,delete_ask=9,summary=10,selection=11,replaced=12,learned=13,
                                   giveup=0,locked=0,field=14))
        self.err=b''.join(b'GAMEPLAY_PARTY label='+label+b' counter='+str(counter).encode()+b' hex='+b'01'*100+b'\n'
                          for label,counter in ((b'learned',2),(b'saved',3),(b'continued',3)))
        self.err+=b'original core destroyed; new core normal Continue\n'

    def check(self, row=None, err=None, case=None):
        return m.validate_result(json.dumps(self.row if row is None else row).encode(),self.err if err is None else err,self.case if case is None else case)

    def test_complete_result(self):
        self.assertEqual(self.check()['party_identity']['size'],100)

    def test_raw_boundary_before_known_filter(self):
        raw=list(range(1,132));known=raw[39:43]
        self.assertEqual(m.raw_page(raw,1,known),list(range(44,81)))
        self.assertEqual(m.raw_page(raw,3,known),list(range(121,132)))

    def test_preserves_original_order(self):
        self.assertEqual(m.raw_page([76,63,76,129],0,[0]*4),[76,63,129])

    def test_side_change_rejected(self):
        with self.assertRaises(ValueError):m.raw_page([1063],0,[0]*4)

    def test_page_negative_and_boolean_rejected(self):
        for page in (-1,4,True):
            with self.subTest(page=page),self.assertRaises(ValueError):m.raw_page([1],page,[0]*4)

    def test_out_of_range_selection(self):
        with self.assertRaises(ValueError):m.vector('bad',[100],index=1)

    def test_empty_list_not_accepted(self):
        with self.assertRaises(ValueError):m.vector('bad',[33,81,45,52])

    def test_empty_slot_preserves_others(self):
        v=m.vector('empty',m.FLOETTE,species=1029,action=1)
        self.assertEqual(v['known'],[33,81,0,0]);self.assertEqual(v['after'],[33,81,63,0])
        self.assertEqual(v['after_pp'][:2],v['pp'][:2])

    def test_cancels_do_not_teach(self):
        for action in range(2,8):
            v=m.vector('cancel',[100,101],action=action)
            self.assertEqual(v['known'],v['after']);self.assertEqual(v['pp'],v['after_pp'])
            self.assertEqual(v['hof'],int(action!=6))

    def test_wrong_rom_rejected(self):
        self.row['rom_sha256']='0'*64
        with self.assertRaises(ValueError):self.check()

    def test_missing_page_witness_rejected(self):
        self.row['witness']['page_choice']=0
        with self.assertRaises(ValueError):self.check()

    def test_out_of_order_summary_rejected(self):
        self.row['witness']['summary']=2
        with self.assertRaises(ValueError):self.check()

    def test_missing_physical_entry_rejected(self):
        self.row['normal_bag_input']=False
        with self.assertRaises(ValueError):self.check()

    def test_warning_rejected(self):
        self.row['warnings_errors']=1
        with self.assertRaises(ValueError):self.check()

    def test_scope_promotion_rejected(self):
        for key in ('battle_verified','story_acquisition_verified','issue19_complete','release_ready'):
            row=copy.deepcopy(self.row);row[key]=True
            with self.subTest(key=key),self.assertRaises(ValueError):self.check(row=row)

    def test_byte_corruption_rejected(self):
        err=self.err.replace(b'label=continued counter=3 hex=01',b'label=continued counter=3 hex=02')
        with self.assertRaises(ValueError):self.check(err=err)

    def test_missing_fresh_core_rejected(self):
        with self.assertRaises(ValueError):self.check(err=self.err.split(b'original core destroyed')[0])

    def test_wrong_counter_rejected(self):
        self.row['save_counters']=[2,2,2]
        with self.assertRaises(ValueError):self.check()

    def test_header_is_fixed_vector_not_provider(self):
        h=m.header([self.case]).decode()
        self.assertIn('static const struct GCase G_CASES[]',h)
        self.assertIn('"positive"',h)
        self.assertNotIn('call_preserving',h)
        self.assertEqual(m.FLOETTE,[63,76,80,104,118,129,219,263,318,347,420,682])

    def test_native_three_barriers_and_no_old_oracle(self):
        text=(ROOT/'tools/mgba_pr16_learnset_gameplay.c').read_text()
        self.assertEqual(text.count('a_guard(c);'),3)
        self.assertEqual(text.count('a_restore(c,&saved);'),3)
        self.assertEqual(text.count('c->reset(c);'),2)
        self.assertNotIn('a_candidates(',text)
        self.assertNotIn('gameplay_old_archive(',text)
        for segment in text.split('a_guard(c);')[1:]:
            guarded=segment.split('a_restore(c,&saved);',1)[0]
            for prohibited in ('call_preserving','write8(','write16(','write32(','p02s_set_data'):
                self.assertNotIn(prohibited,guarded)


if __name__=='__main__':unittest.main()
