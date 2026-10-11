import copy,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts')]
import pr16_dex_save_failure_ui as u
class NegativeUI(unittest.TestCase):
 def test_single_crc_exception_with_seven_barriers(self):u.validate_header((ROOT/u.HEADER).read_text())
 def test_no_extra_write_exception(self):
  s=(ROOT/u.HEADER).read_text()
  for extra in ['sf_fixture_write8(c,0,0);','si_restore(c,0);','si_call(c,0);','write_register(c,0);']:
   with self.assertRaises(ValueError):u.validate_header(s+extra)
 def test_barrier_must_precede_first_frame(self):
  s=(ROOT/u.HEADER).read_text().replace('si_guard(c);','')
  with self.assertRaises(ValueError):u.validate_header(s+'si_guard(c);')
 def test_closed_trace_rejects_missing_or_mispaired_records(self):
  with tempfile.TemporaryDirectory()as temp:
   folder=Path(temp);raw=b'P6\n240 160\n255\n'+b'\1\0\0'+bytes(240*160*3-3);sha=u.identity(raw)['sha256']
   rows=[dict(begin='EXPLICIT_CRC_NEGATIVE_SAVE_FAILURE_UI',candidate_sha256='0'*64,host_write_barriers=7,formal_save_changed=False)]
   for i,stage in enumerate(['injected_at_field','ordinary_error_first_page','ordinary_save_error','field_after_failure']):
    rows.append(dict(input=i,frame=i,key=0,frames=1))
    if i==0:rows.append(dict(fixture_calls=1,fixture_bytes=1,address=0x0203DB44,old=0,new=1,register_writes=0,other_host_writes=0))
    rows.append(dict(failure_ui_stage=stage,frame=i+1,active=0,state=0,attempt=255 if i else 0,callback=0x0806F1F5 if i==1 else 0x0806F21D if i==2 else 0,delay=0,counter=101,damaged_mask=0));rows.append(dict(screen=i,frame=i+1,sha256=sha));(folder/('screen-'+str(i).zfill(4)+'.ppm')).write_bytes(raw)
   rows.append(dict(end='PASS_EXPLICIT_CRC_FIXTURE_SAVE_FAILURE_UI',frames=4,inputs=4,screens=4,fixture_calls=1,fixture_bytes=1,host_write_barriers=7,other_host_writes=0,register_writes=0,save_attempts=1,save_commits=0,counter=101,all_flash_unchanged=True,authority_present=True,story_progress_accepted=False,destructive_save_failed_entered=False,error_page_advances=1))
   encode=lambda x:('\n'.join(json.dumps(r)for r in x)+'\n').encode()
   u.validate(encode(rows),folder,'0'*64)
   for index,key,value in [(0,'candidate_sha256','1'*64),(1,'input',3),(1,'key',99),(2,'other_host_writes',1),(4,'screen',1),(4,'frame',2),(5,'frame',99)]:
    changed=copy.deepcopy(rows);changed[index][key]=value
    with self.assertRaises(ValueError):u.validate(encode(changed),folder,'0'*64)
if __name__=='__main__':unittest.main()
