"""Save83東5歩・trainer160新1勝・保存/Continueを原本から独立受入。"""
import copy,os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save83_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE83_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE82_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE83_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def test_exact_original(self):self.assertEqual(a.verify(self.root,self.before,self.rom)['trainer_victories'],1)
    def test_limited_claims(self):
        r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['trainer_victories'],r['wild_victories']),(5,1,0));self.assertFalse(r['gym_puzzle_completed']);self.assertFalse(r['gym_leader_defeated']);self.assertFalse(r['hm05_taught_or_used']);self.assertFalse(r['full_story_accepted']);self.assertFalse(r['paper_consumed_or_delivered'])
    def test_cold_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_parent_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_rom_all_bytes(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s,self.rom[:-1]+bytes([self.rom[-1]^1]))
    def test_party_two_pp_and_hp_bytes_only(self):
        s=a.parent.sectors;b,_=s.bank(self.before,0,82,s.LAYOUT);raw=(self.root/'story-fast.srm').read_bytes();c,_=s.bank(raw,0xe000,83,s.LAYOUT);self.assertEqual(a.party_delta(self.before[b[1]+56:b[1]+656],raw[c[1]+56:c[1]+656]),[(52,6,4),(54,14,12),(86,32,31)])
    def test_extra_party_rejected(self):
        with self.assertRaises(ValueError):a.party_delta(bytes(600),b'\x01'+bytes(599))
    def test_new_legacy_flag_rejected(self):
        with self.assertRaises(ValueError):a.flags_delta(bytes(0x120),b'\x01'+bytes(0x11f))
    def test_paths(self):self.assertEqual(a.GUIDE,'docs/PR16_STORY_SAVE83_JA.md');self.assertEqual(a.CP,'content/modernization/pr16_story_save83_checkpoint.json')
    def test_no_owner_overclaim(self):
        r=a.semantics(self.pa,self.pb)
        for k in ['ram_difference_owner_resolved','party_byte41_runtime_owner_resolved','old_save52_cold_difference_owner_resolved','healing_ram_ledger_owner_resolved','old_save77_cold_difference_owner_resolved','old_save78_progress_difference_owner_resolved','old_save80_progress_difference_owner_resolved','npc_runtime_object_id_resolved']:self.assertFalse(r[k])
    def test_counter_is_not_completion(self):self.assertNotEqual(a.FLASH_PHASES[-1],a.FLASH)
    def test_all_field_frame_bytes_identical(self):self.assertEqual((self.root/'progress/screen-0067.ppm').read_bytes(),(self.root/'continue/screen-0001.ppm').read_bytes())
    def test_original_trace(self):self.assertEqual(len(a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)['observations']),68)
    def test_extra_hidden_row_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes()+b'{}\n',(self.root/'progress/commands.txt').read_bytes(),a.m.a.OUTPUT)
    def test_wrong_seed_rejected(self):
        with self.assertRaises(ValueError):a.trace_rows((self.root/'progress/stdout.txt').read_bytes(),(self.root/'progress/commands.txt').read_bytes(),a.OUTPUT)
    def test_native_trainer_and_no_leader(self):
        d=a.semantics(self.pa,self.pb);self.assertEqual(d['trainer_id'],160);self.assertEqual(d['physical_trainer_bit'],1440);self.assertEqual(d['reward_yen'],384);self.assertEqual(d['observed_pp_consumption'],[2,0,2,0]);self.assertEqual(d['keep_current_choices'],3);self.assertFalse(d['gym_leader_defeated'])
    def test_static_next_four_edges(self):
        n=a.next_route();self.assertEqual((n['start'],n['interaction']['from_xy'],len(n['route'])-1),([11,7],[11,3],4));self.assertEqual(n['expected_flag_changes'],[[4374,0,1],[4376,1,0]])
    def test_static_scope(self):
        n=a.next_route();self.assertFalse(n['route_native_accepted']);self.assertFalse(n['gym_puzzle_accepted']);self.assertFalse(n['old_switch_inputs_replayed']);self.assertTrue(n['source_graph_reused'])
    def test_incomplete_screens_rejected(self):
        p=copy.deepcopy(self.pa);p['observations'].pop()
        with self.assertRaises(ValueError):a.semantics(p,self.pb)
    def test_incorrect_input_count_rejected(self):
        p=copy.deepcopy(self.pa);p['end']['inputs']+=1
        with self.assertRaises(ValueError):a.semantics(p,self.pb)
    def test_cold_extra_input_rejected(self):
        q=copy.deepcopy(self.pb);q['end']['inputs']+=1
        with self.assertRaises(ValueError):a.semantics(self.pa,q)
    def rejected(self,lane,index,key,value):
        p,q=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(p if lane=='progress'else q)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(p,q)
