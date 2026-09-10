#!/usr/bin/env python3
"""Verify the actual Stage84 integration originals and update only the current view."""
from __future__ import annotations
import argparse
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile
import modernization_final_integration as final
import run_modernization_p06_decided_e2e as native

ROOT = Path(__file__).resolve().parents[1]
RUN = 34477344071
HEAD = '4d7365c7144cdda3ee15fca7c5cb365c87e7621d'
FINGERPRINT = '9cdfdd8fa5c0177e8f2278ebadc1e51647fdc6b184339939cd27c973d02745d4'
DIRECTORY = 'content/modernization/p08_final_evidence/34477344071'
RECEIPT = 'content/modernization/p08_final_candidate_acceptance.json'
OVERVIEW = 'content/modernization/p08_remaining_work.json'
DOMAINS = ['p02','mega_shop','floette','p03','p04_mega_runtime','battle_policy','p05']
# GitHub artifact ID, exact size, exact SHA-256. These are originals, not fixtures.
ARTIFACTS = {
 'candidate':(10152134447,282003,'ed107486691eac003c5029272edeb5b2e685ed36c9d53024e42fd19bd0866860'),
 'merged':(10152265628,11249,'51dc5b43f568c10d188aa4d0da7177b993f64ef1ac84fd6748ec677e37bede70'),
 'domain-p02':(10152220315,10470,'c1a69b93eaf1bc7bbe75bb2291e33ecce86c367a85b54b3def7667027c4b36fb'),
 'domain-mega_shop':(10152184535,10126,'d582631a552aa5b5a3d3baae07f642eb721e1d6c665c4e9a3d37643a54d4a7aa'),
 'domain-floette':(10152224970,9910,'8850643a77e6d06ea074603138a5c95b0f89e85797935bb371b2b3b100ee7f78'),
 'domain-p03':(10152170863,9672,'75515c30a914192bee1fda5cb661dd9a67a487a7ca9bb087df371966f4fa0074'),
 'domain-p04_mega_runtime':(10152172406,9606,'10a5125ecfeb1d3afcb1dd50a0c0a068048764c7f2fc72674be6c1c156288b4a'),
 'domain-battle_policy':(10152204196,11337,'60072dbc757b7fbe07223dcaa4c694bdf17afbd64598f01ba9892375006acbc7'),
 'domain-p05':(10152196002,10017,'eeaaf168dbc48700e815f1ecd87381150e86dff2820068cfe463bb22deb6e7c7'),
}
need = final.need
load = final.p06.strict_json
same = native.capture_api.same_typed
identity = final.p06.identity


def read(root, name):
    p = root/name
    need(not any(q.is_symlink() for q in (p,*p.parents)), 'symlink input')
    return p.read_bytes()


