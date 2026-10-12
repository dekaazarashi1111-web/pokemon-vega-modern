"""今回新規Save101だけの独立受入。native再走なし。"""
import copy,json,os,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save101_accept as a
class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=pathlib.Path(os.environ['PR16_SAVE101_ORIGINAL']);cls.before=pathlib.Path(os.environ['PR16_SAVE100_INPUT']).read_bytes();cls.rom=pathlib.Path(os.environ['PR16_SAVE101_ROM']).read_bytes();cls.pa=a.trace(cls.root/'progress',a.m.a.OUTPUT);cls.pb=a.trace(cls.root/'continue',a.OUTPUT)
    def boundary(self):s=(self.root/'story-fast.srm').read_bytes();return a.boundary(self.before,s,s,self.rom)
    def frames(self):return[(self.root/n).read_bytes()for n in['progress/screen-0032.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    def test_exact_original(self):self.assertTrue(a.verify(self.root,self.before,self.rom)['west_connection_accepted'])
    def test_scope(self):r=a.semantics(self.pa,self.pb);self.assertEqual((r['travel_steps'],r['turns'],r['warps'],r['map_connections']),(5,1,0,1));self.assertFalse(r['full_story_accepted']);self.assertFalse(r['native_battle_continuation_accepted']);self.assertEqual(r['compact_battle_ledger'],[])
    def test_region_milestone(self):r=a.semantics(self.pa,self.pb);self.assertEqual(r['milestone_kind'],'region_connection');self.assertFalse(r['diagnostic_frontier_completed']);self.assertFalse(r['ordinary_battle_checkpoint'])
    def test_party_and_flags(self):r=self.boundary();self.assertEqual(r['party_byte_deltas'],[]);self.assertEqual(r['physical_flag_deltas'],[])
    def test_party_mutation(self):
        with self.assertRaises(ValueError):a.party_delta(b'\0'*600,b'\1'+b'\0'*599)
    def test_flag_mutation(self):
        with self.assertRaises(ValueError):a.flags_delta(b'\0'*288,b'\1'+b'\0'*287)
    def test_hp_pp(self):r=self.boundary();self.assertEqual((r['hp'],r['pp']),([277,294],[3,9,8,2]))
    def test_walk_counter(self):self.assertEqual(self.boundary()['variable_deltas'],[(0x4021,93,98)])
    def test_expanded_flags(self):r=self.boundary();self.assertEqual(r['s61e_payload_deltas'],[]);self.assertEqual(r['expanded_flag_deltas'],[]);self.assertEqual([r['expanded_flags'][str(f)]for f in(4352,4380,4382,4383)],[1]*4)
    def test_save_states(self):o=self.pa['observations'];self.assertEqual(o[27]['save_counter'],101);self.assertNotEqual(o[27]['flash_sha256'],a.FLASH);self.assertEqual(o[28]['flash_sha256'],a.FLASH);self.assertFalse(o[28]['field']);self.assertTrue(o[32]['field'])
    def test_cold_save_changed(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before,s,s[:-1]+bytes([s[-1]^1]),self.rom)
    def test_input_changed(self):
        s=(self.root/'story-fast.srm').read_bytes()
        with self.assertRaises(ValueError):a.boundary(self.before[:-1]+bytes([self.before[-1]^1]),s,s,self.rom)
    def test_rom_changed(self):
        s=(self.root/'story-fast.srm').read_bytes();b=bytearray(self.rom);b[0]^=1
        with self.assertRaises(ValueError):a.boundary(self.before,s,s,bytes(b))
    def test_diff_accounting(self):r=self.boundary();self.assertEqual((r['changed_bytes'],r['changed_ranges'],r['sector_checksum_checks'],r['old_bank_preserved_bytes']),(7128,1807,42,57344))
    def test_resources(self):r=self.boundary();self.assertEqual((r['paper_quantity'],r['money_before'],r['money_after'],r['museum_admission_var4061'],r['badge_count']),(0,23114,23114,1,2))
    def test_ram_same_not_old_owner_resolved(self):r=a.semantics(self.pa,self.pb);self.assertTrue(r['progress_to_cold_ram_ledger_identical']);self.assertFalse(r['prior_save100_ram_difference_owner_resolved'])
    def test_pixel_scope(self):r=a.screen_comparison(self.frames());self.assertEqual(r['progress_to_cold_changed_pixels'],[588,0]);self.assertEqual(r['cold_changed_pixels'],588);self.assertTrue(r['progress_equals_settled_cold'])
    def test_player_pixel_rejected(self):
        f=self.frames();b=bytearray(f[1]);b[15+3*(100+80*240)]^=1;f[1]=bytes(b)
        with self.assertRaises(ValueError):a.screen_comparison(f)
    def test_declared_next_facility(self):p=a.next_route();self.assertEqual(p['milestone_contract']['id'],'SHIOU_POKEMON_CENTER_NORMAL_RECOVERY');self.assertEqual([v['map']for v in p['static_map_chain']],[[3,24],[3,37],[3,3],[7,3]]);self.assertFalse(p['milestone_contract']['runtime_route_authorized'])
    def test_nurse_counter_not_walkable(self):p=a.next_route();self.assertEqual(p['facility_owner']['counter_between'],[7,3]);self.assertEqual(p['milestone_contract']['endpoint']['xy'],[7,4]);c=[t for t in p['terrain_preflight']if t['map']==[7,3]and t['xy']==[7,3]][0];self.assertEqual((c['collision'],c['behavior']),(1,128))
    def test_next_static_bytes(self):p=a.next_route();self.assertTrue(all(self.rom[x['address']-0x8000000:x['address']-0x8000000+x['size']].hex()==x['hex']for x in p['bindings']))
    def test_gym_owner(self):p=a.next_route()['downstream_major_badge'];self.assertEqual(p['badge_flag'],2084);self.assertTrue(any(x['category']=='trainer'and x['value']==418 for x in p['owner_refs']));self.assertFalse(p['native_accepted'])

def reject(lane,index,key,value):
    def case(self):
        pa,pb=copy.deepcopy(self.pa),copy.deepcopy(self.pb);(pa if lane=='progress'else pb)['observations'][index][key]=value
        with self.assertRaises(ValueError):a.semantics(pa,pb)
    return case
for i,(lane,index,key,value)in enumerate([
 ('progress',0,'facing',3),('progress',1,'xy',[3,17]),('progress',5,'map',[3,24]),('progress',6,'xy',[52,13]),('progress',6,'facing',4),('progress',6,'lock',1),('progress',6,'field',False),('progress',6,'callback2',999),('progress',6,'party_count',3),('progress',6,'rp',1),('progress',6,'battle_flags',8),('progress',6,'battle_outcome',1),('progress',6,'party_sha256','0'*64),('progress',6,'ledger_sha256','0'*64),('progress',6,'flash_sha256',a.FLASH),('progress',26,'save_counter',101),('progress',27,'flash_sha256',a.FLASH),('progress',28,'field',True),('progress',32,'field',False),('continue',0,'xy',[0,17]),('continue',0,'facing',2),('continue',1,'ledger_sha256','0'*64),('continue',1,'party_sha256','0'*64),('continue',1,'save_counter',100),('continue',1,'flash_sha256',a.m.a.FLASH)]):setattr(Acceptance,'test_reject_observation_'+str(i),reject(lane,index,key,value))
if __name__=='__main__':unittest.main()
