#!/usr/bin/env python3
"""Reconcile one preserved native loss without replay or modifying its FAIL record."""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT)]
import pr16_bp_loss_return_native as native
import pr16_bp_loss_return_successor as successor

RUN = 34759726061
JOB = 103730310536
HEAD = 'dfe293f57b009e04274c5eb67dbb9c4e6cae74ec'
ARTIFACT = 10318786656
ARCHIVE = {'size': 802691, 'sha256': 'a740d3bfca7c84f8a933f85e30243c3883f40a760dfe73f9554a95ca2b35642d'}
CANDIDATE = {'size': 33554432, 'sha256': 'fcda15075a586d59f4f9da5f7f55a294765f826ab1453a576e74192df822d879'}
CRC = 'A15FAF9D'
SELF = 'scripts/pr16_bp_loss_return_evidence.py'
OLD_CHECK = "    need(0x08000000<=row['final_script_pointer']<0x0A000000 and 0x08000000<row['final_callback2']<0x0A000000,'return callback/script invalid')"
need, identity, stable = successor.need, successor.identity, successor.stable


def terminal_loss(row, stderr):
    """A terminated loss script is valid only with the full native transition chain."""
    need(row['battle_outcome'] == 2 and row['final_script_pointer'] == 0
         and row['final_callback2'] == 0x08055E75, 'loss must terminate in the exact idle field callback')
    dispatch = native.require_loss_witness(row, stderr)
    traces = []
    for line in stderr.splitlines():
        if not line.startswith(b'BP_RETURN '):
            continue
        fields = dict(re.findall(rb'([a-z0-9_]+)=([^ ]+)', line))
        required = (b'label', b'frame', b'cb2', b'script', b'outcome', b'marker', b'snapshot', b'count', b'bp', b'save')
        need(all(k in fields for k in required), 'incomplete native transition')
        t = {k.decode(): int(fields[k], 16 if k in (b'cb2',b'script') else 10) for k in required[1:]}
        t['label'] = fields[b'label'].decode()
        traces.append(t)
    need(traces and all(a['frame'] <= b['frame'] for a,b in zip(traces,traces[1:])), 'unordered transition frames')
    stop = [t for t in traces if t['label'] == 'facility-stop']
    need(len(stop) == 1 and stop[0]['frame'] == row['facility_return_frame']
         and stop[0]['cb2'] == row['final_callback2'] and stop[0]['script'] == 0
         and (stop[0]['marker'],stop[0]['snapshot'],stop[0]['count'],stop[0]['bp'],stop[0]['save']) == (0,0,1,0,2),
         'terminal trace does not prove restored original party/ledger')
    active = [t for t in traces if t['frame'] == dispatch and t['cb2'] == successor.ENTRY
              and t['script'] == 0x092CF669 and (t['marker'],t['snapshot'],t['count']) == (2,1,3)]
    after_call = [t for t in traces if dispatch < t['frame'] < stop[0]['frame']
                  and t['script'] == 0x092CF66E and t['cb2'] == 0x08055E75
                  and (t['marker'],t['snapshot'],t['count']) == (2,1,3)]
    restored = [t for t in traces if after_call and after_call[0]['frame'] < t['frame'] < stop[0]['frame']
                and t['cb2'] == 0x08055E75 and t['script'] != 0
                and (t['marker'],t['snapshot'],t['count']) == (0,0,1)]
    need(len(active) == 1 and len(after_call) == 1 and restored, 'AfterBattle continuation and restoration chain absent')
    need(all((t['outcome'],t['bp'],t['save']) == (2,0,2) for t in traces if t['frame'] >= dispatch), 'post-loss outcome/BP/save changed')
    return {'dispatch_frame': dispatch, 'afterbattle_script_advanced_frame': after_call[0]['frame'],
            'restored_frame': restored[0]['frame'], 'idle_frame': stop[0]['frame']}


def validate_native(raw, stderr, code):
    """Replace just the erroneous terminal pointer assertion; all old checks remain."""
    import pr16_bp_selection_native as launch
    import pr16_bp_battle_progress as first
    old = first.checked_text(ROOT/native.OLD, native.OLD_SHA)
    validation = old.split('def validate(raw,stderr,code):\n',1)[1].split('\n\ndef run():',1)[0]
    validation = first.replace_once(validation, OLD_CHECK, '    terminal_loss(row,stderr)')
    module = native.derived_driver()
    module.__dict__['terminal_loss'] = terminal_loss
    exec(compile('def validate(raw,stderr,code):\n'+validation, SELF, 'exec'), module.__dict__)
    before = launch.SHA
    try:
        launch.SHA = CANDIDATE['sha256']
        return module.validate(raw, stderr, code)
    finally:
        launch.SHA = before