def archive(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries=z.infolist(); names=[e.filename for e in entries]
        need(len(names)==len(set(names)) and sum(e.file_size for e in entries)<6000000,'archive bounds/duplicates')
        for e in entries:
            p=Path(e.filename)
            need(not p.is_absolute() and '..' not in p.parts and '\\' not in e.filename and not e.is_dir(), 'unsafe member')
            need(((e.external_attr>>16)&0o170000)!=0o120000,'symlink member')
            need(p.suffix.lower() not in ('.gba','.sav','.srm'),'raw ROM/save forbidden in evidence')
        return {n:z.read(n) for n in names}


def fields(got, expected):
    need(type(got) is dict,'object required')
    for key,value in expected.items():
        need(same(got.get(key),value),'receipt differs: '+key)


def build(root=ROOT):
    path=Path(DIRECTORY)
    run=load(read(root,path/'actions-run.json')); jobs=load(read(root,path/'actions-jobs.json'))
    api=load(read(root,path/'actions-artifacts.json'))
    fields(run,dict(id=RUN,head_sha=HEAD,head_branch='codex/modernization-followup-20260908',run_attempt=1,
                    path='.github/workflows/modernization-final-integration.yml',event='push',status='completed',conclusion='success'))
    need(jobs['total_count']==len(jobs['jobs'])==10,'all ten workflow jobs required')
    expected={'candidate','preserve-p06-original','merge'}|{'domain ('+d+')' for d in DOMAINS}
    need({j['name'] for j in jobs['jobs']}==expected,'unexpected job set')
    for j in jobs['jobs']:
        fields(j,dict(run_id=RUN,head_sha=HEAD,status='completed',conclusion='success'))
        need(all(s['status']=='completed' and s['conclusion']=='success' for s in j['steps']),'failed/skipped step')
    by_id={a['id']:a for a in api['artifacts']}; sets={}; originals={}
    for label,(aid,size,sha) in ARTIFACTS.items():
        raw=read(root,path/(label+'.zip'));need(identity(raw)==dict(size=size,sha256=sha),'original ZIP differs: '+label)
        a=by_id[aid];fields(a,dict(id=aid,name='final-integration-'+label,size_in_bytes=size,digest='sha256:'+sha))
        fields(a['workflow_run'],dict(id=RUN,head_sha=HEAD))
        sets[label]=archive(raw);need(sets[label]['tested-head.txt'].decode().strip()==HEAD,'tested HEAD differs')
        originals[label]=dict(artifact_id=aid,size=size,sha256=sha)
    candidate=sets['candidate']; merged=sets['merged'];
    want_rom=dict(size=final.SIZE,sha256=final.SHA)
    fields(load(candidate['plan.json']),dict(input_rom=dict(path=final.ROM,**want_rom),plan_fingerprint=FINGERPRINT,domain_order=DOMAINS))
    need(candidate['build-first.json']==candidate['build-second.json'],'independent build results differ')
    fields(load(candidate['recipe-first.json']),dict(candidate=want_rom,crc32='5D95817C',release_ready=False,clean_rom_regeneration_verified=False))
    inner=archive(candidate['evidence/original.zip'])
    need(identity(candidate['evidence/original.zip'])==dict(size=final.ORIGINAL_SIZE,sha256=final.ORIGINAL_SHA),'P06 original differs')
    old=final.validate_original_members(inner)
    need(same(load(candidate['evidence/acceptance.json']),old),'P06 original acceptance differs')
    tracked_original=read(root,'content/modernization/p08_p06_evidence/34444010444/original.zip')
    need(tracked_original==candidate['evidence/original.zip'],'retained P06 original absent/different')
    p06=load(candidate['p06/result.json'])
    fields(p06,dict(status='PASS',candidate_stage=84,candidate=want_rom,validation_class='FIXED_GITHUB',
                    fresh_process_runs=8,core_instances=24,cache_reuse=0,existing_save_cases=4,new_mon_cases=4,
                    full_p06_acceptance=False,release_ready=False,active_baseline_changed=False,guards=list(native.GUARDS)))
    need(len(p06['cases'])==8 and len(p06['source_bindings'])==26,'P06 case/source count differs')
    for case,row in zip(native.CASES,p06['cases']):
        name='p06/'+'-'.join(map(str,case))
        code=native.capture_api.require_exited(load(candidate[name+'.process.json']))
        actual=native.validate(candidate[name+'.stdout'],case,code,final.SHA)
        need(same(actual,row) and not candidate[name+'.stderr'],'P06 final observation differs')
    for guard in native.GUARDS:
        name='p06/guard-'+guard
        need(native.capture_api.require_exited(load(candidate[name+'.process.json']))==1,'P06 physical guard exit')
        need(not candidate[name+'.stdout'] and candidate[name+'.stderr']==b'P03 archive: host write after observation barrier\n','P06 physical guard differs')
    for name,bind in p06['source_bindings'].items():
        need(identity(read(root,name))==bind,'final P06 source changed: '+name)
    gate=load(merged['runtime_gate.json'])
    fields(gate,dict(status='PASS_WITH_DECLARED_LIMITS',domain_order=DOMAINS,plan_fingerprint=FINGERPRINT))
    fields(gate['claims'],dict(full_p03_done=False,full_p05_done=False,release_ready=False))
    need(len(gate['domains'])==7,'seven merged domains required')
    results={}
    for d,g in zip(DOMAINS,gate['domains']):
        f=sets['domain-'+d];r=load(f['result.json'])
        fields(r,dict(id=d,status='PASS',input_rom=dict(path=final.ROM,**want_rom),plan_fingerprint=FINGERPRINT))
        need(same(r['runner_result'],load(f['runner.stdout.json'])),'raw domain result differs')
        need(hashlib.sha256(f['runner.stderr.log']).hexdigest()==r['stderr_sha256'],'domain stderr differs')
        fields(load(f['validation.json']),dict(id=d,status='DOMAIN_RESULT_VALID',plan_fingerprint=FINGERPRINT))
        for key in ('id','status','runner','runner_result','compilation','command_argument_count','stderr_sha256'):
            need(same(g[key],r[key]),'merge changed domain: '+key)
        need(identity(read(root,r['runner']['path']))=={k:r['runner'][k] for k in ('size','sha256')},'domain runner changed')
        results[d]=dict(status='PASS',original_archive='domain-'+d+'.zip',runner=r['runner'],classification=r['runner_result'].get('classification',r['runner_result'].get('state_fixture')))
    fields(load(merged['merge-summary.json']),dict(status='GITHUB_MATRIX_MERGE_PASS',matrix_mGBA_process_runs=7,merge_mGBA_process_runs=0,plan_fingerprint=FINGERPRINT))
    patches=load(candidate['handoff/manifest.json'])
    fields(patches,dict(candidate=want_rom,status='ENGINEERING_HANDOFF_NOT_RELEASE',clean_rom_patch_included=False,release_ready=False))
    for name,r in patches['artifacts'].items():
        need(identity(candidate['handoff/'+name])==r['patch'] and r['roundtrip_verified'] is True,'handoff patch differs')
    protection=load(candidate['protection.json'])
    fields(protection,dict(full_index_guard_exit=1,full_index_guard_pass=False,guard_disabled=False,originals_deleted=False,visibility_changed=False,baseline_changed=False))
    return dict(schema_version=1,status='SCOPED_FINAL_CANDIDATE_ACCEPTED_NOT_RELEASE',source_run_id=RUN,source_head_sha=HEAD,
                evidence_directory=DIRECTORY,originals=originals,candidate=want_rom,candidate_stage=84,crc32='5D95817C',
                plan_fingerprint=FINGERPRINT,domains=results,fresh_domain_processes=7,fresh_p06_processes=8,p06_core_instances=24,
                p06_adopted_species=2,p06_adopted_fields=3,p06_original_run=final.ORIGINAL_RUN,
                p06_phase_requirements_accepted=['adopted_three_fields_only','existing_and_new_slot_identity','native_stat_recalculation','normal_save_and_cold_continue'],
                p06_unaccepted_scope=['adopted_passive_battle_effects_and_applicable_phase_UI_integration'],
                historical_scope_relabelled=False,patches=patches,protection=protection,
                clean_rom_regeneration_verified=False,full_p03_acceptance=False,full_p05_acceptance=False,
                full_p06_acceptance=False,full_p07_acceptance=False,release_ready=False,active_baseline_changed=False)


def project_overview(legacy,root=ROOT):
    receipt=build(root)
    need(same(load(read(root,RECEIPT)),receipt),'current integration receipt differs')
    current=copy.deepcopy(legacy)
    current['task']='USER-MODERNIZATION-FINAL-INTEGRATION'
    current['final_candidate']=dict(stage=84,**receipt['candidate'],crc32=receipt['crc32'],release_approved=False)
    current['final_integration']=dict(source_path=RECEIPT,source_run_id=RUN,tested_head=HEAD,new_native_processes=15,
                                     old_native_acceptance_preserved_not_relabelled=True)
    current['p06_adoption']['accepted_requirements']=receipt['p06_phase_requirements_accepted']
    current['p06_adoption']['original_evidence']='content/modernization/p08_p06_evidence/34444010444/acceptance.json'
    current['p06_adoption']['final_candidate_evidence']=RECEIPT
    current['p06_adoption']['other_review_rows']='HOLD_UNLESS_EXPLICITLY_ADOPTED; not a mandatory 194-row rebalance'
    current['p07_adoption']['source_reconciliation']='docs/FINAL_INTEGRATION_HANDOFF_JA.md#仕様判断'
    current['closed_conditions']=[dict(id='SINGLE_CANDIDATE_IDENTITY',original_id='SINGLE_CANDIDATE',
        original_request='P08: one candidate, independently regenerate and test changed inputs',target='Stage84 candidate identity and inherited seven domains',
        pass_condition='full SHA matches in two independent builds and all seven fresh domain records plus eight new P06 records',evidence=RECEIPT),
        dict(id='P06_ADOPTION_EVIDENCE_CONNECTION',original_id='PHASE_ACCEPTANCE',original_request='P06 adopted two species / three fields, original and new candidate acceptance',
        target='three-byte adopted delta, slot/stat/save compatibility',pass_condition='original eight cases independently revalidated; new eight cases on Stage84',evidence=RECEIPT)]
    mapping={
      'EVOLUTION_FORM_OTHER_EGG':('P03 instruction 3-5 and acceptance','evolution/form move acquisition and relevant egg supply','native learning result, cancellation where relevant, normal save/cold Continue; existing birth/hatch/capacity passes retained','scripts/run_modernization_remaining_routes.py; original P03 route table; no blanket cross-product'),
      'ARCHIVE_ECONOMY':('P03 instruction 4; P07 instruction 4','archive unlock/cost/supply','adopt either current HoF + Move Memory + zero fee or a specified replacement; test only resulting changes','config/modernization_p03_stage74_supply.json runtime.unlock/runtime.economy'),
      'NATURAL_CAPTURE_GEAR':('P05 original acceptance and current P08 boundary','natural capture/item acquisition to battle','normal acquisition into battle; no fixture replacement after observation boundary','scripts/run_modernization_p05_controller_witness.py and run_modernization_p05_scheduler_e2e.py are accepted downstream evidence, not capture evidence'),
      'PHYSICAL_CIRCUS_ADMISSION':('P05 suppression requirement and current P08 boundary','actual reception/admission to suppression','reach battle from the actual facility entrance; do not substitute writing the Circus flag','Stage84 circus-source-audit covers only bounded reviewed sources; actual entrance not identified by that audit'),
      'PHASE_ACCEPTANCE':('P06 instruction 3-5','remaining applicable phase integration of adopted changes','connect the accepted four requirement groups; verify adopted passive effects and applicable UI, without adopting all review rows','scripts/run_modernization_p06_decided_e2e.py --candidate-stage 84; receipt p06_unaccepted_scope'),
      'SOURCE_RECONCILIATION_ADOPTION':('07_extra_learnsets.txt instruction 1-5','normal-to-Vega and Vega-to-normal deltas','approved species/form, move, route, timing, limits and supply rows; exact compile/UI/save match','docs/FINAL_INTEGRATION_HANDOFF_JA.md#仕様判断; tools/modernization_p07_learnsets.py'),
      'SINGLE_CANDIDATE':('P08 final-candidate acceptance','native final-candidate coverage beyond inherited seven-domain regression','close named remaining native routes and bind any required impact regression to Stage84; old Stage82 results stay historical','identity/build/seven-domain/P06 regression closed; native and specification gaps listed separately'),
      'REPOSITORY_GUARD':('current request protection clause','public visibility and tracked originals','approved containment/remediation; distinguish full-index failure from passing new-file guard','receipt protection; public repo contains three tracked ROM/save paths; no permission/delete/history action authorized'),
      'RELEASE_DECISION':('P08 handoff and current request end conditions','clean-input regeneration and releasable package','clean-ROM two-build reproducibility, required acceptance and safe package; merge/baseline switch are NOT implied','four tested engineering BPS patches exist; clean-ROM patch and full acceptance are not complete'),
    }
    for row in current['remaining_conditions']:
        req,target,criteria,resume=mapping[row['id']]
        row.update(original_request=req,target_function=target,pass_condition=criteria,success_evidence=None,resume=resume)
        if row['id']=='SINGLE_CANDIDATE':
            row['id']='FINAL_NATIVE_ACCEPTANCE';row['reason_ja']='Stage84への候補統一・7領域回帰・P06新規8件は完了。残る必要なnative経路と変更影響の受入は未完了。'
        elif row['id']=='PHASE_ACCEPTANCE':
            row['reason_ja']='採用3項目・旧成功原本・Stage84のslot/能力値/通常保存は工程受入へ接続済み。採用特性の戦闘効果と適用範囲のUI受入が未完了。監査194行の全採用は要求しない。'
        elif row['id']=='SOURCE_RECONCILIATION_ADOPTION':
            row['reason_ja']='双方向分離・原作基準保持・経路別採用は確定。照合資料の推奨上限・代替案から具体的な採用行を一意に確定できず、配布行の判断が必要。'
    current['source_bindings'][RECEIPT]=identity(read(root,RECEIPT))
    from modernization_owner_policy import project
    return project(current, root)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
    try:
        receipt=build()
        path=ROOT/RECEIPT
        if args.write:
            need(not path.exists() and not path.is_symlink(),'receipt already exists')
            path.write_bytes(final.stable(receipt))
        else:
            need(same(load(read(ROOT,RECEIPT)),receipt),'receipt differs')
        import record_modernization_p03_forgetting as previous
        legacy=previous.remaining_work(ROOT,previous.build())
        current=project_overview(legacy)
        if args.write:(ROOT/OVERVIEW).write_bytes(final.stable(current))
        else:need(same(load(read(ROOT,OVERVIEW)),current),'current remaining-work view differs')
        print(json.dumps(dict(status='PASS',source_run_id=RUN,candidate_sha256=final.SHA,originals_verified=9,
                              new_emulator_runs=0,release_ready=False)));return 0
    except (OSError,ValueError,KeyError,TypeError,zipfile.BadZipFile) as exc:
        print('final acceptance: '+str(exc),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
