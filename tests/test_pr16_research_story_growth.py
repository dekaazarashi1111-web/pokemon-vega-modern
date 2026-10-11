"""新区間の実原本陽性を前提とし、改変拒否の対象を個別に固定する。"""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_research_story_growth as m


def replace(value,path,new):
    for key in path[:-1]:value=value[key]
    value[path[-1]]=new


class GrowthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dev=ROOT/m.DEV
        cls.raw=(cls.dev/'progress.stdout.txt').read_bytes()
        cls.cold_raw=(cls.dev/'continue.stdout.txt').read_bytes()
        cls.parent=m.load((ROOT/m.PARENT).read_bytes())
        cls.first,cls.second=m.read_trace(cls.raw),m.read_trace(cls.cold_raw)
        cls.positive=m.verify(cls.raw,cls.cold_raw,cls.parent,m.OUTPUT_SAVE)
        assert cls.positive['status']=='PASS_NATURAL_STORY_GROWTH_SAVE_SCOPED'

    def test_actual_positive_scope(self):
        self.assertEqual(self.positive['experience_awards'],[37,33])
        self.assertEqual(self.positive['final_experience'],204)
        self.assertEqual(self.positive['level_after'],6)
        self.assertEqual(self.positive['final_hp'],[21,21])
        self.assertEqual(self.positive['trainer_victories'],0)
        self.assertEqual(self.positive['trainer_losses'],2)
        self.assertEqual(self.positive['wild_victories'],1)
        self.assertEqual(self.positive['wild_escapes'],1)
        self.assertFalse(self.positive['natural_research_arrival_accepted'])
        self.assertFalse(self.positive['new_town_arrival_accepted'])
        self.assertFalse(self.positive['release_ready'])

    def test_original_progress_commands_match_every_external_input(self):
        m.command_trace((self.dev/'commands.txt').read_text(),self.raw)

    def test_original_cold_commands_match_every_external_input(self):
        m.command_trace((self.dev/'continue-commands.txt').read_text(),self.cold_raw,True)

    def test_all_three_native_ui_matches(self):
        for a,b in ((77,2),(79,3),(82,5)):
            self.assertEqual(self.first['screens'][a]['sha256'],self.second['screens'][b]['sha256'])

    def test_format_positive_not_native_acceptance(self):
        raw=b'P6\n240 160\n255\n'+b'\xff\x00\x00'+bytes(240*160*3-3)
        m.screen_bytes(raw,dict(sha256=m.identity(raw)['sha256']))

    def test_blank_screen_rejected_even_with_correct_hash(self):
        raw=b'P6\n240 160\n255\n'+bytes(240*160*3)
        with self.assertRaises(ValueError):m.screen_bytes(raw,dict(sha256=m.identity(raw)['sha256']))

    def test_wrong_ppm_dimensions_rejected(self):
        raw=b'P6\n160 240\n255\n'+b'\xff\x00\x00'+bytes(240*160*3-3)
        with self.assertRaises(ValueError):m.screen_bytes(raw,dict(sha256=m.identity(raw)['sha256']))

    def test_wrong_screen_hash_rejected(self):
        raw=b'P6\n240 160\n255\n'+b'\xff\x00\x00'+bytes(240*160*3-3)
        with self.assertRaises(ValueError):m.screen_bytes(raw,dict(sha256='0'*64))

    def test_missing_screen_set_rejected(self):
        with tempfile.TemporaryDirectory() as name,self.assertRaises(ValueError):
            m.screens(self.first,Path(name))

    def test_truncated_end_rejected(self):
        with self.assertRaises(ValueError):m.read_trace(b'\n'.join(self.raw.splitlines()[:-1])+b'\n')

    def test_duplicate_json_key_rejected(self):
        raw=self.raw.replace(b'"host_write_barriers":7',b'"host_write_barriers":7,"host_write_barriers":7',1)
        with self.assertRaises(ValueError):m.read_trace(raw)

    def test_nonobject_row_rejected(self):
        lines=self.raw.splitlines();lines.insert(1,b'[]')
        with self.assertRaises(ValueError):m.read_trace(b'\n'.join(lines)+b'\n')

    def test_unknown_write_row_rejected(self):
        lines=self.raw.splitlines();lines.insert(1,b'{"write32":1}')
        with self.assertRaises(ValueError):m.read_trace(b'\n'.join(lines)+b'\n')

    def test_missing_same_frame_screen_rejected(self):
        lines=self.raw.splitlines();del lines[14]
        with self.assertRaises(ValueError):m.read_trace(b'\n'.join(lines)+b'\n')

    def test_boot_input_changed_rejected(self):
        rows=m.prior.load_rows(self.raw);rows[1]['key']=16
        with self.assertRaises(ValueError):m.read_trace(encode(rows))

    def test_command_execution_mismatch_rejected(self):
        text=(self.dev/'commands.txt').read_text().replace('key 64 80','key 128 80',1)
        self.assertNotEqual(text,(self.dev/'commands.txt').read_text())
        with self.assertRaises(ValueError):m.command_trace(text,self.raw)

    def test_reused_observation_zero_rejected(self):
        text=(self.dev/'commands.txt').read_text().replace('observe 1\n','observe 0\n')
        with self.assertRaises(ValueError):m.commands(text)

    def test_extra_cold_save_rejected(self):
        text=(self.dev/'continue-commands.txt').read_text().replace('quit\n','save\nquit\n')
        with self.assertRaises(ValueError):m.commands(text,True)

    def test_missing_progress_save_rejected(self):
        text=(self.dev/'commands.txt').read_text().replace('save\n','')
        with self.assertRaises(ValueError):m.commands(text)

    def test_fixture_command_rejected(self):
        text='warp 96 0\n'+(self.dev/'commands.txt').read_text()
        with self.assertRaises(ValueError):m.commands(text)

    def test_multi_key_command_rejected(self):
        text='key 3 2\n'+(self.dev/'commands.txt').read_text()
        with self.assertRaises(ValueError):m.commands(text)

    def test_missing_quit_rejected(self):
        text=(self.dev/'commands.txt').read_text().replace('quit\n','')
        with self.assertRaises(ValueError):m.commands(text)


