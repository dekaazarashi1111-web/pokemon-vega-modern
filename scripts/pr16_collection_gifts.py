#!/usr/bin/env python3
"""Issue19: remaining collection gifts via physical NPC/menu/Save/Continue.

The initial party, location, unlocks and unclaimed collection owner are fixtures.
No old native suite, original generator, ARM builder or accepted case is run.
"""
from __future__ import annotations
from collections import Counter
import datetime
import json
import os
from pathlib import Path
import re
import shlex
import struct
import subprocess
import sys
from zoneinfo import ZoneInfo
sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parent)]
import pr16_natural_supply as s
m, egg = s.m, s.egg
ROOT = s.ROOT
need, identity, load, write = s.need, s.identity, s.load, s.write
TASK = 'USER-20260925-COLLECTION-GIFTS'
SELF = 'scripts/pr16_collection_gifts.py'
TEST = 'tests/test_pr16_collection_gifts.py'
C = 'tools/mgba_pr16_collection_gifts.c'
WF = '.github/workflows/pr16-supply-followup-20260925.yml'
MODEL = 'content/collection_supply_v1/canonical_model.json'
CONFIG = 'config/collection_supply_v1.json'
CODE = {SELF, TEST, C, WF, 'scripts/pr16_collection_gift_bg.py', 'tests/test_pr16_collection_gift_bg.py'}
CP = m.BASE + 'pr16_collection_gifts_checkpoint.json'
GUIDE = 'docs/PR16_COLLECTION_GIFTS_JA.md'
EVIDENCE = m.BASE + 'pr16_collection_gifts_evidence'
WORK = ROOT / '.local/pr16-collection-gifts'
PROOF = WORK / 'proof'
SHOTS = WORK / 'screens'
CANDIDATE = s.CANDIDATE
SCOPE = 'COLLECTION_NPC_INITIAL_MOVES_SAVE_CONTINUE'
NEXT = ('Issue19: Collection配布18件の保存成功を再実行しない。未受入の研究タマゴ孵化後のform/技保持、'
        '釣り/隠し野生の特殊技順を続ける。全owner/全供給/Issue19/release/baseline切替は未完。'
        '旧自然配布・孵化3/EXP進化共有3/EXP4/アメ11/Bag23/egg8/旧野生/ARM/Wikiは変更影響なし。')


def vectors(model, rows, pp):
    """Independent accepted original spans, not results or candidate move bytes."""
    gifts, forms = model['gifts'], model['forms']
    need(len(gifts) == 18 and Counter(g['kind'] for g in gifts) == {'FIXED': 3, 'RESEARCH_EGG': 15}, '18 authored gift routes')
    result = []
    seen = set()
    for index, gift in enumerate(gifts):
        form_index = gift['form_index']
        need(type(form_index) is int and 0 <= form_index < len(forms), 'form index')
        form = forms[form_index]
        sid = form['target_species']
        need(type(sid) is int and 0 < sid < 1671 and sid not in seen, 'distinct explicit owner')
        seen.add(sid)
        is_egg = int(gift['kind'] == 'RESEARCH_EGG')
        need(gift['kind_id'] == is_egg and form['method'] in ('FIXED_GIFT', 'RESEARCH_EGG'), 'gift kind agreement')
        need(form['method'] == ('RESEARCH_EGG' if is_egg else 'FIXED_GIFT'), 'form/gift method')
        need(type(gift['unlock_id']) is int and 0 <= gift['unlock_id'] <= 18, 'reviewed fixture unlock')
        need(sid in rows and rows[sid], 'prepared original owner; never fallback')
        level = 1 if is_egg else 50
        moves = s.boundary.n.initial(rows[sid], level)
        need(any(moves) and len(moves) == 4, 'nonvacuous original initial moves')
        canonical = [pp[move] if move else 0 for move in moves]
        need(all(type(x) is int and 1 <= x <= 64 for x, move in zip(canonical, moves) if move), 'canonical PP')
        bit = gift['claim_bit']
        need(type(bit) is int and 0 <= bit < 8, 'claim bit bounds')
        name = ('research-egg-' if is_egg else 'fixed-form-') + str(sid)
        result.append(dict(name=name, gift_index=index, form_index=form_index, species=sid,
                           level=level, is_egg=is_egg, claim_bit=bit,
                           display_name=gift['display_name'], moves=moves, pp=canonical,
                           original_rows=[list(row) for row in rows[sid]], unlock_id=gift['unlock_id']))
    need(sorted(v['claim_bit'] for v in result if not v['is_egg']) == [0, 1, 2], 'unique fixed claims')
    return sorted(result, key=lambda v: (v['is_egg'], v['gift_index']))