def zip_members(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        need(len(names) == len(set(names)) and len(names) <= 200, 'duplicate/excessive archive members')
        need(all(not n.startswith('/') and '..' not in Path(n).parts for n in names), 'unsafe archive path')
        return {n: z.read(n) for n in names}


def verify_archive(raw, root=ROOT):
    need(identity(raw) == ARCHIVE, 'native archive identity differs')
    members = zip_members(raw)
    prefix = 'pr16-bp-loss-return-native/'
    control = 'pr16-bp-loss-return-run/'
    index = json.loads(members[control+'members.json'])
    names = {prefix+k[7:] if k.startswith('native/') else control+k for k in index}
    need(names | {control+'members.json'} == set(members), 'outer archive member inventory differs')
    for k,meta in index.items():
        name = prefix+k[7:] if k.startswith('native/') else control+k
        need(identity(members[name]) == meta, 'outer artifact member changed: '+name)
    receipt = json.loads(members[prefix+'receipt.json'])
    need(receipt['tested_head'] == HEAD and receipt['status'] == 'FAIL', 'original failure receipt changed')
    for name,meta in receipt['members'].items():
        need(identity(members[prefix+name]) == meta, 'receipt member changed')
    old = json.loads(members[prefix+'result.json'])
    need(old['status'] == 'FAIL' and old['actual_new_processes'] == 1 and old['successful_fresh_cores'] == 0
         and old['failures'] == [{'stage':'setup-or-execution','error':'return callback/script invalid'}], 'original failure classification differs')
    need(old['candidate'] == CANDIDATE, 'native candidate differs')
    sources = zip_members(members[prefix+'sources.zip'])
    need(set(sources) == set(old['sources']), 'source inventory differs')
    for name,data in sources.items():
        need(identity(data) == old['sources'][name] and (root/name).read_bytes() == data, 'source not the executed bytes: '+name)
    generated = zip_members(members[prefix+'generated-controller.zip'])
    need(set(generated) == set(old['generated']), 'generated inventory differs')
    for name,data in generated.items():
        need(identity(data) == old['generated'][name], 'generated source changed')
    need(generated['controller.c'] == native.derived_driver().assemble_controller().encode(), 'controller derivation changed')
    for guard in ('bus8','bus16','bus32','raw8','raw16','raw32','register'):
        process = json.loads(members[prefix+'guard-'+guard+'.process.json'])
        need(process == dict(schema_version=1,returncode=1,timed_out=False,spawn_error=None), 'host-write barrier process differs')
        need(members[prefix+'guard-'+guard+'.stdout'] == b''
             and members[prefix+'guard-'+guard+'.stderr'] == b'P03 archive: host write after observation barrier\n', 'host-write barrier did not reject')
    process = json.loads(members[prefix+native.CASE+'.process.json'])
    need(process == dict(schema_version=1,returncode=0,timed_out=False,spawn_error=None), 'native process failed')
    row = validate_native(members[prefix+native.CASE+'.stdout'],members[prefix+native.CASE+'.stderr'],process['returncode'])
    witness = terminal_loss(row,members[prefix+native.CASE+'.stderr'])
    recipe = json.loads(members[control+'successor-candidate.json'])
    need(recipe['candidate'] == CANDIDATE and recipe['crc32'] == CRC
         and recipe['parent']['sha256'] == successor.PARENT_SHA and recipe['runtime']['size'] == 180
         and recipe['change'] == dict(offset=successor.OFFSET,before='655f0508',after='8146ff09',size=4)
         and recipe['undeclared_changed_bytes'] == recipe['original_allocations_changed'] == 0
         and recipe['independent_native_compiles'] == recipe['independent_bounded_builds'] == 2, 'successor recipe differs')
    return dict(schema_version=1,classification='DIAGNOSTIC_ONLY_NOT_ACCEPTANCE',
        scope='NATIVE_LOSS_RETURN_ACCEPTED_ONLY_NOT_FORMAL_BP',run_id=RUN,job_id=JOB,tested_head=HEAD,
        original_actions_conclusion='failure',original_python_status='FAIL',original_failure_preserved=True,
        native_process_returncode=0,native_result=row,native_loss_return_accepted=True,
        revalidation_status=native.STATUS,revalidation_requires_no_emulator=True,
        new_emulator_processes=0,original_native_processes=1,original_native_fresh_cores=1,
        successful_cores_in_original_receipt=0,raw_native_success_validated_without_rerun=True,
        witness=witness,candidate=CANDIDATE,crc32=CRC,successor_recipe=recipe,
        source_count=len(sources),generated_count=len(generated),artifact_member_count=len(members),
        artifact_id=ARTIFACT,archive=ARCHIVE,original_members=index,
        original_sources=old['sources'],original_generated=old['generated'],
        accepted_cancel_replayed=False,old_native_failure_relabelled=False,
        native_bp_earning_accepted=False,p05_native_bp_gap_closed=False,release_ready=False)
