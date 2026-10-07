#!/usr/bin/env python3
"""新Flash受入の保存原本・終端だけを照合。測定scopeを再実行しない。"""
import copy,json,os
from pathlib import Path
import pr16_dex_hof_jp_field_actions as actions
import pr16_dex_hof_jp_field_chain as chain
import pr16_dex_hof_jp_field_text as field
ROOT=Path(__file__).resolve().parents[1]
CP='content/modernization/pr16_dex_hof_jp_field_checkpoint.json'
EVIDENCE='content/modernization/pr16_dex_hof_jp_field_evidence'
FRONTIER=EVIDENCE+'/unknown-frontier.json'
OLD_FRONTIER='content/modernization/pr16_dex_hof_registered_ui_batch_evidence/unknown-frontier.json'
GUIDE='docs/PR16_DEX_HOF_FLASH_ACCEPTED_JA.md'
HEAD='608c7e2486870cb92523abeeba65646c6d29c4ad'
RUN=37697774244
FILES={
 'measurement.json':dict(size=248568,sha256='7db68c62b1273d4b06d1dad2efac1d35d715c1a0f94462da80e215f38e57e3d9'),
 'reference-chain.json':dict(size=160664,sha256='0539ee048ea49cf0f6b492f88325a89578c43182936d6910c19a7d3c9f5cf6cd'),
 'tests.json':dict(size=97,sha256='06f4bc3e81f46f398ef37cbed56d54932871723c500276b8b50a070a00ab0696')}
need,identity,exact=field.need,field.identity,field.exact
COUNTERS=dict(schema_version=1,classified=780,unclassified=94,newly_classified=1,native_processes=0,donor_safe_bytes=0,
 current_owner_count=115,current_rom_reconstructions=1,unit_tests=117,old_full_rom_scan_runs=0,
 old_native_cases_replayed=0,formal_rom_changed=False,formal_save_changed=False,donor_eligible=False,donor_leased=False,
 all_prior_accepted_retained=True,remaining_unknown_rows_retained=True)
STEP_NAMES=['Set up job','Run actions/checkout@v4','Same branch and closed source boundary',
 'Official Ubuntu compiler for current candidate','New Flash producer and complete badge text only',
 'Closed successful text publication guard','Run actions/upload-artifact@v4','Read-only checkout and task graph',
 'Post Run actions/checkout@v4','Complete job']


def unknown_frontier(full,old):
 need(set(old)=={'candidate','total','owner_unknown','unowned_unknown','rows','donor_eligible','indirect_reference_completeness_claimed'} and old['donor_eligible']is False and old['indirect_reference_completeness_claimed']is False,'旧frontierの閉schema/安全claim')
 need(old['candidate']==full['candidate']==field.CANDIDATE and old['total']==95,'旧unknown95原本')
 rows=[r for r in old['rows']if r['hit']['address']!=field.HIT]
 need(len(rows)==94 and len(old['rows'])==95,'新1行だけをunknownから除く')
 need([r['hit']for r in rows]==[h for h in full['hits']if h['accepted']is False],'全94行が正式deltaの未分類全fieldと一致')
 out=copy.deepcopy(old);out.update(total=94,owner_unknown=0,unowned_unknown=94,rows=rows)
 need(all(not row['owners']for row in rows),'現unknownはowner外のまま')
 return out


