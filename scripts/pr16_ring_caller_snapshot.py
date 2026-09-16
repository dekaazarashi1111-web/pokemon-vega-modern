#!/usr/bin/env python3
"""Bound an actual read-only boot trace to the saved caller model.

A sampled register value is not an allocation proof. In particular DMA samples
at instruction boundaries do NOT prove absence of an intervening DMA transfer.
The model's mapping/synchrony inputs remain explicit conditional assumptions.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_ring_caller_compose as compose
import pr16_ring_followup_v2 as s

ENTRY = 0x093789F2
SOURCE = 'tools/mgba_pr16_ring_caller_snapshot.c'
SELF = 'scripts/pr16_ring_caller_snapshot.py'
PRIOR = 'content/modernization/pr16_ring_caller_compose.json'
MAX_HITS, CALL_LIMIT, SEARCH_LIMIT = 8, 4096, 240000000
MAX_TRACE_BYTES = 8_000_000


def strict(raw: bytes):
    s.need(len(raw) <= MAX_TRACE_BYTES and b'\0' not in raw, 'trace byte bound')
    def pairs(items):
        out = {}
        for k, v in items:
            s.need(k not in out, 'duplicate JSON key')
            out[k] = v
        return out
    return [json.loads(line, object_pairs_hook=pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError('JSON constant')))
            for line in raw.decode('utf-8').splitlines() if line.strip()]


def number(value, bits=32):
    return compose.uint(value, bits, 'observed integer')


def instruction(raw_pc, cpsr):
    number(raw_pc); number(cpsr)
    delta = 2 if cpsr & 32 else 4
    s.need(raw_pc >= delta and not raw_pc & 1, 'raw PC alignment/underflow')
    return raw_pc - delta


def model_binding(entry: dict, path: list[dict], exit: dict) -> dict:
    snap = copy.deepcopy(entry['snapshot'])
    for key in ('raw_pc', 'cpsr', 'r0', 'r4'):
        number(entry[key])
    for key in ('raw_pc', 'cpsr', 'sp', 'r0', 'r4', 'minimum_sp', 'saved_lr_word',
                'saved_r4_word', 'record_word_after', 'flag_byte_after', 'counter_after',
                'pending_id_after', 'steps'):
        number(exit[key])
    for key in ('returned', 'cpu_mode_stable', 'memory_control_stable',
                'dma_disabled_at_step_boundaries'):
        s.need(type(exit[key]) is bool, 'observation boolean')
    s.need(entry['cpsr'] & 32 and instruction(entry['raw_pc'], entry['cpsr']) == ENTRY,
           'not original FlagSet entry')
    s.need(entry['r0'] <= 65535 and snap['id'] == entry['r0'], 'FlagSet argument differs')
    s.need(0 < len(path) <= CALL_LIMIT and len(path) == exit['steps'], 'call step count')
    s.need(path[0]['pc'] == ENTRY and path[0]['sp'] == snap['sp']
           and path[0]['cpsr'] == entry['cpsr'], 'entry/path discontinuity')
    for offset, row in enumerate(path):
        s.need(row['offset'] == offset, 'PC trace order')
        for key in ('pc', 'sp', 'cpsr'):
            number(row[key])
    s.need(exit['minimum_sp'] == min([snap['sp'], exit['sp']] + [r['sp'] for r in path]),
           'minimum SP differs')
    modes = all(r['cpsr'] & 31 == entry['cpsr'] & 31 for r in [*path, exit])
    s.need(modes == exit['cpu_mode_stable'], 'CPU mode trace differs')
    # These flags request CONDITIONAL reasoning only. Neither is promoted to
    # a runtime invariant by numeric PC/SP or sampled hardware register data.
    s.need('normal_mapping_stable' not in snap and 'synchronous' not in snap,
           'caller must not inject model assumptions as measurements')
    snap.update(normal_mapping_stable=True, synchronous=True)
    model = compose.check_snapshot(snap)
    s.need(exit['returned'] and exit['cpsr'] & 32
           and instruction(exit['raw_pc'], exit['cpsr']) == snap['lr'] & ~1,
           'actual return not observed')
    s.need(exit['sp'] == snap['sp'] and exit['r4'] == entry['r4'] and exit['r0'] == 0,
           'observed return registers differ')
    s.need(exit['saved_lr_word'] == snap['lr'] and exit['saved_r4_word'] == entry['r4'],
           'observed inherited saved slots differ')
    s.need(exit['minimum_sp'] >= model['frame'][0], 'observed stack exceeds conditional bound')
    expected_word, expected_counter = snap['record_word'], snap['index']
    expected_flag, expected_pending = snap['flag_byte'], None
    record = snap['record_base'] + 4 * snap['index']
    for write in model['writes']:
        address, width, value = write['address'], write['width'], write['value']
        if record <= address < record + 4:
            mask = ((1 << (width * 8)) - 1) << ((address - record) * 8)
            expected_word = (expected_word & ~mask) | (value << ((address - record) * 8))
        elif address == compose.COUNTER:
            expected_counter = value
        elif address == compose.PENDING_ID:
            expected_pending = value
        elif address == model['return_pointer']:
            expected_flag = value
        else:
            raise ValueError('unbound modeled write')
    if model['return_pointer']:
        s.need(entry['flag_readable'] is True and exit['flag_byte_after'] == expected_flag,
               'actual flag byte differs from conditional prediction')
    if model['active_prefix']:
        s.need(entry['record_readable'] is True and exit['record_word_after'] == expected_word,
               'actual record differs from conditional prediction')
    s.need(exit['counter_after'] == expected_counter, 'actual counter differs')
    if expected_pending is not None:
        s.need(exit['pending_id_after'] == expected_pending, 'actual pending ID differs')
    return {'ordinal': entry['ordinal'], 'scope': 'ONE_OBSERVED_BOOT_CALL_NOT_RING_ROUTE',
            'snapshot': entry['snapshot'], 'route': model['route'], 'trace_return_consistent': True, 'runtime_provenance_bound': False,
            'return_target': snap['lr'] & ~1, 'observed_instructions': len(path),
            'observed_minimum_sp': exit['minimum_sp'], 'conditional_frame': model['frame'],
            'conditional_predictions_match_observation': True,
            'conditional_assumptions_not_discharged': ['normal_mapping_stable', 'synchronous'],
            'hardware_samples': {k: entry[k] for k in ('memory_control', 'ime', 'ie', 'dma_enable')},
            'hardware_sample_summary': {k: exit[k] for k in ('cpu_mode_stable',
                'memory_control_stable', 'dma_disabled_at_step_boundaries')},
            'allocated_storage_extent_proven': False, 'synchrony_proven': False,
            'all_callers_resolved': False, 'all_runtime_owners_excluded': False,
            'ring_acquisition_accepted': False, 'release_ready': False}


def validate_trace(raw: bytes) -> dict:
    rows = strict(raw)
    s.need(rows and all(type(r) is dict for r in rows), 'trace rows absent')
    summary = rows[-1]
    s.need(summary['kind'] == 'summary' and summary['search_limit'] == SEARCH_LIMIT,
           'missing bounded summary')
    for key in ('hits', 'search_steps', 'search_limit', 'unobserved_title_frames',
                'host_memory_writes', 'host_register_writes', 'host_function_calls', 'savestate_loads'):
        number(summary[key])
    s.need(summary['hits'] <= MAX_HITS and summary['search_steps'] <= SEARCH_LIMIT
           and summary['unobserved_title_frames'] == 1200, 'search scope differs')
    for key in ('host_memory_writes', 'host_register_writes', 'host_function_calls', 'savestate_loads'):
        s.need(summary[key] == 0, 'host intervention in observation')
    s.need(summary['ring_acquisition_accepted'] is False, 'boot trace cannot accept Ring')
    observations, rejected, entries = [], [], []
    pos, last_start = 0, -1
    while pos < len(rows) - 1:
        entry = rows[pos]; pos += 1; ordinal = len(entries) + 1
        s.need(entry['kind'] == 'entry' and entry['ordinal'] == ordinal, 'entry sequence')
        start = number(entry['step'])
        s.need(last_start < start <= SEARCH_LIMIT, 'search event order');last_start=start
        path=[]
        while pos < len(rows)-1 and rows[pos]['kind']=='pc':
            s.need(rows[pos]['ordinal']==ordinal and len(path)<CALL_LIMIT, 'PC ordinal/budget')
            path.append(rows[pos]);pos+=1
        s.need(pos < len(rows)-1, 'incomplete observed call')
        exit=rows[pos];pos+=1
        s.need(exit['kind']=='exit' and exit['ordinal']==ordinal, 'exit sequence')
        entries.append(entry)
        try:
            observations.append(model_binding(entry,path,exit))
        except (ValueError, KeyError, TypeError) as error:
            rejected.append({'ordinal':ordinal,'reason':str(error),'accepted':False})
    s.need(len(entries)==summary['hits'], 'hit count differs')
    return {'classification':'UNBOUND_TRACE_VALIDATION_NOT_RUNTIME_EVIDENCE',
            'candidate':copy.deepcopy(s.CANDIDATE), 'trace_identity':s.identity(raw),
            'observed_calls':len(entries),'bound_calls':len(observations),
            'bindings':observations,'rejected_calls':rejected,'search':summary,
            'status':'OBSERVED_CALLS_BOUND_CONDITIONALLY' if observations else 'NO_BINDABLE_CALL_OBSERVED',
            'runtime_provenance_bound':False,'new_emulator_processes':0,'fresh_cores':0,'accepted_native_cases_replayed':0,
            'prior_abi_classifications_replayed':0,'rom_changes':0,'candidate_reconstructions':1,
            'allocated_storage_extent_proven':False,'synchrony_proven':False,
            'all_runtime_owners_excluded':False,'ring_acquisition_accepted':False,'release_ready':False}


def source_policy(text: str) -> None:
    for forbidden in ('->writeRegister', '->rawWrite', '->busWrite', '->loadState',
                      '->loadSave', 'call_thumb(', 'call_preserving('):
        s.need(forbidden not in text, 'host-write surface: '+forbidden)
    s.need('c->step(c)' in text and 'c->readRegister(c' in text, 'missing instruction observer')


def capture(out: Path) -> dict:
    rom = s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    before=s.identity(rom.read_bytes())
    s.need(before=={k:s.CANDIDATE[k] for k in ('size','sha256')}, 'candidate identity')
    source_policy((s.ROOT/SOURCE).read_text())
    private=s.ROOT/'.local/pr16-ring-caller-snapshot-private';private.mkdir(parents=True,exist_ok=True)
    binary=private/'observer';save=private/'blank.sav'
    s.need(not save.exists(), 'refuse to replay an already-started capture')
    save.write_bytes(b'\xff'*0x20000)
    subprocess.run(['gcc-13','-O2','-std=c11','-Wall','-Wextra','-Werror',str(s.ROOT/SOURCE),
                    '-lmgba','-o',str(binary)],cwd=s.ROOT,check=True)
    process={'actual_new_processes':1,'fresh_cores_started':1,'timed_out':False}
    started=time.monotonic()
    with (out/'trace.jsonl').open('wb') as stdout,(out/'native.stderr.txt').open('wb') as stderr:
        try:
            p=subprocess.run([str(binary),str(rom),str(save)],stdout=stdout,stderr=stderr,
                             cwd=s.ROOT,timeout=600,check=False)
            process['returncode']=p.returncode
        except subprocess.TimeoutExpired:
            process.update(timed_out=True,returncode=None)
    process['elapsed_seconds']=round(time.monotonic()-started,3)
    process['rom_before']=before;process['rom_after']=s.identity(rom.read_bytes())
    (out/'process.json').write_bytes(s.stable(process))
    s.need(process['rom_after']==before and not process['timed_out'] and process['returncode']==0,
           'native capture failed; preserve trace/process without acceptance')
    result=validate_trace((out/'trace.jsonl').read_bytes())
    result.update(classification='BOUNDED_BOOT_CALLER_OBSERVATION_NOT_RING_ACCEPTANCE',
                  runtime_provenance_bound=True,new_emulator_processes=1,fresh_cores=1)
    for bound in result['bindings']:
        bound.update(runtime_provenance_bound=True,actual_return_observed=True)
    result['observer_identity']=s.identity((s.ROOT/SOURCE).read_bytes())
    result['binary_identity']=s.identity(binary.read_bytes())
    result['process']=process
    result['old_unread_targets']=s.load(PRIOR)['analysis']['old_unread_targets']
    s.need(len(result['old_unread_targets'])==18, 'old owner frontier changed')
    return result
