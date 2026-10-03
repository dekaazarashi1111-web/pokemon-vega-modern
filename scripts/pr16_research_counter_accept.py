#!/usr/bin/env python3
"""保存済み数値受付の独立受入。native/コンパイラを再起動せず入力原本の扱いを修復する。"""
import ast
import datetime
import io
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_counter_numeric as patch
import pr16_research_counter_probe as probe
import pr16_research_counter_oracle as oracle
import pr16_research_lifecycle_actions as d
TASK='USER-20260927-RESEARCH-COUNTER'
START='665623135eb7c01cefbd4345abee9f8a0b2c714d'
MEASURE_HEAD='9ec402333e9c5c0defba6073d6f20d551086c6cb'
RUN=36286898098
ARTIFACT=10920589167
SELF='scripts/pr16_research_counter_accept.py'
WF='.github/workflows/pr16-research-counter-accept.yml'
TEST='tests/test_pr16_research_counter_numeric.py'
DRIVER='scripts/pr16_research_counter_actions.py'
CP='content/modernization/pr16_research_counter_checkpoint.json'
GUIDE='docs/PR16_RESEARCH_COUNTER_JA.md'
RECIPE='content/modernization/pr16_research_counter_numeric_recipe.json'
BASE='content/modernization/pr16_research_counter_evidence'
ACCEPT='content/modernization/pr16_research_counter_acceptance'
OUT=ROOT/'.local/pr16-research-counter-accept';PUBLIC=OUT/'public'
CODE={SELF,WF,TEST,DRIVER,'.github/workflows/pr16-counter-source-context.yml',
      '.github/workflows/pr16-research-counter-numeric.yml',
      'scripts/pr16_research_counter_probe.py','scripts/pr16_research_counter_oracle.py'}
PREFIX='.local/pr16-research-counter/public/'
need,identity=oracle.need,oracle.identity


