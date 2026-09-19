"""18戦目のreadonly境界traceは受入と分離し、完了/未完を厳密に分類する。"""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_drought_launch_boundary as t

class LaunchBoundaryTests(unittest.TestCase):
    def row(self,**change):
        value=dict(frame=100,keys=0,callback2=0x0811F3A9,script=0x09FF4DAD,newbs=0,weather_state=2,complete=0,index=1,offset=1,
            weather=12,next_weather=12,ready=1,brightness=0,phase=2,outcome=0,current=17,best=17,count=3,types=0x04000000,
            field_wait=0,tasks='00'*640,weather_raw='00'*160,owner='00'*64)
        value.update(change);return value
    def completed(self):
        return [self.row(),self.row(frame=120,callback2=0x08055E75,script=0,weather_state=5,complete=1,index=32,offset=32,field_wait=1),
            self.row(frame=299,callback2=0x08055E75,script=0,weather_state=5,complete=1,index=32,offset=32,field_wait=180)]
    def test_completed_then_field_drop(self):
        value=t.analyze_boundary(self.completed())
        self.assertEqual(value['classification'],'CIRCUS_DROUGHT_LAUNCH_COMPLETED_THEN_FIELD_DROP')
        self.assertTrue(value['weather_completed']);self.assertEqual(value['persistent_field_frames'],180)
    def test_incomplete_return_is_separate(self):
        rows=self.completed()
        for row in rows[1:]:row.update(weather_state=2,complete=0,index=1,offset=1)
        value=t.analyze_boundary(rows)
        self.assertEqual(value['classification'],'CIRCUS_DROUGHT_LAUNCH_RETURNED_INCOMPLETE');self.assertFalse(value['weather_completed'])
    def test_missing_chooser_or_context_drift_rejected(self):
        rows=self.completed();rows[0]['script']=0
        with self.assertRaises(ValueError):t.analyze_boundary(rows)
        rows=self.completed();rows[-1]['current']=18
        with self.assertRaises(ValueError):t.analyze_boundary(rows)
    def test_raw_shapes_and_persistent_endpoint_required(self):
        rows=self.completed();rows[-1]['tasks']='00'
        with self.assertRaises(ValueError):t.analyze_boundary(rows)
        rows=self.completed();rows[-1]['field_wait']=179
        with self.assertRaises(ValueError):t.analyze_boundary(rows)
    def test_watch_chain_exact_and_not_repeatable(self):
        base='static void fw_frame(void){}\n#define b_frame fw_frame\n'
        header='static void lb_frame(void){b_frame(c,keys);}\n#undef b_frame\n#define b_frame lb_frame\n'
        result=t.append_watch(base,header);self.assertIn('#define b_frame lb_frame',result)
        with self.assertRaises(ValueError):t.append_watch(result,header)
    def test_boundary_watch_is_composed_after_fade_chain(self):
        fade='static void fw_frame(void){b_frame(c,keys);}\n#define b_frame fw_frame\n'
        header='static void lb_frame(void){b_frame(c,keys);}\n#undef b_frame\n#define b_frame lb_frame\n'
        def chain(text):return text.replace('b_frame(c,keys);','wr_frame(c,keys);')
        result=t.compose_boundary_watch(fade,header,chain)
        self.assertIn('wr_frame(c,keys);',result)
        self.assertLess(result.index('#define b_frame fw_frame'),result.index('static void lb_frame'))
        self.assertTrue(result.rstrip().endswith('#define b_frame lb_frame'))
    def test_previous_setup_failure_is_native_zero_only(self):
        previous=dict(classification='CIRCUS_DROUGHT_LAUNCH_BOUNDARY_OPEN',recording_run=t.FAILED_RUN,diagnostic_complete=False)
        failed=dict(status='FAIL',actual_new_processes=0,successful_fresh_cores=0,results=[],
            failures=[{'stage':'setup-or-execution','error':'inherited frame watcher boundary'}])
        run=dict(id=t.FAILED_RUN,head_sha=t.FAILED_HEAD,status='completed',conclusion='failure')
        artifact=dict(id=t.FAILED_ARTIFACT,digest=t.FAILED_DIGEST,expired=False,workflow_run={'id':t.FAILED_RUN})
        value=t.validate_retry_failure(previous,failed,run,artifact)
        self.assertEqual(value['native_processes'],0);self.assertEqual(value['accepted_native_cases_replayed'],0)
        failed=dict(failed,actual_new_processes=1)
        with self.assertRaises(ValueError):t.validate_retry_failure(previous,failed,run,artifact)
    def test_tracked_header_is_readonly_and_bounded(self):
        text=(ROOT/t.HEADER).read_text()
        for token in ('write8(','write16(','write32(','setKeys(','call_preserving('):self.assertNotIn(token,text)
        self.assertIn('b_frame(c,keys);',text);self.assertIn('lb_field_wait==180U',text)
        self.assertIn('#undef b_frame',text);self.assertIn('#define b_frame lb_frame',text)

if __name__=='__main__':unittest.main()