def encode(rows):return ('\n'.join(json.dumps(x) for x in rows)+'\n').encode()


MUTATIONS=[
 ('parent_status','parent',('status',),'UNCONFIRMED'),
 ('parent_terminal','parent',('actions_completion_confirmed',),False),
 ('parent_run','parent',('run_id',),0),
 ('parent_source','parent',('source_head',),'0'*40),
 ('parent_artifact','parent',('retained_artifact_id',),0),
 ('parent_candidate','parent',('checkpoint','candidate','sha256'),'0'*64),
 ('parent_save','parent',('checkpoint','save','sha256'),'0'*64),
 ('parent_runner','parent',('checkpoint','executable','sha256'),'0'*64),
 ('parent_runtime','parent',('checkpoint','runtime_artifact'),0),
 ('parent_data','parent',('checkpoint','data_artifact'),0),
 ('parent_scope','parent',('natural_research_arrival_accepted',),True),
 ('parent_full_story','parent',('full_story_accepted',),True),
 ('parent_release','parent',('release_ready',),True),
 ('parent_baseline','parent',('active_baseline_changed',),True),
 ('parent_potion','parent',('native_bag_potion_count',),0),
 ('parent_consumed','parent',('potion_consumed',),True),
 ('input_save','first',('start','initial_save_sha256'),'0'*64),
 ('cold_input_save','second',('start','initial_save_sha256'),'0'*64),
 ('successor_rtc','saved',('sha256',),'0'*64),
 ('successor_size','saved',('size',),131072),
 ('progress_inputs','first',('end','inputs'),366),
 ('progress_frames','first',('end','frames'),37209),
 ('cold_inputs','second',('end','inputs'),37),
 ('cold_frames','second',('end','frames'),2735),
 ('save_counter_receipt','first',('saves',0,'after'),5),
 ('initial_xy','first',('observations',0,'xy'),[26,18]),
 ('initial_party','first',('observations',0,'party_sha256'),'0'*64),
 ('extra_party','first',('observations',50,'party_count'),2),
 ('extra_rp','first',('observations',65,'rp'),1),
 ('extra_save','first',('observations',65,'save_counter'),4),
 ('facility_warp','first',('observations',50,'map'),[97,0]),
 ('wild_loss_as_win','first',('observations',16,'battle_outcome'),2),
 ('wild_trainer_flags','first',('observations',6,'battle_flags'),12),
 ('wild_wrong_xy','first',('observations',6,'xy'),[36,5]),
 ('first_trainer_flags','first',('observations',20,'battle_flags'),4),
 ('first_trainer_xy','first',('observations',20,'xy'),[27,8]),
 ('first_trainer_loss_as_win','first',('observations',30,'battle_outcome'),1),
 ('first_normal_return','first',('observations',34,'xy'),[7,5]),
 ('escape_as_win','first',('observations',56,'battle_outcome'),1),
 ('escape_xy','first',('observations',56,'xy'),[34,17]),
 ('second_trainer_loss_as_win','first',('observations',71,'battle_outcome'),1),
 ('second_normal_return','first',('observations',72,'xy'),[7,5]),
 ('single_mon_as_trainer_win','first',('observations',63,'battle_outcome'),1),
 ('level_up_as_trainer_win','first',('observations',65,'battle_outcome'),1),
 ('potion_callback','first',('observations',21,'callback2'),0),
 ('healing_party_callback','first',('observations',23,'callback2'),0),
 ('summary_callback','first',('observations',79,'callback2'),0),
 ('empty_bag_callback','first',('observations',82,'callback2'),0),
 ('cold_party_ui','second',('screens',2,'sha256'),'0'*64),
 ('cold_summary_ui','second',('screens',3,'sha256'),'0'*64),
 ('cold_bag_ui','second',('screens',5,'sha256'),'0'*64),
 ('cold_bag_callback','second',('observations',5,'callback2'),0),
 ('final_xy','first',('observations',84,'xy'),[4,26]),
 ('final_live_xy','first',('observations',84,'live_xy'),[11,33]),
 ('final_facing','first',('observations',84,'facing'),2),
 ('final_locked','first',('observations',84,'lock'),1),
 ('final_party_differs_from_ui','first',('observations',84,'party_sha256'),'0'*64),
 ('cold_party_bytes','second',('observations',3,'party_sha256'),'0'*64),
 ('cold_flash_bytes','second',('observations',4,'flash_sha256'),'0'*64),
 ('cold_ledger_bytes','second',('observations',5,'ledger_sha256'),'0'*64),
 ('cold_save_counter','second',('observations',0,'save_counter'),3),
 ('cold_rp','second',('observations',0,'rp'),1),
 ('cold_xy','second',('observations',0,'xy'),[5,27]),
 ('cold_party_count','second',('observations',0,'party_count'),2),
 ('cold_transient_flags','second',('observations',0,'battle_flags'),12),
 ('cold_transient_outcome','second',('observations',0,'battle_outcome'),2),
 ('cold_exit_lock','second',('observations',6,'lock'),1),
]
for label,anchor in m.ANCHORS.items():
 MUTATIONS.append(('native_image_'+label,'first',('screens',anchor['observe'],'sha256'),'0'*64))


