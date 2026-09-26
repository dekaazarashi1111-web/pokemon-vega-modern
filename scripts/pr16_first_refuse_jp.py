#!/usr/bin/env python3
"""初回失敗を保全し、BPRJ linkerの実RAM番地だけ直した未受入1case。"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_learnset_first_refuse as f
x=f.x
SELF='scripts/pr16_first_refuse_jp.py'
TEST='tests/test_pr16_first_refuse_jp.py'
PRIOR=36071387743
f.CODE.update((SELF,TEST))
original_publish=f.publish


def reuse(raw,read,source):
    """Only unchanged unit inputs/results may be reused; native C has declared impact."""
    f.need(raw['new_unit_tests']==21 and raw['status']=='PARTIAL_BATTLE_EXP_FIRST_REFUSAL','exact failed attempt / successful unit scope')
    for leaf in ('unit.stdout.txt','unit.stderr.txt','unit.process.json'):
        f.need(f.identity(read(leaf))==raw['proof_bindings'][leaf],'saved successful unit original')
    import json
    f.need(json.loads(read('unit.process.json'))=={'returncode':0,'timed_out':False} and b'Ran 21 tests' in read('unit.stderr.txt') and b'\nOK\n' in read('unit.stderr.txt'),'successful 21-unit receipt')
    for path in (f.SELF,f.TEST):f.need(f.identity(source(path))==raw['source_bindings'][path],'unchanged Python validator / unit oracle')
    return {'source_run':PRIOR,'saved_unit_tests':21,'unchanged_unit_tests_reused':20,'changed_native_structure_rechecked':1,'new_japanese_binding_tests':4,'accepted_native_reruns':0,
            'reason_ja':'初回はコメント内の英語版0x02023D74で質問を検出できずsummary到達を正しく拒否。BPRJ.ldの実symbol gBattlescriptCurrInstr=0x02023CD4へ訂正。旧4caseとROMは変更なし。',
            'upstream':{'repository':'kapibarasan000/CFRU-JP','commit':'e24a16fe39e27ae162faf5b78596d1f3df18489d','path':'BPRJ.ld','blob_sha':'cf5363abd8439d63c7bd12cbe83ade861b0ebb51','gBattlescriptCurrInstr':0x02023CD4,'gMoveToLearn':0x02023F82}}


def scoped_run(command,name,*args,**kwargs):
    if name=='unit':
        folder=f.ROOT/f.EVIDENCE/str(PRIOR)
        audit=reuse(f.load(folder/'verification.json'),lambda leaf:(folder/leaf).read_bytes(),lambda path:(f.ROOT/path).read_bytes())
        f.write(f.PROOF/'unit-reuse.json',audit)
        command=[sys.executable,'-B','-m','unittest','tests.test_pr16_first_refuse_jp','tests.test_pr16_learnset_first_refuse.FirstRefusalTests.test_native_never_dispatches_or_writes_during_observation','-v']
    return f.BASE_RUN(command,name,*args,**kwargs)


def publish(value):
    from pr16_learnset_compact_record import publish_resume
    original_publish(value)
    path=f.ROOT/f.GUIDE
    note='\n## 日本語版symbol訂正と履歴\n\n初回run36071387743はsummaryへの到達を検出してFAIL（未受入、履歴保全）。コメントの英語版RAM0x02023D74ではなく、固定CFRU-JP BPRJ.ldのgBattlescriptCurrInstr=0x02023CD4を使用する。ROM/opcode/状態は変更しない。成功unit21の原本をhash照合し、変更なし20を再利用。今回unit5は新binding4と変更C構造1。合計25種のunit契約。旧4成功のnative再実行0。実行/記録入口は scripts/pr16_first_refuse_jp.py。\n'
    with path.open('a') as out:out.write(note)
    state=f.load(f.ROOT/x.m.STATE);state['source_bindings'][f.GUIDE]=f.identity(path.read_bytes())
    state['next_action']['read_paths']=[f.GUIDE,f.CP,f.SELF,SELF,TEST]
    publish_resume(state)
    for name in ('design/run_log.md','design/version_log.md'):
        with (f.ROOT/name).open('a') as out:out.write('- JP binding repair: run36071387743失敗原本を保全。BPRJ.ld実symbol0x02023CD4へ修正。成功unit20再利用、変更C構造1+新4を実行。旧native再実行0。参照 https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/BPRJ.ld 。\n')


if __name__=='__main__':
    f.publish=publish;f.configure();x.m.run=scoped_run
    actions={'execute':f.execute,'record':x.record,'complete':f.complete,'guard':x.guard,'paths':lambda:print('\n'.join(sorted(x.owned())))}
    f.need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|complete|guard|paths');actions[sys.argv[1]]()
