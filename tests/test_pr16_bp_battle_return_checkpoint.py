"""失敗の固定観測・原本・受入境界を検証する。native起動なし。"""
import io
from pathlib import Path
import sys
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_bp_battle_return_checkpoint as c


def trace():
    def row(label,frame,**kw):
        base=dict(frame=frame,cb2='080109c1',main='08013861',command=18,ctrl='0802dc15',exec=3,newbs='02017634',outcome=0,index=0,hp=119,enemy_hp=139,slot=6,script='092cf669',pending=0,streak=0,snapshot=1,marker=2,count=3,bp=0,save=2)
        base.update(kw)
        return 'BP_RETURN label='+label+' '+ ' '.join(k+'='+str(v) for k,v in base.items())
    rows=[row('extension-start',3925),row('turn-stop',11261,outcome=2,hp=0),
          row('transition',11405,outcome=2,cb2='08055f65',newbs='00000000'),
          row('transition',11525,outcome=2,cb2='08055f65',newbs='00000000',script='00000000'),
          row('facility-stop',93925,outcome=2,cb2='08055e75',newbs='00000000',script='00000000'),
          'BP_CTRL label=three-selected frame=1440','BP_CTRL label=post-selection frame=1789',
          'BREED facility-afterbattle map=4/0 xy=8,5 party=3',
          'P03 archive: first battle did not reach native AfterBattle return',
          'BP_RETURN label=forced-switch-return frame=6682','BP_RETURN label=forced-switch-return frame=8001']
    rows += [f'BP_RETURN_MOVE turn={i} pp_event={4000+i}' for i in range(1,9)]
    return ('\n'.join(rows)+'\n').encode()

class ReturnEvidenceTests(unittest.TestCase):
    def test_observed_loss_is_not_afterbattle_acceptance(self):
        row=c.failed_observations(trace())
        self.assertEqual((row['loss_frame'],row['whiteout_frame'],row['final_frame']),(11261,11405,93925))
        self.assertEqual(row['raw_native_status'],'FAIL')
        for key in ('native_afterbattle_observed','original_party_restoration_verified','native_bp_earning_accepted','p05_native_bp_gap_closed','release_ready'):
            self.assertIs(row[key],False)
    def test_no_relaxation_or_success_relabelling(self):
        for before,after in ((b'outcome=2',b'outcome=1'),(b'bp=0',b'bp=9'),(b'save=2',b'save=3'),
            (b'count=3',b'count=1'),(b'snapshot=1',b'snapshot=0'),(b'08055f65',b'080109c1'),
            (b'frame=11261',b'frame=11262'),(b'frame=93925',b'frame=11525'),
            (b'pp_event=4001',b'pp_event=0'),(b'map=4/0',b'map=96/5')):
            with self.subTest(before=before):
                with self.assertRaises(ValueError):c.failed_observations(trace().replace(before,after))
    def test_missing_or_duplicate_witness(self):
        for raw in (b'',trace()+trace(),trace().replace(b'BP_RETURN label=extension-start ',b'OTHER ')):
            with self.assertRaises(ValueError):c.failed_observations(raw)
    def test_positive_archive_scanner(self):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:z.writestr('a.json',b'{}\n')
        c.scan(out.getvalue())
    def test_reject_private_archive_paths(self):
        for name,data in (('../escape.txt',b'x'),('/root.txt',b'x'),('a.gba',b'x'),('a.srm',b'x'),('nested.zip',b'x'),('a.txt',b'\x00')):
            with self.subTest(name=name):
                out=io.BytesIO()
                with zipfile.ZipFile(out,'w') as z:z.writestr(name,data)
                with self.assertRaises(ValueError):c.scan(out.getvalue())
    def test_reject_credentials_without_allowlist(self):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:z.writestr('x.txt',b'ghp_'+b'A'*36)
        with self.assertRaises(ValueError):c.scan(out.getvalue())
    def test_metadata_and_native_caps_are_separate(self):
        with self.assertRaises(ValueError):c.parse(b' '* (4*1024*1024+1))
        with self.assertRaises(ValueError):c.native.validate(b'',b'',1)
    def test_outer_digest_required(self):
        with self.assertRaises(ValueError):c.verify(b'changed',c.PINS[0])
    def test_retained_original_when_present(self):
        path=c.ROOT/c.BASE/('original-'+str(c.PINS[0][0])+'.zip')
        if not path.exists():self.skipTest('closeout retains exact original before integration tests')
        row=c.verify(path.read_bytes(),c.PINS[0])
        self.assertEqual(row['original_conclusion'],'failure')
        self.assertEqual(row['new_emulator_processes'],1)
        self.assertEqual(row['successful_fresh_cores'],0)

if __name__=='__main__':unittest.main()
