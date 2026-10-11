#!/usr/bin/env python3
"""次戦の再生成ownerだけを固定source/実candidateから抽出。native再実行なし。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_bp_exchange_successor as parent
OUT=ROOT/'.local/pr16-bp-party-retention-run'
SOURCE_HEAD='c0dc2ccee1e0253a0c8d8604c6a7312f04a133a3'
SHA='7f32ba99ad34cd0320559a8dc6990876084f371c8bfae769c7482090c7be90cd'
TERMS=('BuildTrainerPartySetup','IsRandomBattleTowerBattle','BuildFrontierParty','CB2_InitBattle')

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((ROOT/'config/github_private_environment.json').read_bytes())
    name='pokemon-vega-private-env-v1-state.zip'
    bound=next(x for x in cfg['archives'] if x['name']==name)
    archive=ROOT/'.local/pr16-bp-trial-native-inputs'/name
    data=archive.read_bytes();parent.need(parent.identity(data)==dict(size=bound['size'],sha256=bound['sha256']),'state archive changed')
    source_paths=('vendor/upstream/CFRU-JP/src/build_pokemon.c','vendor/upstream/CFRU-JP/src/frontier.c',
                  'vendor/upstream/CFRU-JP/include/new/frontier.h')
    sources={};hits={};names=[]
    with zipfile.ZipFile(archive) as z:
        for path in source_paths:
            raw=z.read(path);sources[path]=raw.decode('utf-8')
        raw=sources[source_paths[0]].encode()
        blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        parent.need(blob=='99f58ab79046546230e5ce6fc769dcfb7d5a0e29','upstream source differs from locked commit')
        for item in z.infolist():
            n=item.filename
            if not n.startswith(('generated/','reports/','build/','vendor/upstream/CFRU-JP/')):continue
            if item.file_size>16000000 or Path(n).suffix not in ('.json','.txt','.map','.sym','.ld','.s','.asm'):continue
            if any(t in n.lower() for t in ('credential','secret','device')):continue
            raw=z.read(n)
            if not any(t.encode() in raw for t in TERMS):continue
            text=raw.decode('utf-8');rows=text.splitlines();selected=set()
            for i,line in enumerate(rows):
                if any(t in line for t in TERMS):selected.update(range(max(0,i-2),min(len(rows),i+3)))
            snippets=[dict(line=i+1,text=rows[i][:1500]) for i in sorted(selected)]
            hits[n]=dict(**parent.identity(raw),snippets=snippets[:120])
        names=[n for n in z.namelist() if any(t in n.lower() for t in ('symbol','battle_core')) and n.endswith(('.json','.txt','.map','.sym'))]
    (OUT/'upstream-source.json').write_bytes(parent.stable(sources))
    recipe=parent.run();rom=(parent.OUT/'candidate.gba').read_bytes()
    parent.need(parent.identity(rom)==dict(size=33554432,sha256=SHA),'candidate identity differs')
    slices={}
    for label,start,size in [('battle_init',0xFEC4,0x500),('prepare_battle',0x12CE714,0xA4),('next_scripts',0x12CF680,0x78)]:
        raw=rom[start:start+size];p=OUT/(label+'.bin');p.write_bytes(raw)
        dis=subprocess.check_output(['arm-none-eabi-objdump','-D','-b','binary','-m','arm','-M','force-thumb','--adjust-vma='+hex(0x08000000+start),str(p)],text=True)
        p.unlink()
        slices[label]=dict(address=0x08000000+start,hex=raw.hex(),**parent.identity(raw),disassembly=dis.replace(str(p),label))
    report=dict(schema_version=1,status='OWNER_ABI_AUDIT_NOT_NATIVE_ACCEPTANCE',candidate=parent.identity(rom),
                source_commit='e24a16fe39e27ae162faf5b78596d1f3df18489d',metadata_candidates=names,symbol_hits=hits,excerpts=slices,
                new_emulator_processes=0,accepted_native_cases_replayed=0,native_bp_earning_accepted=False,release_ready=False)
    (OUT/'owner.json').write_bytes(parent.stable(report))
    keep=['AGENTS.md','scripts/pr16_resume.py','tests/test_pr16_resume.py','content/modernization/pr16_native_supply_resume_20260913.json',
          'content/modernization/p08_remaining_work.json','content/modernization/pr16_bp_chooser_checkpoint.json',
          'content/modernization/pr16_bp_exchange_identity_verified.json','scripts/pr16_bp_exchange_identity_record.py',
          'scripts/pr16_bp_exchange_identity.py','scripts/pr16_bp_win_exchange.py','overlays/save_migration/save_migration.h',
          'scripts/build_battle_core.py','tools/engine/cfru_battle_patchset.py','scripts/guard_private_files.py']
    (OUT/'tracked-snapshot.json').write_bytes(parent.stable({p:(ROOT/p).read_text() for p in keep}))
    print(json.dumps(dict(status=report['status'],symbol_metadata=list(hits),new_emulator_processes=0)))
    return report

if __name__=='__main__':run()
