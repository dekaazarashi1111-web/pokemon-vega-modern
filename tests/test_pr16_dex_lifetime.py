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
  self.rows=[dict(fixture='VALID_MDX_UNSAVED_RAM_ONLY',case='bag'),*[dict(screen='screen-00.ppm',stage=x,sha256=m.identity(screen)['sha256'],lock=0)for x in ['loaded-field','bag','returned-field']],dict(status='PASS_UNSAVED_MDX_UI_LIFETIME_ONLY',case='bag',whole_owner_bytes=522,fixture_bytes=522,host_write_barriers=7,ordinary_saves=0,runtime_wired=False,rom_changed=False,story_progress_accepted=False,fixture_calls=0)]
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
  raw=b'P6\n240 160\n255\n'+b'\0'*115200;(m.OUT/'bag/screen-00.ppm').write_bytes(raw)
  for r in self.rows:
   if 'screen'in r:r['sha256']=m.identity(raw)['sha256']
  self.assertRaises(ValueError,self.validate)
if __name__=='__main__':unittest.main()
