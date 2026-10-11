#!/usr/bin/env python3
"""One-time, exact pre/postimage-checked repair of the gear test controller.

Does not build or modify ROMs/saves. Stops if any of the three inputs changed.
The two failed patch-transport workflows applied nothing and ran no emulator.
"""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]
PATHS=['tools/mgba_pr16_purchased_gear.c','scripts/pr16_purchased_gear.py','tests/test_pr16_purchased_gear.py']
BEFORE=['2031e1fa6875584942c45b200eb92d56886b4a40eac7feb3cee9b797e019cc71','abd0ab22d526e388599c54ae6a8f2c45b011b8b4ab0f2c863aef8bce03b3c1b6','7d35ef5d36cde9a7e99e3e0821595a53feeb4ff10ecf6d12a66dc0c7b4bed3e6']
AFTER=['ba8a7994d25bf7d5d95fdf9fb35bace671f4b1625f5cee96df235a92bbdac9aa','f69d2b957e1213d08ec5a81551d4f7a50c434edc794ea686a910f0af5190f09b','c3a391e8f83300719e6ab24b3c0f16dd449ddb9c1af625c8f484b6112cd2fb04']
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def main():
    original=[]
    for name,sha in zip(PATHS,BEFORE):
        p=ROOT/name
        if any(q.is_symlink() for q in (p,*p.parents)):raise ValueError('symlink')
        text=p.read_text()
        if digest(text)!=sha:raise ValueError('preimage differs: '+name)
        original.append(text)
    s=original[0].replace('base_ability,toggles;','base_ability,toggles,mid_reload;')
    s=s.replace('{"eelektross-active",411,1012,1634,313,26,1},','{"eelektross-active",411,1012,1634,313,26,1,0},').replace('{"eelektross-no-toggle",411,1012,1634,313,26,0},','{"eelektross-no-toggle",411,1012,1634,313,26,0,0},').replace('{"eelektross-cancel-toggle",411,1012,1634,313,26,2}','{"eelektross-cancel-toggle",411,1012,1634,313,26,2,0},\n {"eelektross-cold-policy-reset",411,1012,1634,313,26,1,1}')
    start=' a_restore(c,&original);c=b_restart(c,argv[1],argv[2]);c->reset(c);original=*c;a_guard(c);a_require(b_continue(c),"gear equipped cold Continue failed");kt.reloaded=b_frames;'
    end='g_shot("equipped-reloaded");'
    a=s.index(start);b=s.index(end,a)+len(end)
    s=s[:a]+''' /* A configured NEXT-battle policy lives in volatile RAM, not the save.
  * Same-session cases keep it without any post-barrier write. A separate
  * cold-load control must deny Mega rather than silently reconfigure it. */
 if(v->mid_reload){
'''+s[a:b]+'''\n }
'''+s[b:]
    s=s.replace('v->toggles==1U?(kt.mega','(v->toggles==1U && !v->mid_reload)?(kt.mega')
    s=s.replace('printf("{\\"schema_version\\":1','printf("{\\"schema_version\\":2')
    s=s.replace('\\"fresh_cores\\":3,','\\"fresh_cores\\":%u,\\"cold_reload_before_encounter\\":%s,')
    s=s.replace('b_frames);\n#define KW','2U+v->mid_reload,v->mid_reload?"true":"false",b_frames);\n#define KW')
    changed=[s]
    s=original[1].replace("'eelektross-cancel-toggle':2}","'eelektross-cancel-toggle':2,'eelektross-cold-policy-reset':1}")
    s=s.replace('active=CASES[name]==1',"active=name=='eelektross-active';cold=name=='eelektross-cold-policy-reset'")
    s=s.replace("return dict(schema_version=1,status='PASS',scope=SCOPE","return dict(schema_version=2,status='PASS',scope=SCOPE")
    s=s.replace('fresh_cores=3,host_write_barriers=7','fresh_cores=3 if cold else 2,cold_reload_before_encounter=cold,host_write_barriers=7')
    s=s.replace("need(trace['interaction']>0 and all(trace[a]<trace[b] for a,b in zip(TRACE,TRACE[1:]))","sequence=TRACE if value['cold_reload_before_encounter'] else tuple(k for k in TRACE if k!='reloaded')\n    if not value['cold_reload_before_encounter']:need(trace['reloaded']==0,'same-session case fabricated an intermediate cold Continue')\n    need(trace['interaction']>0 and all(trace[a]<trace[b] for a,b in zip(sequence,sequence[1:]))")
    s=s.replace('if CASES[name]==1:need(',"if name=='eelektross-active':need(")
    s=s.replace("report=dict(schema_version=1,status='FAIL'","report=dict(schema_version=2,status='FAIL'")
    s=s.replace("'config/active_play_baseline.json','design/active_play_baseline.md',","'config/active_play_baseline.json','design/active_play_baseline.md','overlays/cfru/integration.c','overlays/cfru/integration.h','tools/modernization_p04_mega_runtime.py','config/modernization_p04_mega_runtime.json',")
    changed.append(s)
    s=original[2].replace('witness.update(toggle=92,mega=95)','witness.update(toggle=92,mega=95,reloaded=0)')
    s=s.replace("row['witness']['mega']=95 if toggles==1 else 0","row['witness']['mega']=95 if name=='eelektross-active' else 0;row['witness']['reloaded']=60 if name=='eelektross-cold-policy-reset' else 0")
    s=s.replace("{'fresh_cores':2}","{'fresh_cores':3}").replace('for key in p.TRACE:\n',"for key in (k for k in p.TRACE if k!='reloaded'):\n")
    anchor='    def test_reject_injected_or_missing_physical_give(self):'
    s=s.replace(anchor,'''    def test_reject_false_intermediate_continue_and_policy_persistence(self):
        row=copy.deepcopy(self.row);row['witness']['reloaded']=60
        with self.assertRaises(ValueError):self.validate(row)
        name='eelektross-cold-policy-reset';row=copy.deepcopy(self.row);row.update(p.expected(name));row['witness'].update(reloaded=60,mega=0)
        self.assertEqual(self.validate(row,name=name),row)
        for delta in ({'mega_species':1634},{'ability':313},{'fresh_cores':2},{'cold_reload_before_encounter':False}):
            with self.subTest(delta=delta),self.assertRaises(ValueError):self.validate(row|delta,name=name)
        row['witness']['mega']=95
        with self.assertRaises(ValueError):self.validate(row,name=name)
'''+anchor)
    changed.append(s)
    for name,text,sha in zip(PATHS,changed,AFTER):
        if digest(text)!=sha:raise ValueError('tested postimage differs: '+name)
    for name,text in zip(PATHS,changed):(ROOT/name).write_text(text)
    print('Three exact tested postimages applied; native acceptance still pending.')
if __name__=='__main__':main()
