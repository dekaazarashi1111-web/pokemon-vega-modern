#!/usr/bin/env python3
"""BP Trial の実ROM script連鎖を有限解読する。受入・ROM修正は行わない。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
BASE = 0x08000000
SHA = 'e630f7f199194fb4b531ff3a561da866902aea200770a832aec5c276e1636267'
OUT = ROOT / '.local/pr16-bp-trial-route'
SELF = 'scripts/pr16_bp_trial_route.py'
WORKFLOW = '.github/workflows/pr16-bp-trial-route.yml'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def stable(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


class GraphError(ValueError):
    def __init__(self, detail):
        super().__init__('script graph rejected at documented command boundary')
        self.detail = detail


def graph(raw, roots):
    """明示rootと命令境界のedgeだけを辿る。native内への推測はしない。"""
    from tools.t02.rom_inventory import COMMAND_LENGTHS
    pending = sorted(set(roots))
    nodes = {}
    while pending:
        start = pending.pop(0)
        if start in nodes:
            continue
        need(len(nodes) < 128, 'script node bound exceeded')
        pc = start
        rows = []
        for _ in range(128):
            at = pc - BASE
            need(0 <= at < len(raw), 'script address outside ROM')
            op = raw[at]
            size = COMMAND_LENGTHS.get(op, 0)
            if not (size > 0 and at + size <= len(raw)):
                raise GraphError(dict(root=start,address=pc,opcode=op,declared_length=size,
                    next_bytes=raw[at:at+24].hex(),partial_node=rows,nodes=list(nodes.values()),
                    error='unknown/truncated instruction; no resynchronization'))
            row = dict(address=pc, opcode=op, bytes=raw[at:at+size].hex())
            if op in (0x04, 0x05, 0x06, 0x07):
                site = at + (1 if op in (0x04, 0x05) else 2)
                target = struct.unpack_from('<I', raw, site)[0]
                need(BASE <= target < BASE + len(raw), 'script edge outside ROM')
                row.update(target=target, operand_address=BASE+site)
                pending.append(target)
            elif op in (0x23, 0x24):
                native = struct.unpack_from('<I', raw, at+1)[0]
                need(native & 1 and BASE <= native < BASE + len(raw), 'native pointer is not ROM Thumb')
                row['native'] = native
            elif op == 0x25:
                row['special'] = struct.unpack_from('<H', raw, at+1)[0]
            rows.append(row)
            if op in (0x02, 0x03, 0x05, 0x0C, 0x0D, 0x24, 0x5E, 0x5F, 0xB9):
                break
            pc += size
        else:
            raise ValueError('script instruction bound exceeded')
        nodes[start] = dict(address=start, instructions=rows)
    return [nodes[k] for k in sorted(nodes)]


def inspect(raw):
    need(identity(raw) == dict(size=33554432, sha256=SHA), 'exact parent ROM required')
    magic = b'VEGAF20\0'
    at = raw.find(magic)
    need(at >= 0 and raw.find(magic, at+1) < 0, 'ambiguous/missing documented VEGAF20 header')
    version, size, code_size, battles, candidates, selected, reward, mon_size = struct.unpack_from('<8I', raw, at+8)
    need(version == 1 and 56 <= code_size < size <= 40000 and at+size <= len(raw), 'invalid facility payload bounds')
    need((battles, candidates, selected, reward, mon_size) == (3, 6, 3, 9, 100), 'facility header contract differs')
    probe, npc, events, scripts = struct.unpack_from('<4I', raw, at+40)
    need(all(BASE+at <= value < BASE+at+size for value in (probe, npc, events, scripts)), 'header pointers leave payload')
    named = dict(payload_npc=npc, pre_high_npc=0x0938D4A4, high_reception=0x093C9390, mistaken_trial=0x092CF790)
    paths, failures = {}, {}
    for name,address in named.items():
        try:
            paths[name] = graph(raw,[address])
        except GraphError as exc:
            failures[name] = exc.detail
    basic = dict(schema_version=1,status='FAIL_ROOTED_STATIC_NOT_NATIVE_ACCEPTANCE',candidate=identity(raw),
        payload=dict(address=BASE+at,size=size,code_size=code_size,header=raw[at:at+56].hex(),npc=npc,probe=probe,events=events,map_scripts=scripts),
        roots=named,graphs=paths,graph_failures=failures,new_emulator_processes=0,rom_changes=0,
        native_rental_accepted=False,p05_native_bp_gap_closed=False,release_ready=False)
    if failures:
        return basic
    edges = [row for node in paths['high_reception'] for row in node['instructions'] if row.get('target') == named['mistaken_trial']]
    need(len(edges) == 1 and edges[0]['opcode'] == 0x06, 'Trial delegate is not one rooted conditional edge')
    rental_paths = [name for name in ('payload_npc', 'pre_high_npc') if any(row.get('special') == 0x2f for node in paths[name] for row in node['instructions'])]
    need(len(rental_paths) == 2, 'rental selection not reachable from both documented predecessors')
    need(not any(row.get('special') == 0x2f for node in paths['mistaken_trial'] for row in node['instructions']), 'mistaken completion unexpectedly contains rental UI')
    cfg = json.loads((ROOT/'config/factory_high_modes_v2.json').read_bytes())
    reception = next(row for row in cfg['hooks'] if row['name'] == 'factory_reception_script')
    completion = next(row for row in cfg['hooks'] if row['name'] == 'factory_trial_completion_chain')
    need(int(cfg['physical_binding']['trial_script'],16) == named['mistaken_trial'], 'historical configured Trial differs')
    need(int.from_bytes(bytes.fromhex(reception['expected_hex']), 'little') == named['pre_high_npc'], 'historical predecessor differs')
    need(int(completion['address'],16) == named['mistaken_trial']+1, 'completion pointer contract differs')
    basic.update(status='PASS_ROOTED_STATIC_NOT_NATIVE_ACCEPTANCE',trial_operand=edges[0],
        replacement_candidate=named['pre_high_npc'],replacement_candidate_is_previous_physical_hook=True,
        limitations=['静的到達性だけ。native受付、レンタル、勝敗、報酬、Save/Continueは別の実行証拠が必要。',
                    'native function内部と高モードの全状態は今回のscript graph受入に含めない。'])
    return basic


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    need(not OUT.is_symlink(), 'unsafe output')
    head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    names = [SELF, WORKFLOW,
        'AGENTS.md','README.md','design/current_state.md','design/agent_context_map.md','design/tasks_next.md',
        'scripts/build_factory_high_modes_v2.py','scripts/build_facility_runtime.py',
        'scripts/pr16_bp_native_controls.py','tests/test_pr16_bp_native_controls.py','tools/mgba_pr16_bp_native_controls.c',
        'config/factory_high_modes_v2.json','overlays/factory_high_modes_v2/factory_high_modes_v2.c',
        'overlays/facility_runtime/facility_runtime.c','overlays/factory_high_modes_v2/factory_high_modes_v2.h',
        'content/modernization/p08_remaining_work.json','content/modernization/pr16_native_supply_handoff.json',
        'scripts/pr16_bp_native_controls_evidence.py','scripts/pr16_fixed_form_closeout.py',
        'tools/t02/rom_inventory.py','config/active_play_baseline.json']
    tracked = set(subprocess.check_output(['git','ls-files','-z'],cwd=ROOT,text=True).split('\0'))
    bound = {}
    with zipfile.ZipFile(OUT/'sources.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in names:
            if name not in tracked:
                continue
            path=ROOT/name; data=path.read_bytes(); data.decode('utf-8')
            need(not path.is_symlink() and b'\0' not in data and len(data)<8_000_000, 'unsafe source snapshot')
            z.writestr(name,data);bound[name]=identity(data)
    report = dict(schema_version=1,status='FAIL',tested_head=head,sources=bound,
        new_emulator_processes=0,rom_changes=0,native_rental_accepted=False,p05_native_bp_gap_closed=False,release_ready=False)
    try:
        import pr16_shop_display_repair as repair
        recipe = repair.run()
        (OUT/'candidate-recipe.json').write_bytes(stable(recipe))
        raw = (repair.OUTPUT/'candidate.gba').read_bytes()
        report.update(inspect(raw))
        need(report['status']=='PASS_ROOTED_STATIC_NOT_NATIVE_ACCEPTANCE','bounded script graph rejected; see route.json')
        print(json.dumps(dict(status=report['status'],tested_head=head,trial_operand=report['trial_operand'],replacement_candidate=report['replacement_candidate'],new_emulator_processes=0)))
    finally:
        (OUT/'route.json').write_bytes(stable(report))
        (OUT/'receipt.json').write_bytes(stable({p.name:identity(p.read_bytes()) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='receipt.json'}))

if __name__ == '__main__':
    main()