def archive(number,size,digest,count,total,run):
    meta=d.inputs.api('actions/artifacts/'+str(number))
    need(meta['id']==number and not meta['expired'] and meta['size_in_bytes']==size
         and meta['digest']=='sha256:'+digest and meta['workflow_run']['id']==run,'固定artifact API identity')
    raw=d.inputs.api('actions/artifacts/'+str(number)+'/zip',True)
    need(identity(raw)==dict(size=size,sha256=digest),'固定artifact ZIP identity')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.infolist())==len(set(z.namelist()))==count and sum(i.file_size for i in z.infolist())==total,'ZIP集合と総容量')
        rows={}
        for info in z.infolist():
            p=PurePosixPath(info.filename)
            need(not p.is_absolute() and '..' not in p.parts and '\\' not in info.filename
                 and not info.is_dir() and info.external_attr>>28!=10,'relative regular artifact file')
            rows[info.filename]=z.read(info)
    return rows,{k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run')}


def repair_context():
    """source/preimage/postimageを閉じて2ファイルだけ修復。旧実測ソースはcommitに保持。"""
    for name,spec in REPAIRS.items():
        raw=(ROOT/name).read_bytes()
        need(identity(raw)==spec['before'],'修復前source identity: '+name)
        text=raw.decode('utf-8')
        for before,after in spec['changes']:
            need(text.count(before)==1,'唯一の修復箇所: '+name);text=text.replace(before,after)
        new=text.encode('utf-8');need(identity(new)==spec['after'],'修復後source identity: '+name)
        compile(text,name,'exec');(ROOT/name).write_bytes(new)
    d.write(PUBLIC/'context-repair.json',{k:{'before':v['before'],'after':v['after']} for k,v in REPAIRS.items()})


def inherited_checks(old,original_test):
    """旧76件を一括成功にせず、無変更のEventTests 15件だけ再利用する。"""
    new=(ROOT/TEST).read_text(encoding='utf-8');prior=original_test.decode('utf-8')
    select=lambda text:text.split('class EventTests(unittest.TestCase):\n',1)[1].split('\n\nclass NativeEvidenceTests',1)[0]
    need(select(new)==select(prior),'15件のevent試験は完全不変')
    cls=next(n for n in ast.parse(prior).body if isinstance(n,ast.ClassDef) and n.name=='EventTests')
    names=[n.name for n in cls.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
    need(len(names)==15,'閉じた15件の試験集合')
    log=old['unit.stderr.txt'];unit=oracle.load(old['unit.json'])
    need(unit['returncode']==1 and unit['expected_tests']==76 and unit['passed_tests']==75
         and identity(log)==unit['stderr'] and identity(old['unit.stdout.txt'])==unit['stdout'],'旧失敗結果を保持')
    for name in names:
        line=f'{name} (tests.test_pr16_research_counter_numeric.EventTests.{name}) ... ok\n'.encode()
        need(log.count(line)==1,'旧event試験の成功原本: '+name)
    return dict(reused_tests=15,methods=sorted(names),class_source=identity(select(prior).encode()),
                original_unit=unit,old_negative_tests_accepted=0,old_positive_tests_accepted=0,
                reason_ja='旧positiveは誤ったpost-close入力で失敗。旧negative60件の見かけのPASSは証拠にせず修正後の陽性前提付き試験で置換する。')


def collect():
    os.chdir(ROOT);d.current();need(not (ROOT/CP).exists(),'受入済み数値表示を再実行しない')
    PUBLIC.mkdir(parents=True)
    run=d.inputs.api('actions/runs/'+str(RUN))
    need(run['status']=='completed' and run['conclusion']=='failure' and run['run_attempt']==1
         and run['head_sha']==MEASURE_HEAD and run['head_branch']=='codex/modernization-followup-20260908','旧runは終端failureのまま保持')
    job=d.inputs.api('actions/jobs/108529248151')
    steps={v['name']:v['conclusion'] for v in job['steps']}
    expected={'Source transfer identity':'success','New counter numeric boundaries only':'failure',
              'Preserve measurement and handoff':'success','Task graph and exact scoped final index':'failure',
              'Non-force evidence checkpoint':'skipped','Run actions/upload-artifact@v4':'success'}
    need(job['run_id']==RUN and job['head_sha']==MEASURE_HEAD and job['status']=='completed'
         and all(steps.get(k)==v for k,v in expected.items()),'失敗工程とcommit未実行の原本')
    rows,meta=archive(ARTIFACT,120577,'829b961d59446c3d0877e028af22fb55f8ed6fb4ff9c2e2f2199aeb9902fc7bf',57,2207935,RUN)
    need(meta['workflow_run']['head_sha']==MEASURE_HEAD,'実測artifact source')
    need(set(rows)=={k for k in rows if k.startswith(PREFIX)}|{CP},'閉じたartifact用途')
    old={k[len(PREFIX):]:v for k,v in rows.items() if k.startswith(PREFIX)}
    inv=oracle.load(old['invocation.json'])
    need(inv['source_head']==MEASURE_HEAD and inv['run_id']==RUN,'実測起点')
    protected=inv['protected_bindings'];need(d.bindings(set(protected))==protected,'歴史受入/BP/P08/baselineは不変')
    need(d.bindings(set(inv['source_bindings']))==inv['source_bindings'],'実測sourceがまだ不変')
    for name,binding in inv['source_bindings'].items():
        need(identity(d.git('show',MEASURE_HEAD+':'+name))==binding,'commitと実測sourceの一致')
    need(d.git('diff','--name-only',MEASURE_HEAD,'HEAD','--',*sorted(inv['source_bindings']))==b'','実測後のsource差分なし')
    original_test=(ROOT/TEST).read_bytes();repair_context();inherited=inherited_checks(old,original_test)
    data,seed_meta=archive(10898510128,17366330,'7d3de78d4e852583eb35551076021630c1343aa623e91fe1529d73f4cf1471ed',3,33685811,36218655601)
    seed=data['seed.srm'];need(identity(seed)==dict(size=131072,sha256='f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb'),'固定seedをROM生成せず再利用')
    results={};screens={};fixtures={}
    for index in (0,1):
        case=str(index);measured=oracle.load(old[case+'/measurement.json'])
        need(measured['returncode']==0 and measured['timeout'] is False and measured['stderr']==identity(b''),'元native clean終端')
        fixture,receipt=probe.fixture(seed,index);need(receipt==measured['fixture'],'完全な起動前fixture再構築')
        (OUT/(case+'.fixture.srm')).write_bytes(fixture);fixtures[case]=receipt
        for name in ('measurement.json','stdout.txt','stderr.txt','commands.txt'):
            p=PUBLIC/case/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(old[case+'/'+name])
        raw=old[case+'/stdout.txt'];commands=old[case+'/commands.txt']
        need(identity(raw)==measured['stdout'] and identity(commands)==measured['commands'] and old[case+'/stderr.txt']==b'','原本入出力のidentity')
        for name,binding in measured['screens'].items():
            b=old[case+'/'+name];need(identity(b)==binding and len(b)==115215 and b.startswith(b'P6\n240 160\n255\n'),'実測PPM identity')
            (PUBLIC/case/name).write_bytes(b)
            screens[case+'/'+name]=dict(artifact_id=ARTIFACT,member=PREFIX+case+'/'+name,identity=binding)
        results[case]=oracle.validate(raw,index,commands,fixture,measured['screens'])
    need(len(screens)==18,'実視認済み18画面')
    compiled=oracle.load(old['compile.json'])
    need(compiled['returncode']==0 and compiled['stderr']==compiled['stdout']==identity(b'')
         and old['compile.stderr.txt']==old['compile.stdout.txt']==b''
         and identity(old['generated.c.txt'])==compiled['source'],'厳格host compile原本')
    guards=oracle.load(old['guards.json']);methods={'bus8','bus16','bus32','raw8','raw16','raw32','register'}
    need(set(guards)==methods,'7種類のbarrier試験')
    for method in methods:
        err=old[method+'.stderr.txt'];out=old[method+'.stdout.txt']
        need(err==b'research-save-impact: host write after observation barrier\n' and out==b''
             and guards[method]==dict(returncode=1,stdout=identity(out),stderr=identity(err)),'host書込み拒否を再利用')
    measurement=oracle.load(old['measurement.json'])
    need(measurement['candidate']==patch.CANDIDATE and measurement['counts']==dict(native_processes=2,guard_processes=7,host_compiles=1,arm_compiles=0,accepted_case_reruns=0),'閉じた実行計数')
    recipe=oracle.load(old['recipe.json'])
    need(recipe['parent']==patch.PARENT and recipe['candidate']==patch.CANDIDATE and recipe['changed_bytes']==88
         and recipe['declared_bytes']==147 and recipe['outside_declared_changes']==0,'検証済み147byte recipe')
    os.environ['PR16_COUNTER_EVIDENCE']=str(PUBLIC)
    unit=subprocess.run([sys.executable,'-B','-m','unittest','tests.test_pr16_research_counter_numeric.NativeEvidenceTests','-v'],capture_output=True,timeout=90)
    (PUBLIC/'unit.stdout.txt').write_bytes(unit.stdout);(PUBLIC/'unit.stderr.txt').write_bytes(unit.stderr)
    check=dict(returncode=unit.returncode,expected_tests=63,passed_tests=unit.stderr.count(b' ... ok\n'),
               stdout=identity(unit.stdout),stderr=identity(unit.stderr),positive_tests=1,mutation_tests=62,
               each_mutation_requires_positive_baseline=True,footer_fixture_rejection_tests=2)
    d.write(PUBLIC/'unit.json',check)
    need(unit.returncode==0 and check['passed_tests']==63 and not unit.stdout and b'skipped' not in unit.stderr,'修正済み63件の全PASS')
    review=dict(status='PASS_COUNTER_NUMERIC_TEXT_VISUAL_SCOPED',reviewed_screen_count=18,screens=screens,
        method_ja='本会話で固定artifactの18 PPMを2倍の一覧画像として視認。OCR不使用。Actionsはmember/hashの一致を検証し、コード自身による視認とは主張しない。',
        finding_ja='RP 0 / ランク 1 と RP 9999 / ランク 7 を確認。2行の枠内に収まり、対象数値の欠け・文字化けなし。導入・活動案内・再訪案内・会話終了も確認。',
        whole_game_visual_quality_accepted=False,standard_list_accepted=False,natural_story_progress_accepted=False,naturally_earned_spending_accepted=False)
    d.write(PUBLIC/'visual-review.json',review);d.write(PUBLIC/'oracle.json',results);d.write(PUBLIC/'inherited-checks.json',inherited)
    diagnosis=dict(original_run=d.run_summary(run),original_steps=expected,original_artifact=meta,
        causes_ja=['終了後ファイル131088byteと不変の入力Flash131072byteを全ファイル比較して誤拒否。',
                   '旧試験loaderが終了後ファイルを入力として使用。旧negative60件は陽性前提がなく、見かけのPASSを受入しない。',
                   '旧unit tracebackのcheckout絶対pathを最終index guardが拒否。raw artifactを保持し、trackedコピーだけroot表記を正規化する。'],
        post_close_scope_ja='元の終了後ファイルはsize/hashのみ残りbytesは未保存。16byte追加部分の意味やprefix不変を後付けで主張しない。今回受入は原本に記録された全観測点の実コアFlash131072byte不変。修正後driverのprefix検査は将来用で、今回再実行なし。',
        new_native_processes=0,new_guard_processes=0,new_host_compiles=0,new_arm_compiles=0,new_rom_builds=0,
        accepted_case_reruns=0,failed_run_conclusion_rewritten=False)
    d.write(PUBLIC/'recovery.json',diagnosis)
    return dict(old=old,failed_checkpoint=rows[CP],source=inv,meta=meta,seed_meta=seed_meta,
                measurement=measurement,checks=check,inherited=inherited,fixtures=fixtures,review=review,results=results,protected=protected)


REPAIRS = {
 TEST: {
  'before': {'size':8053,'sha256':'e4d8f80e2eb50e55d0837002ae6ef764ea6a3318f525cf2925b54108105e8feb'},
  'after': {'size':8298,'sha256':'01ba5de0afdb9c035c62aecf11a269c0294c2f1e0f9995318232a497c4872b80'},
  'changes': [
   ["(self.directory.parent/(str(index)+'.srm')).read_bytes()", "(self.directory.parent/(str(index)+'.fixture.srm')).read_bytes()"],
   ["args=self.inputs(index);rows=[oracle.load(line) for line in args[0].splitlines()]", "args=self.inputs(index)\n        # 拒否試験ごとに有効な陽性原本から始め、別原因による見かけのPASSを防ぐ。\n        oracle.validate(*args)\n        rows=[oracle.load(line) for line in args[0].splitlines()]"],
   ["elif kind=='fixture': args[3]=args[3][:-1]+bytes([args[3][-1]^1])", "elif kind=='fixture': args[3]=args[3][:-1]+bytes([args[3][-1]^1])\n        elif kind=='footer_input': args[3]+=bytes(16)"],
   ["('truncate','commands','fixture','screens')", "('truncate','commands','fixture','footer_input','screens')"],
   ["('drop','duplicate','trailing','truncate','commands','fixture','screens','balance_text',", "('drop','duplicate','trailing','truncate','commands','fixture','footer_input','screens','balance_text',"]]},
 DRIVER: {
  'before': {'size':15609,'sha256':'a5595d164a635b8c98800c8cff203abd39df86effa80cb700e94aadd3a07fba2'},
  'after': {'size':16283,'sha256':'e25c6ebb924b953c5f12881366e6a7fb568a52b98dcd83db0a39b59059db0608'},
  'changes': [
   ["fixture,receipt=probe.fixture(seed,index);save=OUT/(str(index)+'.srm');save.write_bytes(fixture)", "fixture,receipt=probe.fixture(seed,index)\n        (OUT/(str(index)+'.fixture.srm')).write_bytes(fixture)\n        save=OUT/(str(index)+'.srm');save.write_bytes(fixture)"],
   ["patch.need(save.read_bytes()==fixture,'fixture Flash remained unchanged')", "saved=save.read_bytes()\n            patch.need(len(saved) in (len(fixture),len(fixture)+16) and saved[:len(fixture)]==fixture,\n                       'post-close Flash prefix unchanged; container tail is not input fixture')"],
   ['passed==count==76','passed==count==78'],
   ["'two numeric boundaries and all 76 new tests'","'two numeric boundaries and all 78 checks'"],
   ['専用probe/oracle/新76検査/Actions','専用probe/oracle/78検査/Actions'],
   ["raw=p.read_bytes();raw.decode('utf-8');patch.need(b'\\0' not in raw,'tracked UTF8 only')\n        target=directory/p.relative_to(PUBLIC);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)\n        evidence[str(target)]=patch.identity(raw)", "raw=p.read_bytes();raw.decode('utf-8');patch.need(b'\\0' not in raw,'tracked UTF8 only')\n        target=directory/p.relative_to(PUBLIC);target.parent.mkdir(parents=True,exist_ok=True)\n        safe=raw.replace((str(ROOT)+'/').encode(),b'<checkout>/')\n        if safe!=raw:\n            target=target.with_name(target.stem+'.normalized'+target.suffix)\n            notice=target.with_suffix(target.suffix+'.normalization.json')\n            d.write(notice,dict(raw=patch.identity(raw),normalized=patch.identity(safe),method='CHECKOUT_ROOT_ONLY',raw_in_actions_artifact=True))\n            evidence[str(notice)]=patch.identity(notice.read_bytes())\n        target.write_bytes(safe);evidence[str(target)]=patch.identity(safe)"]]}}


def record():
    data=collect();old=data['old'];owned=set()
    history=Path(BASE)/str(RUN);need(not history.exists() and not Path(ACCEPT).exists(),'原本記録の重複禁止')
    history.mkdir(parents=True)
    manifest={};normalizations={}
    def preserve(target,raw):
        raw.decode('utf-8');need(b'\0' not in raw,'UTF8 textのみを追跡')
        safe=raw.replace((str(ROOT)+'/').encode(),b'<checkout>/')
        if safe!=raw:
            original=str(target);target=target.with_name(target.stem+'.normalized'+target.suffix)
            normalizations[original]=dict(raw=identity(raw),normalized_path=str(target),normalized=identity(safe),method='CHECKOUT_ROOT_ONLY',raw_in_original_artifact=True)
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(safe)
        manifest[str(target)]=identity(safe);owned.add(str(target))
    for relative,raw in sorted(old.items()):
        if Path(relative).suffix in ('.json','.txt'): preserve(history/relative,raw)
    preserve(history/'checkpoint.failed.json',data['failed_checkpoint'])
    d.write(history/'normalizations.json',normalizations);owned.add(str(history/'normalizations.json'))
    manifest[str(history/'normalizations.json')]=identity((history/'normalizations.json').read_bytes())
    d.write(history/'manifest.json',manifest);owned.add(str(history/'manifest.json'))
    # 新たな検証原本と旧失敗原本を別directoryに分離する。
    manifest={}
    for p in sorted(PUBLIC.iterdir()):
        if p.is_file() and p.suffix in ('.json','.txt'): preserve(Path(ACCEPT)/p.name,p.read_bytes())
    d.write(Path(ACCEPT)/'manifest.json',manifest);owned.add(ACCEPT+'/manifest.json')
    (ROOT/RECIPE).write_bytes(old['recipe.json']);owned.add(RECIPE)
    d.current()
    runs=d.inputs.api('actions/runs?head_sha='+os.environ['GITHUB_SHA']+'&per_page=50')
    need(runs['total_count']==len(runs['workflow_runs']) and runs['total_count']<=50,'最新HEAD Actions一覧の完全性')
    checks=[d.run_summary(v) for v in runs['workflow_runs']]
    receipt=dict(schema_version=1,task=TASK,status='PASS_COUNTER_NUMERIC_TEXT_SCOPED',source_head=os.environ['GITHUB_SHA'],
        run_id=int(os.environ['GITHUB_RUN_ID']),measurement_source_head=MEASURE_HEAD,measurement_run=RUN,
        original_measurement_conclusion='failure',measurement_terminal_confirmed=True,
        original_artifact=data['meta'],original_evidence_manifest=str(history/'manifest.json'),
        source_bindings=d.bindings(CODE|set(data['source']['source_bindings'])),protected_bindings=data['protected'],
        parent=patch.PARENT,candidate=patch.CANDIDATE,recipe=RECIPE,fixture_source_artifact=data['seed_meta'],fixtures=data['fixtures'],
        accepted_cases=['rp0_rank1','rp9999_rank7'],oracle=ACCEPT+'/oracle.json',visual_review=ACCEPT+'/visual-review.json',
        evidence_manifest=ACCEPT+'/manifest.json',recovery=ACCEPT+'/recovery.json',context_repair=ACCEPT+'/context-repair.json',
        valid_reused_event_tests=15,corrected_evidence_tests=data['checks'],distinct_accepted_tests=78,
        reused_native_processes=2,reused_guard_processes=7,reused_host_compiles=1,
        new_native_processes=0,new_guard_processes=0,new_host_compiles=0,new_arm_compiles=0,new_rom_builds=0,accepted_case_reruns=0,
        counter_numeric_display_accepted=True,counter_rank_number_accepted=True,standard_list_accepted=False,
        natural_story_progress_accepted=False,naturally_earned_spending_accepted=False,
        post_close_file_bytes_accepted=False,whole_game_visual_quality_accepted=False,
        own_actions_completion_confirmed=False,observed_head_checks=checks,
        active_baseline_changed=False,release_ready=False,issue19_complete=False)
    d.write(CP,receipt);owned.add(CP)
    goal='受付の数値残高/rankは0RP・rank1と9999RP・rank7の2境界を限定受入済み。次はSTANDARD_LISTの選択・取消・再訪を後継candidate c3971e83へ実装し変更影響だけ検証、その後自然稼得RP→ショップ支出と通常ストーリー進行を接続する。数値2境界、物理4入口、旧稼得/BP/P08の成功部分を無変更再実行しない。'
    guide='''# PR16 受付の残高・rank数値表示

Task: `USER-20260927-RESEARCH-COUNTER`

## 完了した範囲

受付の固定文「ポイントを／かくにんします。」を、実際の残高とランクを表示する2行の会話へ接続した。
`RP 0 / ランク 1` と `RP 9999 / ランク 7` を物理キー操作と独立oracleで確認し、全18画面を視認した。
9999RPは起動前の表示境界fixtureであり、自然に稼いだRPとは主張しない。
標準listはまだ実装しておらず、現時点のUIは標準buffernumberとmsgboxによる数値会話である。

## 実装と後継ROMの境界

親は32MiB `26dac23cfdbc02c3c25e357b79dcdf3d247c10d893f54a4f6d6b1227bf5624da`。
後継は32MiB `c3971e83184613a27730eaec6490d203a2c1261c77894b711b0352f487808557`。
既存の15byte文言と132byteイベント窓だけを使用し、宣言147byte内の88byteを変更。外部差分0、完全rollback一致、新領域0、新ARM compile0。
残高getter→buffernumber slot0、rank getter→slot1を接続し、成功resultを0へ戻す。cap4、保存失敗13、その他の終了分岐は保持する。
canonical model/overlayは歴史的な親の正本として不変。数値層の正本は `scripts/pr16_research_counter_numeric.py` と `content/modernization/pr16_research_counter_numeric_recipe.json`。
次のcandidate生成では、親の受入済みrecipe列を再利用して26dac23cを復元した後、数値層を一度だけ適用する。旧モデルの固定文やP08/BP候補を後継の代用品にしない。

## 検証と失敗記録の扱い

元run36286898098 / source9ec402333e9c5c0defba6073d6f20d551086c6cbの結論はfailureのまま保持する。
同runのnative2process、厳格host compile1、host書込み拒否7方式は成功原本を再利用した。
終了後のファイル131088byteと入力Flash131072byteの全ファイル比較、および終了後ファイルを使う試験loaderが検証失敗の原因だった。
入力の不変コピーと終了後ファイルを分離し、各拒否試験の前に陽性原本が通ることを必須化した。末尾16byte付入力の拒否2件も追加。
旧negative60件の見かけのPASSは採用せず、修正後の63件をすべてPASS。無変更のevent VM試験15件だけ旧成功原本から再利用し、有効な試験は計78件。
VM試験をnative試験件数に含めない。観測barrier以降は物理keyのみ。実値、2数値buffer、展開全文、owner64byte、ledger2048byte、Bag、party、save counter、全観測点の実コアFlashが一致。
終了後ファイルのbytesは元artifactに存在せず、追加16byteの意味やdisk prefix一致を今回の証拠から推測しない。
修正後driverのprefix検査は将来用の修正であり、今回それを動かしたとは主張しない。
旧unit tracebackはcheckout絶対pathを含むためguardがcommitを止めた。旧artifactはそのまま保存し、trackedコピーだけroot表記を正規化してbefore/after hashを記録した。
今回の回復・受入でnative/guard/host compile/ARM/ROM生成を再実行した回数はすべて0。

## 画面確認

固定artifact10920589167の18 PPMを拡大して視認。2境界の数値が枠内に収まり、対象表示に欠け・文字化けなし。導入・活動案内・再訪案内と会話終了を確認した。
画像、member、hashの対応は `content/modernization/pr16_research_counter_acceptance/visual-review.json` に固定した。
全map、全活動、全ゲーム画面の無欠陥を主張するものではない。

## 次の作業・再実行禁止

'''+goal+'''

新しい標準listは「開く・選択・取消・再訪」を一つの受入単位にする。以後の自然RP支出は今回の人工9999RPとは別の根拠を必要とする。
数値の元workflowは固定source hashを持つ歴史的実測入口で、再実行しない。後継受付に変更影響がある場合だけ、新しいscope/source/inputを宣言して必要部分を検証する。
BP/Circus/P08、旧4入口の受入、旧稼得、固定再開入口、active baselineは不変。merge、draft解除、release、Issue19全完了は行わない。
checkpoint: `content/modernization/pr16_research_counter_checkpoint.json`。原本終端failureと独立受入を混同しない。受入用Actions自身の終端はGitHub側で照合する。
'''
    (ROOT/GUIDE).write_text(guide,encoding='utf-8');owned.add(GUIDE)
    state=d.read(d.STATE)
    state['research_counter']=dict(path=CP,status=receipt['status'],candidate=patch.CANDIDATE,recipe=RECIPE,
        source_head=receipt['source_head'],run_id=receipt['run_id'],measurement_run=RUN,
        counter_numeric_display_accepted=True,counter_rank_number_accepted=True,standard_list_accepted=False)
    state['bp']['current_stop']='受付の数値残高・rankを2境界/18画面で限定受入。旧runの検証失敗を原本から切り分け、63件の修正試験と不変15件で確定。次は標準list。'
    state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_COUNTER_STANDARD_LIST_AND_NATURAL_SPENDING_NEXT',goal_ja=goal,
        read_paths=[GUIDE,CP,RECIPE,ACCEPT+'/visual-review.json','scripts/pr16_research_counter_numeric.py',
                    'content/research_economy_v1/canonical_model.json','overlays/research_economy_v1/research_economy_v1.c'],
        stop_rule_ja='数値2境界/旧4入口/旧稼得を無変更再実行しない。標準list・自然RP支出・通常進行は未受入。原本/基準は不変、merge/release禁止。')
    state['do_not_repeat'].insert(0,'受付数値0RP/rank1・9999RP/rank7はcheckpointと18画面で限定受入。元run36286898098のfailureを保持し、回復でnative再実行0。旧negative60件は受入せず陽性前提付き63件へ置換。不変event15件/compile1/guard7/実測2processを再実行しない。')
    state['observed_head']=os.environ['GITHUB_SHA']
    state['observed_head_semantics']='数値受付の独立受入・検証入力修復のsource HEAD。元実測runは終端failureを保持し成功native原本だけ再利用。自己記録run終端と一般CIは別途GitHubで確認。'
    state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],runs=checks,
        reason_ja='受付数値の限定受入原本を保存。元run36286898098はfailureを改作せず回復済みとして記録。受入run自身の終端や一般CI全成功は事前に主張しない。')
    state['pending_runs']=[dict(run_id=r['id'],tested_head=r['head_sha'],status=r['status']) for r in runs['workflow_runs'] if r['status'] in ('queued','in_progress')]
    state['logs_synchronized']=True
    for p in CODE|set(data['source']['source_bindings'])|{CP,RECIPE,GUIDE}:
        state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    from pr16_learnset_compact_record import publish_resume
    publish_resume(state);owned|={d.STATE,d.DOC}
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 受付数値表示・独立受入と検証原本の修復\n- Version: research-counter-numeric-v1\n- Status: DONE（残高/rank数値表示の限定範囲。標準list/自然RP支出/通常進行は未完）\n- Summary: 既存147byte内88byteの数値会話を接続、2境界の実値・buffer・全文と18画面を確認。親26dac23c→c3971e83。人工9999RPを自然稼得と主張しない。\n- Files changed: 数値probe/oracle/専用試験/Actions、入力の不変コピーと陽性前提の修復、recipe、失敗原本と回復証拠/checkpoint/専用MD、固定引継ぎMD/JSON、両ログ。\n- Verify: 旧run36286898098はfailureを保持。成功native2/guard7/host1を再利用。修正63試験PASSと不変event15試験の原本を照合、計78件。新規native/guard/host/ARM/ROM生成0、既受入独立再実行0。task graph/resume/final index guard PASSを後段commitの必須条件とする。全体historical guard/一般CI全成功は主張しない。\n- Commit: source={os.environ["GITHUB_SHA"]} / acceptance run={os.environ["GITHUB_RUN_ID"]}; 同branch非force commit。自己SHAはgit logとremote refで照合。\n- Network: 固定GitHub artifactとrun/job/PR metadataのみ。原本absolute tracebackはartifactに保持、tracked正規化コピーは別hashで明示。ROM/save/binaryはGitに追加しない。merge/release/baseline変更なし。\n'
    for p in d.LOGS:
        with (ROOT/p).open('a',encoding='utf-8') as f:f.write(log)
    owned|=d.LOGS|set(REPAIRS)
    need(d.bindings(set(data['protected']))==data['protected'],'全protected bytes不変')
    d.write(OUT/'owned.json',sorted(owned))
    print('PASS_COUNTER_NUMERIC_TEXT_SCOPED: corrected=63 inherited=15 native_reexecuted=0')


def guard():
    os.chdir(ROOT);d.current()
    import pr16_resume
    import pr16_learnset_runtime_record as g
    pr16_resume.validate(ROOT)
    # この会話開始HEADからの全新規sourceも対象。最終record差分だけを検査しない。
    g.START=START;g.CODE=CODE;g.OWNED=set(d.read(OUT/'owned.json'));g.guard()
    cp=d.read(CP);need(d.bindings(set(cp['protected_bindings']))==cp['protected_bindings'],'最終protected bytes不変')
    need(d.bindings(set(cp['source_bindings']))==cp['source_bindings'],'最終source bytes不変')
    subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__=='__main__':
    if sys.argv[1:]==['record']:record()
    elif sys.argv[1:]==['guard']:guard()
    elif sys.argv[1:]==['paths']:print('\n'.join(d.read(OUT/'owned.json')))
    else:raise SystemExit('record|guard|paths')
