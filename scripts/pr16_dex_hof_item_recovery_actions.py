#!/usr/bin/env python3
"""消失出力の最小再計測。旧165試験を継承し、新実測原本のhashを公開前に記録。"""
import contextlib,io,json,os,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests')]
import pr16_dex_hof_jp_item_actions as original
import pr16_dex_hof_jp_item_chain as chain
import pr16_dex_hof_jp_item_text as consumer
import pr16_dex_hof_item_recovery_validation as validation
import pr16_dex_publication as publication
need,identity=consumer.need,consumer.identity
SELF='scripts/pr16_dex_hof_item_recovery_actions.py'
WF='.github/workflows/pr16-dex-hof-item-recovery.yml'
GUIDE='docs/PR16_DEX_HOF_ITEM_RECOVERY_JA.md'
FIXTURE='content/modernization/pr16_dex_hof_item_recovery_development_proof.json'
OUT=ROOT/'.local/jp-item-recovery';PUBLIC=ROOT/'public-jp-item-recovery';ARTIFACT='pr16-jp-item-recovery-text-only'
NEW_CODE={SELF,WF,GUIDE,FIXTURE,'scripts/pr16_dex_hof_item_recovery_validation.py','tests/test_pr16_dex_hof_item_recovery_validation.py'}
CODE=original.CODE|NEW_CODE
ORIGINAL_HEAD='ea976a497522bbf966d1e0e6ef9f2875d1950d37';ORIGINAL_RUN=37701354400;ORIGINAL_JOB=113065287651
INHERITED=OUT/'inherited.json'
TEST_COUNT=24 # 新出力回復suiteだけ。旧165試験は継承。
FILES={'measurement.json','reference-chain.json','tests.json','provenance.json'}


def bindings():return original.bindings(CODE)


def guard():
 import pr16_resume
 import pr16_story_live_probe as live
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','同branch初回の限定回復だけ')
 pr=live.api('pulls/16');need(pr['state']=='open'and pr['draft']and not pr['merged']and pr['head']['sha']==os.environ['GITHUB_SHA'],'現HEAD draft/open')
 pr16_resume.validate(ROOT);publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF)
 history=live.api('actions/workflows/'+Path(WF).name+'/runs?branch=codex%2Fmodernization-followup-20260908&per_page=100')
 need(history['total_count']==1 and len(history['workflow_runs'])==1 and history['workflow_runs'][0]['id']==int(os.environ['GITHUB_RUN_ID']),'同branch回復workflowは初回runだけ。別runの再構成を累積2へ隠さない')
 need(not OUT.exists()and not PUBLIC.exists(),'回復scope初回だけ');OUT.mkdir(parents=True)
 run=live.api('actions/runs/'+str(ORIGINAL_RUN));job=live.api('actions/jobs/'+str(ORIGINAL_JOB));art=live.api('actions/runs/'+str(ORIGINAL_RUN)+'/artifacts')
 need(run['head_sha']==ORIGINAL_HEAD and run['run_attempt']==1 and run['status']=='completed'and run['conclusion']=='failure','元run全体failureを保持')
 need(job['run_id']==ORIGINAL_RUN and job['status']=='completed'and job['conclusion']=='failure'and job['name']=='item-text','元job失敗終端')
 steps=job['steps'];need([s['number']for s in steps]==[1,2,3,4,5,6,7,8,16,17],'元全stepの順序')
 need([s['conclusion']for s in steps]==['success']*5+['failure','skipped','skipped','success','success'],'元測定成功と公開失敗を分離')
 need(steps[4]['name']=='New exchange and mailbox roots with complete text only'and steps[5]['name']=='Closed successful text publication guard','正しい元step')
 need(art['total_count']==0 and art['artifacts']==[],'元runner原本artifactなし')
 comparison=live.api('compare/'+ORIGINAL_HEAD+'...'+os.environ['GITHUB_SHA'])
 allowed=NEW_CODE|{'content/modernization/pr16_native_supply_resume_20260913.json','docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md','design/run_log.md','design/version_log.md'}
 need(comparison['status']=='ahead'and comparison['behind_by']==0 and comparison['ahead_by']==1 and {f['filename']for f in comparison['files']}==allowed,'元165試験の全source/依存不変、新回復と記録だけ')
 need(len(original.CODE)==14 and not set(original.CODE)&allowed,'凍結した元14sourceへ変更なし')
 log=live.api('actions/jobs/'+str(ORIGINAL_JOB)+'/logs',True);need(type(log)is bytes and 0<len(log)<10000000,'元jobログの有限取得')
 decoded=log.decode('utf8');need(decoded.count('{"status": "PASS_CURRENT_ROOTED_ITEM_EXCHANGE_MAIL_MINIMUM_TYPE", "tests": 165, "classified": 781, "unclassified": 93, "new_native": 0}')==1 and decoded.count('ValueError: 非空LF UTF8境界')==1,'元成功集計行と公開失敗行だけを継承')
 inherited=dict(source_head=ORIGINAL_HEAD,run_id=ORIGINAL_RUN,job_id=ORIGINAL_JOB,tests=165,original_run_conclusion='failure',measurement_step='success',publication_step='failure',original_artifact_missing=True,original_output_hashes_available=False,job_log_identity=identity(log),source_files_unchanged=14,scope_test_reruns=0)
 INHERITED.write_text(json.dumps(inherited,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(dict(status='PASS_INHERITED_SCOPE_TESTS_ONLY',**inherited),ensure_ascii=False))


def expected():
 inherited=json.loads(INHERITED.read_bytes())
 return dict(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),expected_bindings=bindings(),recovery_test_count=TEST_COUNT,inherited_log_identity=inherited['job_log_identity'])