def mutation(which,path,value):
    def test(self):
        args=dict(first=copy.deepcopy(self.first),second=copy.deepcopy(self.second),
                  parent=copy.deepcopy(self.parent),saved=copy.deepcopy(m.OUTPUT_SAVE))
        replace(args[which],path,value)
        with self.assertRaises(ValueError):m.retained(**args)
    return test

for name,which,path,value in MUTATIONS:setattr(GrowthTests,'test_reject_'+name,mutation(which,path,value))


def terminal(key,value):
    def test(self):
        rows=m.prior.load_rows(self.raw);rows[-1][key]=value
        with self.assertRaises(ValueError):m.read_trace(encode(rows))
    return test

for key,value in [('warnings_errors',1),('host_write_barriers',6),('guarded_host_writes',1),
 ('fixture_calls',1),('natural_research_arrival_accepted',True),('warnings_errors',False),
 ('fixture_calls',False),('guarded_host_writes',False),('extra','unknown')]:
 setattr(GrowthTests,'test_terminal_'+key+'_'+str(value),terminal(key,value))


def screen_alias(value):
    def test(self):
        rows=m.prior.load_rows(self.raw)
        row=next(r for r in rows if r.get('screen')==1 and 'screen' in r)
        row['screen']=value
        with self.assertRaises(ValueError):m.read_trace(encode(rows))
    return test

setattr(GrowthTests,'test_boolean_screen_id_rejected',screen_alias(True))
setattr(GrowthTests,'test_float_screen_id_rejected',screen_alias(1.0))

if __name__=='__main__':unittest.main()
