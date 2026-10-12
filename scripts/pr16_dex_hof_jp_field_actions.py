#!/usr/bin/env python3
"""新Flash縦切りのみ。旧受入再走なし、公開は閉じた成功textのみ。"""
import contextlib,hashlib,io,json,os,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests')]
import pr16_dex_hof_jp_field_text as field
import pr16_dex_hof_jp_field_producer as producer
import pr16_dex_publication as publication
need,identity=field.need,field.identity
SELF='scripts/pr16_dex_hof_jp_field_actions.py'
WF='.github/workflows/pr16-dex-hof-jp-field-text.yml'
GUIDE='docs/PR16_DEX_HOF_JP_FIELD_TEXT_JA.md'
DEV='content/modernization/pr16_dex_hof_jp_field_development.json'
MANIFEST='content/modernization/pr16_dex_hof_jp_field_sources.json'
OUT=ROOT/'.local/jp-field-text';PUBLIC=ROOT/'public-jp-field-text';ARTIFACT='pr16-jp-field-text-only'
CODE={SELF,WF,GUIDE,DEV,MANIFEST,
 'scripts/pr16_dex_hof_jp_field_producer.py','scripts/pr16_dex_hof_jp_field_text.py','scripts/pr16_dex_hof_jp_field_chain.py',
 'tests/test_pr16_dex_hof_jp_field_producer.py','tests/test_pr16_dex_hof_jp_field_text.py','tests/test_pr16_dex_hof_jp_field_chain.py','tests/test_pr16_dex_hof_jp_field_actions.py'}
FILES={'measurement.json','reference-chain.json','tests.json'}


def bindings(paths):return {p:identity((ROOT/p).read_bytes())for p in sorted(paths)}

def source_preflight(directory,download=False):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
 manifest=field.source_manifest()
 need(field.exact(json.loads((ROOT/MANIFEST).read_bytes()),manifest),'独立source manifest完全一致')
 sources={}
 for name,row in manifest.items():
  path=directory/name
  need(not any(p.is_symlink()for p in(path,*path.parents)),'source symlink拒否')
  if not path.exists() and download:
   if row['repository']=='dekaazarashi1111-web/pokemon-vega-modern':
    # 既存原本は変更されていない場合だけ再利用。ここでdownload/Git再実行をしない。
    raw=(ROOT/row['source']).read_bytes()
   else:
    import urllib.request
    with urllib.request.urlopen('https://raw.githubusercontent.com/'+row['repository']+'/'+row['commit']+'/'+row['source'],timeout=90)as response:
     raw=response.read(row['size']+1)
   need(identity(raw)=={k:row[k]for k in('size','sha256')},'取得前固定source identity')
   path.write_bytes(raw)
  need(path.is_file()and not path.is_symlink(),'固定source regular file');sources[name]=path.read_bytes()
 field.sources_bind(sources)
 return sources


def guard():
 import pr16_resume
 import pr16_story_live_probe as live
 need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern' and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908' and os.environ['GITHUB_RUN_ATTEMPT']=='1','許可済み同branch初回だけ')
 pr=live.api('pulls/16')
 need(pr['state']=='open'and pr['draft'] and not pr['merged'] and pr['head']['sha']==os.environ['GITHUB_SHA'],'現HEAD draft/open')
 pr16_resume.validate(ROOT)
 publication.contract(ROOT,WF,PUBLIC,ARTIFACT,SELF)
 need(not OUT.exists()and not PUBLIC.exists(),'新scope初回だけ')
 # 汎用Stage79 pendingはこの独立新scopeの前提ではない。成功へ書換えない。


def measured_report(proof,delta,tests):
 return dict(status='PASS_CURRENT_ROOTED_FLASH_BADGE_MINIMUM_TYPE',candidate=field.CANDIDATE,
  source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),unit_tests=tests,
  current_rom_reconstructions=1,current_owner_count=115,classified=780,unclassified=94,newly_classified=1,
  inherited_classified=779,inherited_unclassified=95,all_prior_accepted_retained=True,
  old_full_rom_scan_runs=0,old_native_cases_replayed=0,native_processes=0,donor_safe_bytes=0,
  formal_rom_changed=False,formal_save_changed=False,donor_eligible=False,donor_leased=False,
  scope_proof=proof,delta_identity=identity(delta),development_identity=identity((ROOT/DEV).read_bytes()),
  source_bindings=bindings(CODE),public_source_bindings=field.source_manifest())