def run():
 import pr16_dex_hof_capacity_actions as reconstruct
 import pr16_dex_hof_donor as donor
 need(INHERITED.is_file()and not PUBLIC.exists(),'元scope継承を先に検証')
 try:
  original.source_preflight(OUT/'sources',download=True)
  import test_pr16_dex_hof_item_recovery_validation as tests
  stream=io.StringIO();suite=unittest.defaultTestLoader.loadTestsFromModule(tests)
  result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);(OUT/'tests.txt').write_text(stream.getvalue())
  need(result.wasSuccessful()and not result.skipped and result.testsRun==TEST_COUNT,'新出力回復試験だけ成功')
  # 元165試験/Flash/旧consumer/旧heap/nativeはここでは起動しない。
  reconstruct.OUT=OUT/'current';reconstruct.OUT.mkdir()
  with(OUT/'reconstruct.log').open('w')as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):raw,latest=reconstruct.reconstruct()
  need(identity(raw)==latest['candidate']==consumer.CANDIDATE and len(donor.bind_owners(raw,latest))==115,'現0641全SHA/115owner再束縛')
  parent=chain.parent(*[(ROOT/p).read_bytes()for p in chain.PARENT_INPUTS])
  for h in parent['hits']:donor.signed(raw,h)
  regions,proof=consumer.regions(raw,parent);delta=chain.canonical(chain.build(parent,regions,proof))
  args=expected();log_identity=args.pop('inherited_log_identity')
  report=validation.measured_report(proof,delta,**args)
  validation.validate_report(report,delta,parent,**args)
  PUBLIC.mkdir();(PUBLIC/'reference-chain.json').write_bytes(delta)
  (PUBLIC/'measurement.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
  (PUBLIC/'tests.json').write_text(json.dumps(validation.test_summary(TEST_COUNT),ensure_ascii=False,indent=2)+'\n')
  (PUBLIC/'provenance.json').write_text(json.dumps(validation.provenance(report,inherited_log_identity=log_identity),ensure_ascii=False,indent=2)+'\n')
  validation.validate_output(PUBLIC,parent,**args,inherited_log_identity=log_identity,log=sys.stdout)
  print(json.dumps(dict(status='PASS_CURRENT_JP_ITEM_TEXT_RECOVERY',new_tests=TEST_COUNT,inherited_tests=165,inherited_test_reruns=0,current_rom_reconstructions=1,cumulative_scope_rom_reconstructions=2,classified=781,unclassified=93,new_native=0)))
 except Exception as exc:
  import traceback
  (OUT/'private-failure.txt').write_text(traceback.format_exc())
  frames=[dict(source=Path(t.filename).name,function=t.name,line=t.lineno)for t in traceback.extract_tb(exc.__traceback__)if Path(t.filename).parent==ROOT/'scripts']
  print(json.dumps(dict(error_code='ITEM_RECOVERY_FAILED_PRIVATE_DETAILS_RETAINED',type=type(exc).__name__,source_frames=frames)))
  raise RuntimeError('ITEM_RECOVERY_FAILED_PRIVATE_DETAILS_RETAINED')from None


def export():
 need(os.environ.get('ITEM_RECOVERY_OUTCOME')=='success','今回実測成功だけを公開')
 need(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==os.environ['GITHUB_SHA'],'公開前HEAD不変')
 need(subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=ROOT).returncode==0 and subprocess.run(['git','diff','--cached','--quiet','--'],cwd=ROOT).returncode==0,'公開前tracked/index無変更')
 parent=chain.parent(*[(ROOT/p).read_bytes()for p in chain.PARENT_INPUTS])
 validation.validate_output(PUBLIC,parent,**expected(),log=sys.stdout)

if __name__=='__main__':
 need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'閉じた3操作');globals()[sys.argv[1]]()
