"""HM05新区間だけのrefusal tests。原本を読むがnative/旧受入試験は実行しない。"""
import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_hm05_accept as m
PLAN=m.load((m.ROOT/m.DEV/'expected.json').read_bytes())


def raw(lane,key):
    return m.inflate(PLAN[lane]['development_'+key+'_zlib_b85'])


def parsed():
    return (m.trace(raw('progress','stdout'),raw('progress','commands'),m.INPUT_SAVE),
            m.trace(raw('continue','stdout'),raw('continue','commands'),m.OUTPUT_SAVE))


def formal_fixture():
    # 合成fixtureでありnative測定/画面レビューではない。追加tailの判定だけを試験する。
    a,b=parsed();o=copy.deepcopy(b['observations'][-1]);o.update(observe=10,frame=3690,field=True,lock=0)
    b['observations'].append(o);b['end'].update(inputs=59,frames=3690)
    return a,b


class TraceTests(unittest.TestCase):
    def reject(self,key,value,index=None,lane='progress'):
        data=[m.load(x) for x in raw(lane,'stdout').splitlines()]
        if index is None:index=len(data)-1
        data[index][key]=value
        data=b''.join(json.dumps(x,separators=(',',':')).encode()+b'\n' for x in data)
        with self.assertRaises(ValueError):m.trace(data,raw(lane,'commands'),m.INPUT_SAVE if lane=='progress' else m.OUTPUT_SAVE)
    def test_exact_development_streams(self):
        a,b=parsed();self.assertEqual(a['end']['inputs'],248);self.assertEqual(b['end']['inputs'],56)
    def test_wrong_begin_seed(self):self.reject('initial_save_sha256','0'*64,0)
    def test_wrong_candidate(self):self.reject('candidate_sha256','0'*64,0)
    def test_wrong_input_key(self):self.reject('key',16,1)
    def test_boolean_input_index(self):self.reject('input',False,1)
    def test_wrong_input_frame(self):self.reject('frame',1,1)
    def test_wrong_input_duration(self):self.reject('frames',599,1)
    def test_wrong_end_count(self):self.reject('inputs',247)
    def test_missing_barrier(self):self.reject('host_write_barriers',6)
    def test_guarded_write(self):self.reject('guarded_host_writes',1)
    def test_fixture_call(self):self.reject('fixture_calls',1)
    def test_native_warning(self):self.reject('warnings_errors',1)
    def test_unproven_scope(self):self.reject('natural_research_arrival_accepted',True)
    def test_extra_line(self):
        with self.assertRaises(ValueError):m.trace(raw('progress','stdout')+b'{}\n',raw('progress','commands'),m.INPUT_SAVE)
    def test_duplicate_json_key(self):
        data=raw('progress','stdout').replace(b'"host_write_barriers":7',b'"host_write_barriers":7,"host_write_barriers":7',1)
        with self.assertRaises(ValueError):m.trace(data,raw('progress','commands'),m.INPUT_SAVE)
    def test_screen_frame_mismatch(self):
        rows=[m.load(x) for x in raw('progress','stdout').splitlines()];i=next(i for i,x in enumerate(rows) if 'screen' in x)
        self.reject('frame',0,i)
    def test_regular_coordinate_mismatch(self):
        rows=[m.load(x) for x in raw('progress','stdout').splitlines()];i=next(i for i,x in enumerate(rows) if x.get('observe')==2)
        self.reject('live_xy',[0,0],i)


class PlanTests(unittest.TestCase):
    def test_exact_plan(self):self.assertTrue(m.decode_plan(PLAN)['continue'].endswith(b'observe 10\nquit\n'))
    def test_wrong_parent(self):
        plan=copy.deepcopy(PLAN);plan['input_save']=m.OUTPUT_SAVE
        with self.assertRaises(ValueError):m.decode_plan(plan)
    def test_wrong_command_binding(self):
        plan=copy.deepcopy(PLAN);plan['progress']['commands']['size']+=1
        with self.assertRaises(ValueError):m.decode_plan(plan)
    def test_helper_forbidden(self):
        with self.assertRaises(ValueError):m.commands(b'save\nquit\n')
    def test_combined_key_forbidden(self):
        with self.assertRaises(ValueError):m.commands(b'key 3 2\nquit\n')
    def test_unbounded_frames_forbidden(self):
        with self.assertRaises(ValueError):m.commands(b'key 0 601\nquit\n')
    def test_missing_or_duplicate_quit(self):
        for cmd in (b'key 0 2\n',b'quit\nquit\n'):
            with self.subTest(cmd=cmd),self.assertRaises(ValueError):m.commands(cmd)
    def test_observation_order(self):
        with self.assertRaises(ValueError):m.commands(b'observe 2\nquit\n')
    def test_truncated_compression(self):
        with self.assertRaises(ValueError):m.inflate(PLAN['progress']['commands_zlib_b85'][:-5])
    def test_bomb_and_extra_stream(self):
        import base64,zlib
        for data in (zlib.compress(b'x'*1001),zlib.compress(b'x')+zlib.compress(b'y')):
            with self.subTest(size=len(data)),self.assertRaises(ValueError):m.inflate(base64.b85encode(data).decode(),1000)