def geometry(rom, config):
    # Collection SupplyはNPCではなく通常A入力のBG eventを追加する。
    from pr16_collection_gift_bg import geometry as bg_geometry
    return bg_geometry(rom, config)


def header(cases, geo):
    arr = lambda v: '{'+','.join(str(x)+'U' for x in v)+'}'
    lines = ['/* Original source oracle. Not decoded from observed party results. */']
    lines += ['#define CF_'+k.upper()+' '+str(geo[k])+'U' for k in ('group','number','x','y','host_index','local_id','script')]
    lines += ['struct CFCase {const char *name; unsigned index,species,level,egg,bit; unsigned moves[4],pp[4];};',
              'static const struct CFCase cf_cases[] = {']
    for v in cases:
        lines.append(' {"'+v['name']+'",'+','.join(str(v[k])+'U' for k in ('gift_index','species','level','is_egg','claim_bit'))+','+arr(v['moves'])+','+arr(v['pp'])+'},')
    return '\n'.join(lines+['};', ''])


def validate(out, err, case, geo):
    r = json.loads(out, object_pairs_hook=egg.strict_pairs)
    fixed = dict(schema_version=1, status='PASS', scope=SCOPE, case=case['name'],
                 candidate_sha256=CANDIDATE['sha256'], gift_index=case['gift_index'],
                 species=case['species'], level=case['level'], is_egg=case['is_egg'],
                 moves=case['moves'], pp=case['pp'], npc_script=geo['script'],
                 fresh_cores=2, denied_host_write_apis=7, guarded_phases=4,
                 party_preserved_bytes=200, initial_party_map_unlock_claim_are_fixtures=True,
                 story_acquisition_verified=False, egg_hatch_verified=False,
                 all_owners_accepted=False, issue19_complete=False, release_ready=False, warnings_errors=0)
    dynamic = {'witness', 'save_counters', 'owner_claim_bits', 'native_save_steps'}
    need(set(r) == set(fixed) | dynamic, 'strict result schema')
    for k, v in fixed.items():
        need(type(r[k]) is type(v) and r[k] == v, 'result '+k)
    keys = ('boundary', 'root', 'list', 'selected', 'claimed', 'returned', 'saved', 'continued', 'revisited', 'cancelled')
    t = r['witness']
    need(type(t) is dict and set(t) == set(keys), 'witness keys')
    need(all(type(t[k]) is int for k in keys) and 0 < t[keys[0]] and
         all(t[a] < t[b] for a,b in zip(keys, keys[1:])) and t['cancelled'] < 150000, 'strict physical chronology')
    counters = r['save_counters']
    need(type(counters) is list and len(counters) == 5 and all(type(x) is int and x >= 0 for x in counters), 'counter types')
    need(0 < counters[1]-counters[0] <= 8 and counters[2] == counters[1]+1 and counters[2:] == [counters[2]]*3, 'native gift/manual Save/fresh Continue/cancel counters')
    labels = (b'fixture', b'claimed', b'saved', b'continued', b'cancelled')
    parts = re.findall(rb'^CF_PARTY stage=(\w+) counter=(\d+) hex=([0-9a-f]+)$', err, re.M)
    need(len(parts) == err.count(b'CF_PARTY ') == 5 and tuple(x[0] for x in parts) == labels, 'complete raw party witnesses')
    need([int(x[1]) for x in parts] == counters, 'counter/party binding')
    raw = [bytes.fromhex(x[2].decode()) for x in parts]
    need(len(raw[0]) == 100 and all(len(x) == 200 for x in raw[1:]), 'whole party sizes')
    need(raw[0] == raw[1][:100] and raw[1] == raw[2] == raw[3] == raw[4], 'party persisted and cancel read-only')
    child = raw[1][100:]
    need(struct.unpack_from('<H', child, 32)[0] == case['species'] and child[84] == case['level'], 'independent raw owner/level')
    need(list(struct.unpack_from('<4H', child, 44)) == case['moves'] and list(child[52:56]) == case['pp'] and child[40] == 0, 'independent raw move/PP/bonus')
    mon = re.findall(rb'^CF_MON stage=(claimed|continued|cancelled) species=(\d+) level=(\d+) egg=(\d+) hp=(\d+) max=(\d+)$', err, re.M)
    need(len(mon) == err.count(b'CF_MON ') == 3 and [x[0] for x in mon] == [b'claimed',b'continued',b'cancelled'], 'getter lifecycle')
    for row in mon:
        species,level,is_egg,hp,maximum=map(int,row[1:])
        need((species,level,is_egg)==(case['species'],case['level'],case['is_egg']) and 0<hp<=maximum, 'native owner/egg getter witness')
    need(0 < struct.unpack_from('<H', child, 86)[0] <= struct.unpack_from('<H', child, 88)[0], 'raw HP')
    claims = r['owner_claim_bits']; wanted = 0 if case['is_egg'] else 1 << case['claim_bit']
    need(claims == [0, wanted, wanted, wanted, wanted] and all(type(x) is int for x in claims), 'claim lifecycle')
    owners = re.findall(rb'^CF_OWNER stage=(\w+) hex=([0-9a-f]{1024})$', err, re.M)
    need(len(owners) == err.count(b'CF_OWNER ') == 5 and tuple(x[0] for x in owners) == labels, 'owner lifecycle')
    import zlib
    for i, (_, hx) in enumerate(owners):
        owner = bytearray.fromhex(hx.decode()); crc = struct.unpack_from('<I', owner, 12)[0]; owner[12:16] = bytes(4)
        need(struct.unpack_from('<IIHH', owner) == (0x31565343, 0xcea9acbc, 1, 512), 'owner ABI')
        need(zlib.crc32(owner) & 0xffffffff == crc and owner[20] == 0 and owner[80] == claims[i], 'raw owner CRC/pending/claim')
    need(owners[1][1] == owners[2][1] == owners[3][1] == owners[4][1], 'collection owner unchanged after gift')
    steps = re.findall(rb'^CF_SAVE frame=(\d+) before=(\d+) after=(\d+) count=(\d+) lock=(\d+)$', err, re.M)
    need(type(r['native_save_steps']) is int and r['native_save_steps'] == len(steps) == counters[1]-counters[0], 'raw gift saves')
    previous_frame, previous_counter = t['selected'], counters[0]
    for row in steps:
        frame, before, after, count, lock = map(int, row)
        need(previous_frame < frame < t['returned'] and before == previous_counter and after == before+1 and count in (1,2) and lock == 1, 'native save chronology')
        previous_frame, previous_counter = frame, after
    need(previous_counter == counters[1], 'complete save transition chain')
    need(err.count(b'original core destroyed; new core boot and normal Continue\n') == 1 and
         b'host write after observation barrier' not in err and b'mGBA[' not in err, 'fresh core/host barriers/logs')
    return dict(r, party_identity=identity(raw[1]))