def case(lane,index,key,value):return lambda self:self.rejected(lane,index,key,value)
CASES={'origin': ('progress', 0, 'map', [3, 2]), 'start': ('progress', 0, 'xy', [6, 8]), 'first_east': ('progress', 2, 'xy', [6, 7]), 'facing': ('progress', 1, 'facing', 2), 'encounter_xy': ('progress', 6, 'xy', [11, 6]), 'encounter_lock': ('progress', 6, 'lock', 0), 'encounter_field': ('progress', 6, 'field', True), 'intro_callback': ('progress', 8, 'callback2', a.m.m.BATTLE), 'battle_callback': ('progress', 9, 'callback2', a.m.m.FIELD), 'battle_flag': ('progress', 9, 'battle_flags', 4), 'early_outcome': ('progress', 41, 'battle_outcome', 1), 'outcome': ('progress', 42, 'battle_outcome', 0), 'party_count': ('progress', 9, 'party_count', 3), 'rp': ('progress', 9, 'rp', 1), 'early_party': ('progress', 15, 'party_sha256', a.PARTIES[1]), 'first_pp': ('progress', 16, 'party_sha256', a.PARTIES[0]), 'hp_change': ('progress', 23, 'party_sha256', a.PARTIES[1]), 'second_pp': ('progress', 24, 'party_sha256', a.PARTIES[2]), 'third_pp': ('progress', 33, 'party_sha256', a.PARTIES[3]), 'fourth_pp': ('progress', 40, 'party_sha256', a.PARTIES[4]), 'early_ledger': ('progress', 16, 'ledger_sha256', a.TRANSIENT_LEDGER), 'transient_ledger': ('progress', 17, 'ledger_sha256', a.m.a.LEDGER), 'final_ledger': ('progress', 38, 'ledger_sha256', a.TRANSIENT_LEDGER), 'field_map': ('progress', 45, 'map', [3, 2]), 'field_xy': ('progress', 45, 'xy', [11, 8]), 'field_facing': ('progress', 45, 'facing', 2), 'field_lock': ('progress', 45, 'lock', 1), 'field_wire': ('progress', 45, 'field', False), 'menu_lock': ('progress', 46, 'lock', 0), 'menu_field': ('progress', 46, 'field', True), 'early_counter': ('progress', 61, 'save_counter', 83), 'missing_counter': ('progress', 62, 'save_counter', 82), 'old_flash': ('progress', 52, 'flash_sha256', a.FLASH), 'partial_flash': ('progress', 53, 'flash_sha256', a.FLASH), 'counter_partial': ('progress', 62, 'flash_sha256', a.FLASH), 'final_hash': ('progress', 63, 'flash_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'final_lock': ('progress', 67, 'lock', 1), 'cold_map': ('continue', 0, 'map', [3, 2]), 'cold_xy': ('continue', 0, 'xy', [11, 8]), 'cold_facing': ('continue', 0, 'facing', 3), 'cold_counter': ('continue', 0, 'save_counter', 82), 'cold_party': ('continue', 1, 'party_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'cold_flash': ('continue', 1, 'flash_sha256', a.m.a.FLASH), 'cold_ledger': ('continue', 1, 'ledger_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), 'cold_battle': ('continue', 1, 'battle_flags', 12), 'cold_outcome': ('continue', 1, 'battle_outcome', 1)}
for name,args in CASES.items():setattr(Acceptance,'test_reject_'+name,case(*args))
if __name__=='__main__':unittest.main()

