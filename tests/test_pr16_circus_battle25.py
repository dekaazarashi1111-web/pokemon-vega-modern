"""25戦目限定入力の純粋C、厳密変換、原本prefixの改作拒否。nativeは起動しない。"""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import pr16_circus_battle25_policy as p
import pr16_circus_continuous_probe as probe
ORIGINAL = Path(os.environ.get('B25_ORIGINALS', str(ROOT/'.local/pr16-circus-battle25/original')))


class Battle25Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = (ORIGINAL/'generated/pr16_streak_policy.c').read_text()
        cls.header = (ROOT/'tools/mgba_pr16_circus_battle25.h').read_text()
        cls.trace = (ORIGINAL/(probe.CASE+'.stderr')).read_bytes()
        cls.events = probe.parse(cls.trace)

    def test_c_rank_prefix_coverage_actual_pool_and_overflow(self):
        start = self.policy.index('static unsigned wx_effect(unsigned attack,unsigned defense) {')
        effect = self.policy[start:self.policy.index('static unsigned wx_move_slot', start)]
        fixture = r'''
#include <assert.h>
#include <string.h>
int main(void) {
    const uint64_t scores[6]={158984100,285111450,328473600,140659200,103488000,270590400};
    const uint32_t masks[6]={0x2001,0x1008,0x20001,0x45,1,0x80};
    unsigned old[3],now[3]; uint64_t ranked[6];
    b25_legacy_plan(scores,masks,old);
    assert(old[0]==2 && old[1]==1 && old[2]==5);
    for(unsigned streak=0;streak<24;++streak) {
        for(unsigned i=0;i<6;++i) { ranked[i]=b25_rank(streak,scores[i],masks[i]); assert(ranked[i]==scores[i]); }
        b25_legacy_plan(ranked,masks,now); assert(!memcmp(old,now,sizeof(old)));
    }
    for(unsigned i=0;i<6;++i) ranked[i]=b25_rank(24,scores[i],masks[i]);
    b25_legacy_plan(ranked,masks,now);
    assert(now[0]==2 && now[1]==1 && now[2]==0);
    assert(b25_rank(24,100,1U<<7)==25);
    assert(b25_rank(24,100,(1U<<7)|1U)==100);
    assert(b25_rank(24,100,0x2001)==100);
    assert(b25_rank(24,100,1U<<24)==100);
    assert(b25_rank(24,100,0)==0 && b25_rank(24,100,1U<<25)==0);
    assert(b25_rank(23,UINT64_MAX,0)==UINT64_MAX);
    assert(b25_rank(24,UINT64_MAX,1U<<7)==UINT64_MAX/4);
    const uint64_t ties[6]={8,8,8,8,8,8};
    b25_legacy_plan(ties,masks,now); assert(now[0]==0 && now[1]==1 && now[2]==2);
    assert(scores[5]==270590400 && masks[5]==0x80);
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            src,exe=Path(tmp)/'test.c',Path(tmp)/'test'
            src.write_text(self.header+'\n'+effect+'\n'+fixture)
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(src),'-o',str(exe)],check=True,capture_output=True)
            subprocess.run([str(exe)],check=True,capture_output=True)

    def test_exact_source_transform_and_no_writes(self):
        new=p.adapt(self.policy,self.header)
        self.assertEqual(new.count('uint64_t score=b25_rank('),1)
        self.assertEqual(new.count('CIRCUS_BATTLE25_INPUT_CHANGE'),1)
        self.assertEqual(new.count('wx_cursor(c,best);sp_entry(c,n,best);'),self.policy.count('wx_cursor(c,best);sp_entry(c,n,best);'))
        for forbidden in ('write8','write16','write32','rawWrite','setRegister','runFrame','setKeys'):
            self.assertNotIn(forbidden,self.header)

    def test_altered_original_and_ambiguous_anchor_rejected(self):
        for text in (self.policy+' ',self.policy.replace('scores[i]','scores[0]',1)):
            with self.assertRaises(ValueError):p.adapt(text,self.header)
        for text in ('','xx'):
            with self.assertRaises(ValueError):p.replace_once(text,'x','y')

    def synthetic(self):
        anchor=b'CIRCUS_SUSTAIN_TEAM index=2 original_slot=5 '
        position=self.trace.rindex(anchor)
        marker=dict(frame=403999,streak=24,index=2,old_slot=5,new_slot=0)
        raw=self.trace[:position]+p.MARKER+json.dumps(marker).encode()+b'\n'+self.trace[position:]
        events=copy.deepcopy(self.events);events[113]['order']=[3,2,1]
        return raw,events

    def test_exact_prefix_proof(self):
        raw,events=self.synthetic()
        proof=p.prefix_proof(self.trace,raw,self.events,events)
        self.assertEqual(proof['exact_event_count'],113)
        self.assertEqual(proof['accepted_prefix_battles_reexecuted_for_continuation'],24)
        self.assertGreater(proof['byte_prefix_size'],700000)

    def test_modified_earlier_byte_event_and_early_marker_rejected(self):
        raw,events=self.synthetic()
        with self.assertRaises(ValueError):p.prefix_proof(self.trace,b'X'+raw[1:],self.events,events)
        events[112]['frame']+=1
        with self.assertRaises(ValueError):p.prefix_proof(self.trace,raw,self.events,events)
        raw,events=self.synthetic()
        with self.assertRaises(ValueError):p.prefix_proof(self.trace,raw.replace(b'"streak": 24',b'"streak": 23'),self.events,events)

    def test_original_loss_never_promoted_to_30(self):
        old=probe.strict((ORIGINAL/(probe.CASE+'.stdout')).read_bytes())
        with self.assertRaises(ValueError):probe.require_target(old)
        self.assertEqual((old['wins'],old['losses'],old['bp_earned']),(24,1,72))


if __name__=='__main__':unittest.main()