def pending(accepted, contracts):
    need(set(accepted) <= set(contracts), 'unknown accepted case')
    for name, row in accepted.items():
        need(row['contract'] == contracts[name] and row['result']['status'] == 'PASS', 'accepted input changed; require impact review '+name)
    return [name for name in contracts if name not in accepted]


def execute():
    from pr16_learnset_wiki_actions import current, acquire
    import pr16_learnset_battle as battle
    import pr16_learnset_entry_repair as entry
    import pr16_learnset_wild_repair as wild
    head = current(); need(not WORK.exists(), 'fresh execution directory required')
    PROOF.mkdir(parents=True); SHOTS.mkdir()
    old = load(ROOT/CP) if (ROOT/CP).exists() else {}
    protected = set(m.PROTECTED) | {s.CP, egg.CP, s.boundary.CP, s.boundary.n.CP, m.BASE+'pr16_exp_evolution_share_checkpoint.json'}
    bindings = CODE | {MODEL, CONFIG, s.SELF, egg.SELF, egg.PARENT,
                       'overlays/collection_supply_v1/collection_supply_v1.c', 'overlays/collection_supply_v1/collection_supply_v1.h'}
    v = dict(schema_version=1, task=TASK, status='RUNNING', source_head=head, run_id=int(os.environ['GITHUB_RUN_ID']),
             candidate=CANDIDATE, accepted=old.get('accepted',{}), results=[], failures={},
             new_unit_tests=0, native_processes=0, host_compiles=0, arm_compiles=0, rom_changes=0,
             accepted_case_reruns=0, wiki_generations=0, actions_completion_confirmed=False,
             issue19_complete=False, release_ready=False, active_baseline_changed=False,
             prior_runs=old.get('prior_runs',[])+([old['run_id']] if old else []),
             source_bindings={p:identity((ROOT/p).read_bytes()) for p in bindings},
             protected_bindings={p:identity((ROOT/p).read_bytes()) for p in protected})
    previous=m.PROOF; m.PROOF=PROOF
    try:
        # New pure tests only; cache future unchanged test execution via original evidence.
        test_binding={p:identity((ROOT/p).read_bytes()) for p in (TEST,SELF,C,'scripts/pr16_collection_gift_bg.py','tests/test_pr16_collection_gift_bg.py')}
        if old.get('unit_binding') == test_binding and old.get('unit_passed'):
            v.update(unit_binding=test_binding, unit_passed=True, unit_origin=old.get('unit_origin',old['run_id']))
        else:
            _, err=m.run([sys.executable,'-B','-m','unittest','tests.test_pr16_collection_gifts','tests.test_pr16_collection_gift_bg','-v'],'unit')
            count=re.search(rb'Ran (\d+) tests? in ',err);need(count and b'\nOK\n' in err,'new unit result')
            v.update(new_unit_tests=int(count[1]),unit_binding=test_binding,unit_passed=True,unit_origin=v['run_id'])
        cp=load(ROOT/s.boundary.n.CP); need(cp['candidate']==CANDIDATE and cp['actions_completion_confirmed'], 'accepted candidate source')
        battle.WORK=WORK/'restore';battle.WORK.mkdir();parent=battle.restore();rom,recipe=entry.apply(parent);rom=wild.replay(rom,cp['wild_repair'])
        need(identity(rom)==CANDIDATE,'immutable restored candidate');(WORK/'candidate.gba').write_bytes(rom)
        write(PROOF/'recipe.json', {'entry':recipe,'wild':cp['wild_repair']})
        source=load(ROOT/m.BASE/'pr16_learnset_payload_checkpoint.json')
        acquire(source['payload_artifact'],source['source_head'],WORK/'payload',dict(source['summary']['files'],**{'receipt.json':source['proof_bindings']['receipt.json']}))
        rows,audit=s.boundary.n.sources(WORK/'payload')
        table=struct.unpack_from('<I',rom,0x1cc)[0]-0x08000000;need(table==0x10421f4,'canonical PP root')
        pp={mid:rom[table+12*mid+4] for mid in range(1063)}
        model=load(ROOT/MODEL)
        if any(model['forms'][g['form_index']]['target_species']==1029 for g in model['gifts']):
            floette=load(ROOT/m.BASE/'pr16_learnset_floette_checkpoint.json')
            acquire(floette['payload_artifact'],floette['source_head'],WORK/'floette',dict(floette['summary']['files'],**{'receipt.json':floette['proof_bindings']['receipt.json']}))
            span=(WORK/'floette/floette.level_up.bin').read_bytes()
            need(identity(span)==floette['summary']['files']['floette.level_up.bin'],'Floette original span')
            rows[1029]=s.boundary.n.p.decode_span(span,'level_up');audit['floette_span']=identity(span)
        cases=vectors(model,rows,pp);v['declared_cases']=[case['name'] for case in cases]
        geo=geometry(rom,load(ROOT/CONFIG))
        write(PROOF/'oracle.json',dict(cases=cases,geometry=geo,source=audit,model=identity((ROOT/MODEL).read_bytes())))
        helper=s.hatch_source(s.hatch_cases({1:1,649:1}))
        # Only reusable key/guard/getter helpers are called. The embedded daycare main is never called.
        generated={}
        def put(name,text):
            (WORK/name).write_text(text); generated[name]=identity(text.encode())
        for i,(source,target) in enumerate(egg.EMBEDDED):
            text,n=re.subn(r'\bint\s+main\s*\(', 'int cf_inherited_'+str(i)+'(', (ROOT/source).read_text());need(n==1,'one embedded main');put(target,text)
        put('cf_helpers.c',egg.once(helper,'int main(int argc,char **argv)','int cf_unused_daycare_main(int argc,char **argv)'))
        put('cf_vectors.h',header(cases,geo));(PROOF/'vectors.h').write_bytes((WORK/'cf_vectors.h').read_bytes())
        contracts={case['name']:dict(candidate=CANDIDATE,case=case,geometry=geo,controller=identity((ROOT/C).read_bytes()),helpers=identity(helper.encode())) for case in cases}
        todo=pending(v['accepted'],contracts);need(todo,'all cases already accepted; completion only')
        v.update(contracts=contracts,selected_cases=todo,generated_sources=generated)
        for name, accepted in v['accepted'].items():
            origin=ROOT/EVIDENCE/str(accepted['run_id']);saved=load(origin/'verification.json')
            for suffix in ('.stdout.txt','.stderr.txt','.process.json'):
                p=origin/(name+suffix);need(identity(p.read_bytes())==saved['proof_bindings'][p.name],'accepted evidence unchanged')
        dep=WORK/'native.d';v['host_compiles']+=1
        _,err=m.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(WORK),'-MMD','-MF',str(dep),C,'-lmgba','-o',str(WORK/'native')],'compile')
        need(not err,'host compiler warnings')
        for name in shlex.split(dep.read_text().replace('\\\n',' ').split(':',1)[1]):
            p=Path(name);p=(p if p.is_absolute() else ROOT/p).resolve()
            if p.parent==WORK:need(identity(p.read_bytes())==generated[p.name],'generated source binding')
            else:v.setdefault('compiled_sources',{})[p.relative_to(ROOT).as_posix()]=identity(p.read_bytes())
        seed=(ROOT/m.SEED).read_bytes();stamp=(ROOT/m.SEED).stat().st_mtime_ns;need(identity(seed)==m.SEED_ID,'seed identity')
        byname={c['name']:c for c in cases};attempted=[]
        for name in todo:
            attempted.append(name);fixture=WORK/(name+'.srm');fixture.write_bytes(seed);v['native_processes']+=1
            try:
                out,err=m.run([str(WORK/'native'),str(WORK/'candidate.gba'),str(fixture),CANDIDATE['sha256'],m.SEED_ID['sha256'],name,str(SHOTS/name)],name,600)
                result=validate(out,err,byname[name],geo);v['results'].append(result)
                v['accepted'][name]=dict(run_id=v['run_id'],source_head=head,contract=contracts[name],result=result)
            except Exception as ex:
                v['failures'][name]=dict(type=type(ex).__name__,error=str(ex).replace(str(ROOT),'$REPO'))
                break  # Do not repeat a common blocked UI boundary across the remaining cases.
            write(PROOF/'verification.json',v)
        v['selected_cases']=attempted;v['pending_cases']=[c['name'] for c in cases if c['name'] not in v['accepted']]
        need((ROOT/m.SEED).read_bytes()==seed and (ROOT/m.SEED).stat().st_mtime_ns==stamp and identity((WORK/'candidate.gba').read_bytes())==CANDIDATE,'private inputs unchanged')
        need(v['protected_bindings']=={p:identity((ROOT/p).read_bytes()) for p in protected},'old acceptance unchanged')
        v['status']='PASS_COLLECTION_GIFTS_SCOPED' if len(v['accepted'])==18 else 'PARTIAL_COLLECTION_GIFTS'
        need(not v['failures'],'native/validation failure recorded')
    except Exception as ex:
        if v['status']=='RUNNING':v['status']='FAIL'
        v.update(error_type=type(ex).__name__,error=str(ex).replace(str(ROOT),'$REPO'));raise
    finally:
        v['screenshots']={p.name:identity(p.read_bytes()) for p in SHOTS.glob('*.ppm')}
        v['proof_bindings']={p.name:identity(p.read_bytes()) for p in PROOF.iterdir() if p.is_file() and p.name!='verification.json'}
        write(PROOF/'verification.json',v);m.PROOF=previous


