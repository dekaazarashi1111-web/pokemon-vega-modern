"""UI限定証拠のvalidator。ゲーム進行・保存ABI受入への誤昇格を拒否。"""
import copy,importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('life',Path(__file__).resolve().parents[1]/'scripts/pr16_dex_lifetime.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class LifetimeEvidence(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();m.OUT=Path(self.temp.name);(m.OUT/'bag').mkdir()
  screen=b'P6\n240 160\n255\n'+b'\0\1\2'*38400;(m.OUT/'bag/screen-00.ppm').write_bytes(screen)
  # 二色の実サイズfixture。黒一色やSHAだけのdummyは拒否。
  screen=screen[:-3]+b'\1\2\3';(m.OUT/'bag/screen-00.ppm').write_bytes(screen)
  for i in range(3):(m.OUT/f'bag/screen-{i:02d}.ppm').write_bytes(screen)
  screens=[dict(screen=f'screen-{i:02d}.ppm',stage=x,sha256=m.identity(screen)['sha256'],lock=0,frame=0,callback=0x08055E75,pss=0,cursor_area=0,cursor_position=0)for i,x in enumerate(['loaded-field','bag','returned-field'])]
  self.rows=[dict(fixture='VALID_MDX_UNSAVED_RAM_ONLY',address=0x0203DB40,case='bag',frame=0,**m.fixture_identity()),*screens,dict(status='PASS_UNSAVED_MDX_UI_LIFETIME_ONLY',case='bag',whole_owner_bytes=522,fixture_bytes=522,host_write_barriers=7,ordinary_saves=0,runtime_wired=False,rom_changed=False,story_progress_accepted=False,fixture_calls=0,frames=0,inputs=0,checks=1,native_processes=1,observed_owner_store_calls=0)]
 def tearDown(self):self.temp.cleanup()
 def validate(self,rows=None):return m.validate(('\n'.join(json.dumps(x)for x in (self.rows if rows is None else rows))+'\n').encode(),'bag')
 def reject(self,key,value):self.rows[-1][key]=value;self.assertRaises(ValueError,self.validate)
 def test_valid_scoped_evidence(self):self.assertEqual(self.validate()[0]['case'],'bag')
 def test_save_not_allowed(self):self.reject('ordinary_saves',1)
 def test_wired_not_claimed(self):self.reject('runtime_wired',True)
 def test_rom_change_not_allowed(self):self.reject('rom_changed',True)
 def test_story_not_claimed(self):self.reject('story_progress_accepted',True)
 def test_partial_owner_rejected(self):self.reject('whole_owner_bytes',151)
 def test_wrong_fixture_rejected(self):self.reject('fixture_bytes',523)
 def test_barrier_missing(self):self.reject('host_write_barriers',6)
 def test_undeclared_call(self):self.reject('fixture_calls',1)
 def test_wrong_case(self):self.reject('case','pc')
 def test_terminal_failure(self):self.reject('status','PASS')
 def test_duplicate_terminal(self):self.rows.append(copy.deepcopy(self.rows[-1]));self.assertRaises(ValueError,self.validate)
 def test_duplicate_fixture(self):self.rows.append(copy.deepcopy(self.rows[0]));self.assertRaises(ValueError,self.validate)
 def test_missing_ui(self):self.rows[2]['stage']='unknown';self.assertRaises(ValueError,self.validate)
 def test_not_field_return(self):self.rows[3]['lock']=1;self.assertRaises(ValueError,self.validate)
 def test_bad_screen_hash(self):self.rows[2]['sha256']='0'*64;self.assertRaises(ValueError,self.validate)
 def test_blank_screen(self):
  raw=b'P6\n240 160\n255\n'+b'\0'*115200
  for i in range(3):(m.OUT/f'bag/screen-{i:02d}.ppm').write_bytes(raw)
  for r in self.rows:
   if 'screen'in r:r['sha256']=m.identity(raw)['sha256']
  self.assertRaises(ValueError,self.validate)
 def test_native_clobber_rejected(self):self.rows.insert(1,dict(clobber=True));self.assertRaises(ValueError,self.validate)
 def test_unowned_store_rejected(self):self.rows.insert(1,dict(unowned_store=True));self.assertRaises(ValueError,self.validate)
 def test_wrong_fixture_address(self):self.rows[0]['address']=0x0203D000;self.assertRaises(ValueError,self.validate)
 def test_wrong_fixture_hash(self):self.rows[0]['sha256']='0'*64;self.assertRaises(ValueError,self.validate)
 def test_store_count_rejected(self):self.reject('observed_owner_store_calls',1)
 def test_missing_native(self):self.reject('native_processes',0)
 def test_missing_frames_check(self):self.reject('checks',0)
 def test_path_traversal(self):self.rows[2]['screen']='../screen-01.ppm';self.assertRaises(ValueError,self.validate)
 def test_wrong_frame(self):self.rows[2]['frame']=1;self.assertRaises(ValueError,self.validate)
 def test_wrong_callback(self):self.rows[3]['callback']=0;self.assertRaises(ValueError,self.validate)
 def test_unknown_record(self):self.rows.insert(1,dict(raw='data'));self.assertRaises(ValueError,self.validate)
 def test_input_order(self):self.rows.insert(1,dict(input=2,frame=0,key=1,frames=2));self.assertRaises(ValueError,self.validate)
 def test_boolean_native(self):self.reject('native_processes',True)
if __name__=='__main__':unittest.main()