def validate(receipt,files,frontier,root=ROOT):
 need(type(files)is dict and set(files)==set(FILES),'原本3fileだけ')
 need(all(identity(files[name])==expected for name,expected in FILES.items()),'取得原本の全byte identity')
 parent=chain.parent(*[(Path(root)/path).read_bytes()for path in chain.PARENT_INPUTS])
 oldenv={k:os.environ.get(k)for k in('GITHUB_SHA','GITHUB_RUN_ID')}
 try:
  os.environ.update(GITHUB_SHA=HEAD,GITHUB_RUN_ID=str(RUN))
  measurement=json.loads(files['measurement.json']);actions.validate_report(measurement,files['reference-chain.json'],parent)
 finally:
  for key,value in oldenv.items():
   if value is None:os.environ.pop(key,None)
   else:os.environ[key]=value
 delta=chain.read_measured(files['reference-chain.json'],FILES['reference-chain.json'],parent)
 full=chain.materialize(parent,delta)
 expected_frontier=unknown_frontier(full,json.loads((Path(root)/OLD_FRONTIER).read_bytes()))
 need(exact(frontier,expected_frontier),'旧94行を削除/改作/昇格しない')
 need(set(receipt)==set(COUNTERS)|{'status','source_head','run_id','run_attempt','conclusion','job','artifact',
  'candidate','evidence_bindings','delta_identity','measurement_identity','tests_identity','unknown_identity',
  'guide','previous_checkpoint','next_ja'},'閉じた受入receipt schema')
 for key,value in COUNTERS.items():need(exact(receipt[key],value),'厳密な受入counter/flag '+key)
 need(receipt['status']=='ACCEPTED_ONE_JP_FIELD_MINIMUM_TYPE' and receipt['source_head']==HEAD and type(receipt['run_id'])is int and receipt['run_id']==RUN and type(receipt['run_attempt'])is int and receipt['run_attempt']==1 and receipt['conclusion']=='success','初回成功source/run')
 need(exact(receipt['candidate'],field.CANDIDATE),'正式候補の不変identity')
 need(receipt['guide']==GUIDE and receipt['previous_checkpoint']==chain.PARENT_CHECKPOINT and type(receipt['next_ja'])is str and bool(receipt['next_ja']),'一意guideと親checkpoint')
 need(exact(receipt['evidence_bindings'],{EVIDENCE+'/'+k:v for k,v in FILES.items()}) and receipt['delta_identity']==FILES['reference-chain.json'] and receipt['measurement_identity']==FILES['measurement.json'] and receipt['tests_identity']==FILES['tests.json'],'原本参照と完全identity')
 need(receipt['unknown_identity']==identity(chain.canonical(frontier)),'残94unknownの完全identity')
 job=receipt['job'];steps=job['steps']
 need(type(job['id'])is int and type(job['run_id'])is int,'job整数型')
 need(set(job)=={'id','name','status','conclusion','run_id','logs_url','steps'} and job['id']==113053633223 and job['name']=='field-text' and job['status']=='completed' and job['conclusion']=='success' and job['run_id']==RUN and job['logs_url']is None,'exact successful job snapshot')
 need(type(steps)is list and len(steps)==10 and [s['name']for s in steps]==STEP_NAMES and [s['number']for s in steps]==[1,2,3,4,5,6,7,8,16,17],'全10step identity/順序')
 need(all(set(s)=={'name','status','conclusion','number'} and type(s['number'])is int and s['status']=='completed' and s['conclusion']=='success' for s in steps),'全step成功終端')
 artifact=receipt['artifact']
 need(set(artifact)=={'id','name','size_in_bytes','url','archive_download_url','expired','created_at','expires_at','updated_at','digest','workflow_run'},'閉じた取得時artifact schema')
 need(set(artifact['workflow_run'])=={'id','repository_id','head_repository_id','head_branch','head_sha'} and artifact['workflow_run']['head_branch']=='codex/modernization-followup-20260908' and artifact['workflow_run']['repository_id']==artifact['workflow_run']['head_repository_id']==1358127462,'取得runの同repository/branch')
 need(all(type(artifact[k])is int for k in ('id','size_in_bytes')) and all(type(artifact['workflow_run'][k])is int for k in ('id','repository_id','head_repository_id')),'artifact整数型')
 need(artifact['url']=='https://api.github.com/repos/dekaazarashi1111-web/pokemon-vega-modern/actions/artifacts/11515739265' and artifact['archive_download_url']==artifact['url']+'/zip','artifact URLは固定GitHub取得元')
 need(all(type(artifact[k])is str and __import__('re').fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ',artifact[k])for k in('created_at','expires_at','updated_at')),'artifact時刻の閉形式')
 need(artifact['id']==11515739265 and artifact['name']=='pr16-jp-field-text-only' and artifact['size_in_bytes']==59319 and artifact['digest']=='sha256:c6eaf390867cce15ff2bef979b4e297a58c7514bff9d03b8711ef5a98f036d08' and artifact['expired']is False and artifact['workflow_run']['id']==RUN and artifact['workflow_run']['head_sha']==HEAD,'ZIP外側完全identityと取得時run/source')
 need(json.loads(files['tests.json'])==dict(status='PASS_NEW_FIELD_SCOPE_TESTS',tests=117,failures=0,errors=0,skipped=0),'新117試験の成功原本')
 need(all(old==new for old,new in zip(parent['hits'],full['hits'])if old['address']!=field.HIT),'他873行の全field保持')
 return dict(status='PASS_RETAINED_780_CLASSIFIED_94_UNKNOWN',classified=780,unclassified=94,newly_classified=1,
  native_processes=0,measurement_replays=0,donor_safe_bytes=0)


def main():
 receipt=json.loads((ROOT/CP).read_bytes());files={name:(ROOT/EVIDENCE/name).read_bytes()for name in FILES}
 print(json.dumps(validate(receipt,files,json.loads((ROOT/FRONTIER).read_bytes())),sort_keys=True))

if __name__=='__main__':main()