def validate_report(report,delta_raw,parent):
 import pr16_dex_hof_jp_field_chain as chain
 need(type(report)is dict and set(report)==set(measured_report({},b'',1)),'閉じた成功report schema')
 expected=json.loads((ROOT/DEV).read_bytes())
 need(expected['status']=='PASS_NEW_SYNTHETIC_FIELD_DEVELOPMENT' and expected['candidate']==field.CANDIDATE,'独立synthetic開発原本')
 need(identity(chain.canonical(report['scope_proof']))==expected['scope_proof_identity'],'公開proof全体は独立fixtureで検証した閉scopeだけ')
 exact_fields=dict(status='PASS_CURRENT_ROOTED_FLASH_BADGE_MINIMUM_TYPE',candidate=field.CANDIDATE,
  source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),unit_tests=expected['unit_tests'],
  current_rom_reconstructions=1,current_owner_count=115,classified=780,unclassified=94,newly_classified=1,
  inherited_classified=779,inherited_unclassified=95,all_prior_accepted_retained=True,
  old_full_rom_scan_runs=0,old_native_cases_replayed=0,native_processes=0,donor_safe_bytes=0,
  formal_rom_changed=False,formal_save_changed=False,donor_eligible=False,donor_leased=False,
  delta_identity=identity(delta_raw),development_identity=identity((ROOT/DEV).read_bytes()),
  source_bindings=bindings(CODE),public_source_bindings=field.source_manifest())
 need(all(field.exact(report[k],value)for k,value in exact_fields.items()),'型厳密な閉counter/false/source identity')
 delta=json.loads(delta_raw);chain.validate(parent,delta)
 need(delta['classified']==780 and delta['unclassified']==94 and delta['newly_classified']==1,'1件だけの正式delta')
 need(field.exact(delta['proof'],report['scope_proof']),'証拠容器の同一scope')
 return True


def run():
 import pr16_dex_hof_jp_field_chain as chain
 import pr16_dex_hof_capacity_actions as reconstruct
 import pr16_dex_hof_donor as donor
 need(not OUT.exists()and not PUBLIC.exists(),'新計測scope一度だけ');OUT.mkdir(parents=True)
 try:
  source_preflight(OUT/'sources',download=True)
  modules=[__import__('test_pr16_dex_hof_jp_field_'+name)for name in('producer','text','chain','actions')]
  stream=io.StringIO();suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m)for m in modules)
  result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
  (OUT/'tests.txt').write_text(stream.getvalue());need(result.wasSuccessful()and not result.skipped,'新scope試験のみ')
  reconstruct.OUT=OUT/'current';reconstruct.OUT.mkdir()
  with (OUT/'reconstruct.log').open('w')as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
   raw,latest=reconstruct.reconstruct()
  need(identity(raw)==latest['candidate']==field.CANDIDATE and len(donor.bind_owners(raw,latest))==115,'同0641全SHA/全115owner')
  parent=chain.parent(*[(ROOT/p).read_bytes()for p in chain.PARENT_INPUTS])
  for hit in parent['hits']:donor.signed(raw,hit)
  regions,proof=field.regions(raw,parent)
  delta=chain.build(parent,regions,proof);full=chain.materialize(parent,delta)
  need(all(old==new for old,new in zip(parent['hits'],full['hits'])if old['address']!=field.HIT),'他873行の全field不変')
  delta_raw=chain.canonical(delta);report=measured_report(proof,delta_raw,result.testsRun)
  validate_report(report,delta_raw,parent)
  PUBLIC.mkdir();(PUBLIC/'reference-chain.json').write_bytes(delta_raw)
  (PUBLIC/'measurement.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
  (PUBLIC/'tests.json').write_text(json.dumps(dict(status='PASS_NEW_FIELD_SCOPE_TESTS',tests=result.testsRun,failures=0,errors=0,skipped=0))+'\n')
  print(json.dumps(dict(status=report['status'],tests=result.testsRun,classified=780,unclassified=94,new_native=0)))
 except Exception as exc:
  import traceback
  (OUT/'private-failure.txt').write_text(traceback.format_exc())
  frames=[dict(source=Path(t.filename).name,function=t.name,line=t.lineno)for t in traceback.extract_tb(exc.__traceback__)if Path(t.filename).parent==ROOT/'scripts']
  print(json.dumps(dict(error_code='NEW_FIELD_SCOPE_FAILED_PRIVATE_DETAILS_RETAINED',type=type(exc).__name__,source_frames=frames)))
  raise RuntimeError('NEW_FIELD_SCOPE_FAILED_PRIVATE_DETAILS_RETAINED')from None


def export():
 import pr16_dex_hof_jp_field_chain as chain
 publication.output(PUBLIC,failure=None)
 need(not any(p.is_symlink()for p in(PUBLIC,*PUBLIC.parents)),'公開path symlink拒否')
 need({p.name for p in PUBLIC.iterdir()}==FILES,'閉じた3成功textのみ')
 for p in PUBLIC.iterdir():
  need(p.is_file()and not p.is_symlink(),'regular flat textだけ')
  raw=p.read_bytes();need(0<len(raw)<750000 and raw.endswith(b'\n')and b'\0'not in raw and b'\r'not in raw,'非空LF UTF8境界');raw.decode('utf8')
 need(os.environ.get('FIELD_MEASUREMENT_OUTCOME')=='success','成功実測stepだけ')
 need(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==os.environ['GITHUB_SHA'],'公開前HEAD不変')
 need(subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=ROOT).returncode==0 and subprocess.run(['git','diff','--cached','--quiet','--'],cwd=ROOT).returncode==0,'公開前tracked/index無変更')
 parent=chain.parent(*[(ROOT/p).read_bytes()for p in chain.PARENT_INPUTS])
 report=json.loads((PUBLIC/'measurement.json').read_bytes());validate_report(report,(PUBLIC/'reference-chain.json').read_bytes(),parent)
 need(json.loads((PUBLIC/'tests.json').read_bytes())==dict(status='PASS_NEW_FIELD_SCOPE_TESTS',tests=report['unit_tests'],failures=0,errors=0,skipped=0),'固定試験summary')

if __name__=='__main__':
 need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'閉じた3操作');globals()[sys.argv[1]]()