def owned():
    dest=ROOT/EVIDENCE/os.environ.get('GITHUB_RUN_ID','')
    return {CP,GUIDE,m.STATE,m.DOC,'design/run_log.md','design/version_log.md'} | {p.relative_to(ROOT).as_posix() for p in dest.rglob('*') if p.is_file()}


def publish(v,completion=False):
    from pr16_learnset_compact_record import publish_resume
    good=list(v['accepted']);pending_names=[n for n in v.get('contracts',{}) if n not in good]
    nextstep=NEXT if v['actions_completion_confirmed'] else ('保存成功18件のnative/旧試験は再実行せず、completeでActions/artifact終端だけ照合。' if len(good)==18 else 'Collection配布checkpointの失敗原本を確認し未成功caseだけ修復。保存成功と旧受入は再実行しない。')
    text=f'# PR16 Issue19: Collection配布の原本初期技\n\n状態 `{v["status"]}`。限定受入 {len(good)}/18。Actions終端 `{v["actions_completion_confirmed"]}`。\n\nsource `{v["source_head"]}` / run `{v["run_id"]}`。候補 `{CANDIDATE["sha256"]}` / 33554432 bytes。ROM・runtimeは変更しない。\n\n## 範囲\n\n18経路（固定form3、研究タマゴ15）の実NPC・root/menu/page/選択・配布・通常Save・fresh-core Continue・再訪取消。初期party、開始場所、全unlock、未受領ownerはfixture。ストーリー到達・研究ランク獲得・タマゴ孵化・全owner・releaseを含まない。\n\n配布以降は7host書込APIを拒否し通常キー入力のみ。getterはguard外の読み取り補助として分離。4技/PP/PP Ups/HP/egg bit/元party100byte/全party200byte/owner CRCとclaim bit/Save counterをraw textで独立照合。固定配布のclaim bit保持は確認するが、二重受領の実選択はこの試験では行わない。\n\n| case | species | level | egg | 原本4技 | 実測run |\n| --- | ---: | ---: | ---: | --- | ---: |\n'
    for name,a in v['accepted'].items():
        r=a['result'];text+=f'| {name} | {r["species"]} | {r["level"]} | {r["is_egg"]} | {r["moves"]} | {a["run_id"]} |\n'
    text+=f'\n未成功 `{pending_names}`。今回新unit {v["new_unit_tests"]}、host compile {v["host_compiles"]}、native process {v["native_processes"]}。旧自然供給3、EXP、Bag、egg8、通常野生、ARM/Wikiを再実行しない。source入力転送run36108830541/36109072704は検証件数へ数えない。失敗原本は成功に書き換えない。\n\n## 次\n\n{nextstep}\n'
    (ROOT/GUIDE).write_text(text)
    state=load(ROOT/m.STATE);now=datetime.datetime.now(datetime.timezone.utc)
    state['learnset_collection_gifts']={k:v[k] for k in ('status','source_head','run_id','candidate','actions_completion_confirmed','issue19_complete')}
    state['learnset_collection_gifts'].update(path=CP,accepted_cases=good,pending_cases=pending_names)
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_date_jst']=now.astimezone(ZoneInfo('Asia/Tokyo')).date().isoformat()
    state['observed_head_semantics']='Collection配布限定18経路の実測source/記録source。既受入3件/全Issue19完成とは別。'
    state['observed_head_checks']=dict(scope_head=v['source_head'],runs=v.get('terminal_actions',[dict(id=v['run_id'],status='in_progress',conclusion=None)]),reason_ja='実測成功とActions終端を区別。一般CI/action_requiredや全体完成へ昇格しない。')
    state['bp']['current_stop']=f'Issue19: Collection配布{len(good)}/18。{v["status"]}。全体未完。';state['bp']['next_step']=nextstep
    state['next_action']=dict(state['next_action'],id='COLLECTION_GIFTS' if not v['actions_completion_confirmed'] else 'SPECIAL_WILD_AND_RESEARCH_HATCH',goal_ja=nextstep,read_paths=[GUIDE,CP,SELF,TEST])
    for p in CODE|{CP,GUIDE}:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    note=f'\n## {now.isoformat()}\n- Timestamp: {now.isoformat()}\n- Task: {TASK}\n- Version: issue19-collection-gifts-v1\n- Status: '+('DONE（18経路限定、全体未完）' if v['actions_completion_confirmed'] else 'STOPPED（保存原本から未完だけ継続）')+f'\n- Summary: 実NPC/原本初期技/Save/fresh Continue {len(good)}/18。初期party/場所/unlock/未受領ownerはfixture、研究タマゴ孵化は未受入。\n- Files changed: driver/C/新unit/限定Actions、checkpoint/guide/text証拠、固定引継ぎMD/JSON、両ログ。\n- Verify: 新unit{v["new_unit_tests"]} host{v["host_compiles"]} native{v["native_processes"]}、Actions終端{v["actions_completion_confirmed"]}。終端専用={completion}（専用時native/旧unit/host/ARM再実行0）。旧自然供給3/EXP/Bag/egg8/旧野生/Wiki不変。\n- Commit: 同branchへ非force push、reflected-head.txt/remote照合。\n- Network: GitHub固定source/保存artifact/Actions。ROM・元saveは非追跡。merge/release/baseline切替なし。\n'
    for p in ('design/run_log.md','design/version_log.md'):
        with (ROOT/p).open('a') as f:f.write(note)


