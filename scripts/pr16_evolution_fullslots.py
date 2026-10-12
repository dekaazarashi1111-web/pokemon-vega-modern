#!/usr/bin/env python3
"""Two new evolution full-slot routes on the already repaired exact candidate.

Parent learning/controller/save validators are hash-pinned and retained. Only
cases, scope, and read-only identification of evolution's own Yes/No state are
extended. No direct learner call, RAM/task write or substituted old result.
"""
from pathlib import Path
import hashlib
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_repaired_acceptance as repaired
need = repaired.need
SELF = 'scripts/pr16_evolution_fullslots.py'
PARENT_C = 'tools/mgba_pr16_level_learning.c'
PARENT_C_SHA = '949c9b538b2638d4f4da10743ebd13df9b748be6478c3dbd6a40ae64170c3740'
ADAPTER_SHA = 'e83d17663ffaacfca99fe77df7cd28031671dcd20a83abad1a634a31ed603ba5'
SOURCE = '.local/pr16-evolution-fullslots-source.c'
OUT = ROOT / '.local/pr16-evolution-fullslots'
SCOPE = 'PR16_EVOLUTION_FULLSLOTS_CANCEL_SAVE'
CASES = (('lucario-evolution-full', 12, 10, 13, 366, 20, 1, 0),
         ('lucario-evolution-cancel', 12, 10, 13, 366, 20, 1, 3))
# Native diagnostic original run 34510750395, artifact 10165799408. The fixed
# candidate retains these native instructions: task 080cf9f8, outer state 22,
# nested state 4 (Yes/No). Yes/no targets are 5/10 for learning, 11/0 for stop.
# These are observations only: no call_preserving, setters or host writes.
OBSERVER = '''
static bool l_evolution_prompt(struct mCore*c,bool stop){
    unsigned matches=0;
    for(unsigned i=0;i<16;i++){
        unsigned task=QOL_TASKS+i*QOL_TASK_SIZE;
        if(read8(c,task+4) && read32(c,task)==0x080CF9F9U &&
           read16(c,task+8)==22 && read16(c,task+20)==4 &&
           read16(c,task+22)==(stop?11:5) &&
           read16(c,task+24)==(stop?0:10))matches++;
    }
    a_require(matches<=1,"ambiguous evolution Yes/No task");
    return matches==1;
}
'''


def replace_once(text, old, new):
    need(text.count(old) == 1 and new not in text, 'evolution projection preimage differs')
    return text.replace(old, new, 1)


def controller_source():
    text = repaired.layer.source.checked(ROOT / PARENT_C, PARENT_C_SHA).decode()
    old_cases = '''    {"taillow-level-empty",10,12,10,457,20,2,1},
    {"taillow-level-full",10,12,10,457,20,1,0},
    {"taillow-level-cancel",10,12,10,457,20,1,3},
    {"lucario-evolution-empty",12,10,13,366,20,2,1},'''
    new_cases = '\n'.join('    {"' + r[0] + '",' + ','.join(map(str, r[1:])) + '},' for r in CASES)
    text = replace_once(text, old_cases, new_cases)
    text = replace_once(text, '#define L_SCOPE "PR16_NATIVE_LEVEL_AND_EVOLUTION_LEARNING_SAVE"',
                        '#define L_SCOPE "' + SCOPE + '"')
    text = replace_once(text, 'static struct LTrace l_scene', OBSERVER + '\nstatic struct LTrace l_scene')
    text = replace_once(text, 'cb==P02S_CB2_PARTY && p03f_task(c,P03F_LEARN_ASK)',
                        '(cb==P02S_CB2_PARTY && p03f_task(c,P03F_LEARN_ASK)) || (cb==P02S_CB2_EVOLUTION_UPDATE && l_evolution_prompt(c,false))')
    text = replace_once(text, 'cb==P02S_CB2_PARTY && p03f_task(c,P03F_STOP_ASK)',
                        '(cb==P02S_CB2_PARTY && p03f_task(c,P03F_STOP_ASK)) || (cb==P02S_CB2_EVOLUTION_UPDATE && l_evolution_prompt(c,true))')
    return text


def module():
    repaired.layer.source.checked(ROOT / 'scripts/pr16_repaired_acceptance.py', ADAPTER_SHA)
    m = repaired.load('pr16_native_learning')
    m.native = repaired.native_module()
    m.CASES, m.SOURCE, m.SELF, m.SCOPE = CASES, SOURCE, SELF, SCOPE
    previous = m.validate
    def validate(raw, case, process, stderr=b''):
        value = previous(raw, case, process, stderr)
        w = value['witness']
        need(w['evo_update'] < w['dialog'], 'replacement prompt is not after evolution')
        return value
    m.validate = validate
    return m


def run():
    text = controller_source()
    (ROOT / SOURCE).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / SOURCE).write_text(text)
    before = hashlib.sha256(text.encode()).hexdigest()
    try:
        return module().run(OUT)
    finally:
        need(hashlib.sha256((ROOT / SOURCE).read_bytes()).hexdigest() == before,
             'generated controller changed during execution')
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / 'executed-controller.c').write_text(text)
        (OUT / 'extension-binding.json').write_bytes(repaired.stable({
            'scope': SCOPE, 'candidate_sha256': repaired.ROM_SHA,
            'parent_controller_sha256': PARENT_C_SHA,
            'generated_controller_sha256': before,
            'extension': repaired.identity((ROOT / SELF).read_bytes()),
            'cases': CASES, 'observer_task': '0x080CF9F9',
            'observer_fields': {'outer_state': 22, 'yes_no_state': 4,
                                'learn_targets': [5, 10], 'stop_targets': [11, 0]},
            'diagnostic_original_run': 34510750395,
            'old_runs_relabelled': 0, 'release_ready': False}))


if __name__ == '__main__':
    try:
        print(json.dumps(run(), ensure_ascii=False))
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
