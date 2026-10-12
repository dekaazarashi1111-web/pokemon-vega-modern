#!/usr/bin/env python3
"""残件実装のための限定text fixture。ROM/native/build入力は配布しない。"""
from __future__ import annotations
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
sys.dont_write_bytecode = True
from pr16_candidate_wiki_inputs import Inputs, ROOT, candidate_bytes, digest, need, stable
from pr16_candidate_wiki_details import details
from pr16_candidate_wiki_catalog import assemble
from pr16_candidate_wiki_mega_quality import normalize
from pr16_candidate_wiki_consumers import enrich
from pr16_wiki_remaining_capture import remote_json


def main() -> None:
    inputs = Inputs(); raw = candidate_bytes(inputs)
    model = enrich(normalize(assemble(details(inputs, raw), inputs)), inputs)
    paths = set(subprocess.check_output(['git','ls-files','--',
        'scripts/pr16_candidate_wiki*.py','scripts/pr16_wiki*.py','scripts/build_pr16_candidate_wiki.py',
        'scripts/pr16_resume.py','tools/engine/cfru_move_effect_lowering.py','tools/engine/cfru_qol_runtime.py',
        'tests/test_pr16_wiki_followup*.py','tests/test_pr16_candidate_wiki*.py',
        'content/modernization/pr16_candidate_wiki*.json','content/modernization/pr16_wiki_remaining_source_inventory.json',
        'content/collection_supply_v1/canonical_model.json','state/source-lock.json',
        'config/battle_core.json','config/active_play_baseline.json',
        'config/stage61_wild_overlay_rate_policy.json','config/modernization_p03_stage74_supply_runtime.json',
        'overlays/collection_supply_v1/*.c','overlays/collection_supply_v1/*.h',
        'overlays/modernization_p03_stage74_supply_runtime/*.c',
        'overlays/qol_production/*.c','overlays/qol_production/*.h',
        'tools/modernization_floette_gift.py'], cwd=ROOT).decode().splitlines())
    files = {'model.json':stable(model)}
    for path in sorted(paths):
        need(Path(path).suffix in {'.py','.json','.c','.h'}, 'fixture非text')
        value=inputs.path(path).read_bytes();value.decode('utf-8');need(b'\0' not in value,'fixture NUL')
        files['local/'+path]=value
    lock=inputs.json('state/source-lock.json')
    for label, repo, path in (
        ('cfru','kapibarasan000/CFRU-JP','src/party_menu.c'),
        ('cfru','kapibarasan000/CFRU-JP','src/build_pokemon.c'),
        ('cfru','kapibarasan000/CFRU-JP','assembly/data/move_tables.s'),
        ('pokefirered','pret/pokefirered','src/pokemon.c')):
        commit=next(row['configured_commit'] for row in lock['sources'] if row['name']==label)
        entry=remote_json(f'https://api.github.com/repos/{repo}/contents/{path}?ref={commit}')
        value=base64.b64decode(entry['content']);value.decode('utf-8');need(b'\0' not in value,'upstream NUL')
        need(hashlib.sha1(b'blob '+str(len(value)).encode()+b'\0'+value).hexdigest()==entry['sha'],'upstream blob SHA不一致')
        files[f'upstream/{label}/{path}']=value
    manifest={'schema_version':1,'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),
        'candidate':model['candidate'],'scope':'TEXT_ONLY_WIKI_IMPLEMENTATION_FIXTURE','new_native_runs':0,'rom_changes':0,
        'files':{name:{'size':len(value),'sha256':digest(value)} for name,value in sorted(files.items())}}
    files['manifest.json']=stable(manifest)
    output=ROOT/'.local/pr16-wiki-remaining-fixture';output.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output/'fixture.zip','w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,value in sorted(files.items()):
            entry=zipfile.ZipInfo(name);entry.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(entry,value)
    print(json.dumps({'status':'PASS_TEXT_FIXTURE','files':len(files),'candidate':model['candidate'],'new_native_runs':0}))

if __name__=='__main__':main()