def record():
    from pr16_learnset_wiki_actions import current
    from common import redact_user_paths,user_absolute_path_lines
    current();v=load(PROOF/'verification.json');need(v['source_head']==os.environ['GITHUB_SHA'],'record source')
    dest=ROOT/EVIDENCE/str(v['run_id']);need(not dest.exists(),'no evidence overwrite');dest.mkdir(parents=True)
    for p in PROOF.iterdir():
        if not p.is_file():continue
        raw=p.read_bytes();text=raw.decode();need('\0' not in text,'text evidence only')
        safe='\n'.join(x.rstrip() for x in redact_user_paths(text).splitlines()).rstrip()+'\n' if text else ''
        need(not user_absolute_path_lines(safe),'no user path');(dest/p.name).write_text(safe)
    v['public_evidence_bindings']={p.name:identity(p.read_bytes()) for p in dest.iterdir()};v['evidence_path']=dest.relative_to(ROOT).as_posix()
    write(ROOT/CP,v);publish(v)


def complete():
    from pr16_learnset_wiki_actions import current
    from pr16_wiki_reconcile import fetch
    current();v=load(ROOT/CP);need(len(v['accepted'])==18 and not v['actions_completion_confirmed'],'18 cases before completion; no repeats')
    runs=[]
    for rid in sorted(set(v['prior_runs']+[v['run_id']])):
        run=fetch('actions/runs/'+str(rid));need(run['status']=='completed' and run['head_branch']==m.BRANCH and run['path']==WF,'terminal scoped run')
        jobs=fetch('actions/runs/'+str(rid)+'/jobs?per_page=100');need(jobs['total_count']==len(jobs['jobs'])==1,'complete jobs')
        if rid==v['run_id']:need(run['head_sha']==v['source_head'] and run['conclusion']=='success' and all(x['conclusion'] in ('success','skipped') for x in jobs['jobs'][0]['steps']),'last run all steps')
        runs.append({k:run[k] for k in ('id','head_sha','status','conclusion','path')})
    for p,binding in v['public_evidence_bindings'].items():need(identity((ROOT/v['evidence_path']/p).read_bytes())==binding,'public evidence unchanged')
    for p,binding in v['source_bindings'].items():
        if p!=WF:need(identity((ROOT/p).read_bytes())==binding,'executed source unchanged '+p)
    v.update(actions_completion_confirmed=True,terminal_actions=runs,completed_by_source=os.environ['GITHUB_SHA'])
    write(ROOT/CP,v);publish(v,True);PROOF.mkdir(parents=True,exist_ok=True)
    write(PROOF/'completion.json',dict(task=TASK,terminal_actions=runs,new_native_processes=0,new_unit_tests=0,host_compiles=0,rom_changes=0))


def guard():
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned();g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__=='__main__':
    actions=dict(execute=execute,record=record,complete=complete,guard=guard,paths=lambda:print('\n'.join(sorted(owned()))))
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|complete|guard|paths');actions[sys.argv[1]]()