class CoordinateTests(unittest.TestCase):
    def test_specific_loading_frame(self):
        a,b=parsed();m.coordinate_boundary(a['observations'][1],m.INPUT_SAVE)
    def test_loading_on_wrong_seed(self):
        a,b=parsed()
        with self.assertRaises(ValueError):m.coordinate_boundary(a['observations'][1],m.OUTPUT_SAVE)
    def test_loading_not_generalized(self):
        a,b=parsed()
        for key,value in [('observe',2),('frame',1531),('map',[3,20]),('xy',[0,0]),('live_xy',[1,1]),
                          ('callback2',m.FIELD),('field',True),('lock',1),('party_count',3),('save_counter',20),
                          ('rp',1),('flash_sha256','0'*64),('party_sha256','0'*64)]:
            o=copy.deepcopy(a['observations'][1]);o[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.coordinate_boundary(o,m.INPUT_SAVE)


class SemanticTests(unittest.TestCase):
    def reject(self,lane,index,key,value):
        a,b=formal_fixture();(a if lane=='progress' else b)['observations'][index][key]=value
        with self.assertRaises(ValueError):m.semantic(a,b)
    def test_development_is_not_acceptance(self):
        a,b=parsed();v=m.semantic(a,b,development=True)
        self.assertEqual(v['status'],'DEVELOPMENT_NOT_ACCEPTED')
        with self.assertRaises(ValueError):m.semantic(a,b)
    def test_synthetic_formal_boundary(self):
        a,b=formal_fixture();v=m.semantic(a,b)
        self.assertEqual((v['trainer_victories'],v['wild_escapes']),(2,2))
        self.assertFalse(v['natural_growth_accepted']);self.assertFalse(v['hm05_taught_or_used'])
    def test_trainer_ko_not_victory(self):self.reject('progress',19,'battle_outcome',0)
    def test_trainer_escape_not_win(self):self.reject('progress',19,'battle_outcome',4)
    def test_wild_win_not_escape(self):self.reject('progress',45,'battle_outcome',1)
    def test_victory_reset(self):self.reject('progress',20,'battle_outcome',0)
    def test_unlocked_return_required(self):self.reject('progress',22,'lock',1)
    def test_party_count_preserved(self):self.reject('progress',34,'party_count',5)
    def test_rp_preserved(self):self.reject('continue',5,'rp',1)
    def test_wrong_route(self):self.reject('progress',34,'map',[3,21])
    def test_wrong_hm_stance(self):self.reject('progress',38,'xy',[8,5])
    def test_hm_dialogue_lock(self):self.reject('progress',38,'lock',0)
    def test_heal_required(self):
        a,b=formal_fixture();a['observations'][57]['party_sha256']=m.PARTY
        with self.assertRaises(ValueError):m.semantic(a,b)
    def test_early_save_counter(self):self.reject('progress',68,'save_counter',20)
    def test_partial_flash_not_success(self):self.reject('progress',68,'flash_sha256',m.FLASH)
    def test_last_flash_wrong(self):self.reject('progress',70,'flash_sha256','0'*64)
    def test_old_predicate_not_rewritten(self):self.reject('progress',70,'field',True)
    def test_cold_first_field(self):self.reject('continue',0,'field',False)
    def test_cold_final_menu_rejected(self):self.reject('continue',10,'lock',1)
    def test_cold_final_field_required(self):self.reject('continue',10,'field',False)
    def test_cold_party_preserved(self):self.reject('continue',5,'party_sha256','0'*64)
    def test_cold_counter_preserved(self):self.reject('continue',5,'save_counter',19)
    def test_hm_case_callback(self):self.reject('continue',5,'callback2',m.FIELD)
    def test_cold_ledger_transition_declared(self):self.reject('continue',0,'ledger_sha256',m.LEDGER)


class BytesTests(unittest.TestCase):
    def test_truncated_save(self):
        with self.assertRaises(ValueError):m.save_structure(b'\0'*100,b'\0'*100,b'\0'*100)
    def test_changed_cold_byte(self):
        with self.assertRaises(ValueError):m.save_structure(b'\0'*131088,b'\0'*131088,b'x'+b'\0'*131087)
    def test_s61e_crc_refuses_invalid_record(self):
        with self.assertRaises(ValueError):m.s61e_record(b'\0'*1558)
    def test_wrong_rom(self):
        with self.assertRaises(ValueError):m.owners(b'not a ROM')
    def test_blank_anchor_rejected(self):
        value=b'P6\n240 160\n255\n'+bytes(240*160*3)
        with self.assertRaises(ValueError):m.screen_bytes(value,dict(sha256=m.identity(value)['sha256']))
    def test_native_process_not_used_by_gates(self):
        import unittest.mock
        with unittest.mock.patch('subprocess.run',side_effect=AssertionError('native forbidden')):
            a,b=parsed();m.semantic(a,b,development=True)


if __name__=='__main__':unittest.main()
