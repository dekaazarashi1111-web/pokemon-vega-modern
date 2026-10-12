#!/usr/bin/env python3
"""固定ELFを現候補へbyte照合し、新Circus接続を実ownerへlinkする。入場受入ではない。"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import struct
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
OUT = ROOT/'.local/pr16-circus-link'
SELF = 'scripts/pr16_circus_link_probe.py'
PARENT = {'size': 33554432, 'sha256': '4ea33fb8224b0b84493ccca6e90161da245705eb1eb0a3874691ab39cc3806cc'}
BASE = 0x08000000
OWNERS = ('cfru_integration_pending_copy', 'cfru_integration_pending_facility_set')
WANTED = {*OWNERS, 'cfru_integration_pending_clear', 'VegaFacilityStateGet', 'VegaFacilityStateSet',
    'VegaFacilityStateIsActive', 'VegaConfigureNextFacility', 'VegaBattlePolicyPrepareFacilityBattle',
    'BattleSetup_StartTrainerBattle', 'sp072_LoadBattleCircusEffects', 'GetCurrentBattleTowerStreak',
    'GetBattleTowerStreak', 'SetSav1Weather', 'gBattleCircusFlags', 'gBattleCircusStreaks', 'gBitTable',
    'sBattleCircusEffectDescriptions', 'gSpecialVar_LastResult', 'gSpecialVar_Result', 'gStringVarC',
    'gSpecials', 'gScriptCmdTable', 'ScrCmd_special', 'ScrCmd_callnative'}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(data):
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def stable(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()


def symbols(text):
    result = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) not in (3, 4) or not re.fullmatch('[0-9a-fA-F]{8}', parts[0]):
            continue
        address = int(parts[0], 16)
        size = int(parts[1], 16) if len(parts) == 4 else None
        kind, name = parts[-2:]
        need(name not in result or name.startswith('$'), 'duplicate named ELF symbol: '+name)
        if name.startswith('$'):
            continue
        result[name] = dict(address=address, size=size, kind=kind)
    return result


def elf_span(raw, address, size):
    """ELF32 little-endian sectionのみ。NOBITS、重複、overflowは拒否。"""
    need(raw[:7] == b'\x7fELF\x01\x01\x01' and len(raw) >= 52, 'not ELF32 little endian')
    need(struct.unpack_from('<H', raw, 18)[0] == 40, 'not ARM ELF')
    offset = struct.unpack_from('<I', raw, 32)[0]
    stride, count = struct.unpack_from('<HH', raw, 46)
    need(stride == 40 and 0 < count <= 4096 and 0 <= offset <= len(raw)-stride*count, 'invalid section table')
    need(type(address) is int and type(size) is int and 0 < size <= 65536, 'invalid bounded symbol span')
    matches = []
    for index in range(count):
        _, kind, flags, start, at, length, *_ = struct.unpack_from('<10I', raw, offset+index*stride)
        if kind == 8 or not flags & 2 or not start <= address or address+size > start+length:
            continue
        need(at <= len(raw)-length, 'truncated allocated section')
        matches.append(raw[at+address-start:at+address-start+size])
    need(len(matches) == 1 and len(matches[0]) == size, 'ambiguous or unmapped ELF span')
    return matches[0]


REQUIRED_FUNCTIONS = (*OWNERS, 'VegaConfigureNextFacility', 'VegaFacilityStateGet',
    'VegaFacilityStateSet', 'BattleSetup_StartTrainerBattle', 'sp072_LoadBattleCircusEffects')


def matching_functions(elf_raw, rows, candidate):
    """名前一致では採用しない。利用する7関数の全バイトと絶対位置を照合する。"""
    matches = {}
    for name in REQUIRED_FUNCTIONS:
        row = rows.get(name, {})
        address, size = row.get('address', 0) & ~1, row.get('size')
        if not size or row.get('kind') != 'T' or not BASE <= address < BASE+len(candidate):
            return None
        data = elf_span(elf_raw, address, size)
        if data != candidate[address-BASE:address-BASE+size]:
            return None
        matches[name] = dict(address=address, size=size, sha256=identity(data)['sha256'])
    return matches


def cached_elf(archive, candidate):
    cfg = json.loads((ROOT/'config/github_private_environment.json').read_bytes())
    bound = next(a for a in cfg['archives'] if a['name'] == 'pokemon-vega-private-env-v1-build-cache.zip')
    need(identity(archive.read_bytes()) == {k:bound[k] for k in ('size', 'sha256')}, 'fixed build archive differs')
    chosen, index = [], []
    with zipfile.ZipFile(archive) as z:
        names = z.namelist();need(len(names) == len(set(names)), 'duplicate archive member')
        for info in z.infolist():
            name = info.filename
            if not name.startswith('build/battle-core/') or not name.endswith('/linked.o'):
                continue
            p = PurePosixPath(name)
            need('..' not in p.parts and '\\' not in name and not p.is_absolute(), 'unsafe ELF path')
            need(info.file_size <= 32_000_000, 'ELF bound exceeded')
            raw = z.read(info)
            path = OUT/('cached-'+str(len(index))+'.elf');path.write_bytes(raw)
            listing = subprocess.check_output(['arm-none-eabi-nm', '-g', '-S', '-n', str(path)], text=True)
            rows = symbols(listing)
            match = matching_functions(raw, rows, candidate)
            index.append(dict(path=name, elf=identity(raw), matching_functions=match))
            if match is not None:
                chosen.append((path, raw, rows, name, match))
            else:
                path.unlink()
    (OUT/'cache-index.json').write_bytes(stable(index))
    need(chosen, 'no fixed linked.o matches all actual Circus owner function bytes')
    # 同一buildのrun-1/run-2等は、照合対象が全て同一の場合だけ同値として扱う。
    fingerprints = {stable(row[4]) for row in chosen}
    need(len(fingerprints) == 1, 'ambiguous current owner functions in fixed linked objects')
    path, raw, rows, name, match = sorted(chosen, key=lambda item:item[3])[0]
    binding = dict(archive={k:bound[k] for k in ('name','size','sha256')}, member=name,
        elf=identity(raw), verified_functions=match,
        equivalent_members=[item[3] for item in chosen], whole_cache_revision_claimed=False)
    return path, raw, rows, binding


def rooted_routes(raw, rows):
    from tools.t02.rom_inventory import RomImage
    from tools.stage57_debug_suite import _collect_contactable_roots
    from scripts.pr16_receiver_audit import ReceiverWalker
    from scripts.pr16_bp_trial_route import graph, GraphError
    rom = RomImage('Circus current scoped candidate', raw)
    roots, counts = _collect_contactable_roots(rom)
    walker = ReceiverWalker(rom);invalid = []
    for root in roots:
        if rom.contains(root.address):
            walker.add_root(root)
        else:
            invalid.append(dict(address=root.address, label=root.label, kind=root.kind))
    walked = walker.walk()
    targets = {r['address'] & ~1: name for name, r in rows.items() if name in WANTED}
    selected = []
    for ref in walked['references']:
        category, value = ref['category'], ref['value']
        if (category == 'native' and value & ~1 in targets or
            category == 'special' and value == 0x72 or
            category == 'var' and value == 0x403A):
            selected.append(ref)
    labels = {label for ref in selected for label in ref['roots']}
    paths = {}
    for root in roots:
        if root.label not in labels or not rom.contains(root.address):
            continue
        try:
            paths[root.label] = dict(address=root.address, graph=graph(raw, [root.address]))
        except (ValueError, GraphError) as exc:
            paths[root.label] = dict(address=root.address, error=str(exc), detail=getattr(exc, 'detail', None))
    return dict(root_counts=dict(counts), decoded_roots=walked['root_count'], selected_references=selected,
        rooted_paths=paths, invalid_roots=invalid, diagnostics=walked['diagnostics'], no_match_proves_absence=False,
        native_indirect_callers_fully_excluded=False, physical_entrance_accepted=False)


def link_new(owners):
    source = ROOT/'overlays/circus_admission/circus_admission.c'
    binaries = []
    for attempt in (1, 2):
        folder = OUT/('link-'+str(attempt));folder.mkdir(parents=True, exist_ok=True)
        linker = folder/'circus.ld'
        linker.write_text('ENTRY(VegaCircusAdmissionSelectPending)\nSECTIONS { . = 0x09FFF000; '
            '.text : { KEEP(*(.text.VegaCircusAdmissionSelectPending)) *(.text*) *(.rodata*) } '
            '/DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) } }\n')
        elf = folder/'circus.elf'
        command = ['arm-none-eabi-gcc','-std=c11','-Os','-mthumb','-mcpu=arm7tdmi','-ffreestanding',
            '-fno-builtin','-ffunction-sections','-fdata-sections','-fno-unwind-tables',
            '-fno-asynchronous-unwind-tables','-Wall','-Wextra','-Werror','-nostdlib',
            '-Wl,--gc-sections','-Wl,--build-id=none',
            *['-Wl,--defsym,'+name+'='+hex(address|1) for name,address in sorted(owners.items())],
            '-T',str(linker),str(source),'-o',str(elf)]
        proc = subprocess.run(command,capture_output=True)
        (folder/'compile.stdout').write_bytes(proc.stdout);(folder/'compile.stderr').write_bytes(proc.stderr)
        need(proc.returncode == 0, 'Circus owner link failed')
        need(subprocess.check_output(['arm-none-eabi-nm','-u',str(elf)]) == b'', 'unresolved owner')
        binary = folder/'circus.bin'
        subprocess.run(['arm-none-eabi-objcopy','-O','binary',str(elf),str(binary)],check=True)
        payload = binary.read_bytes();need(32 <= len(payload) <= 1024, 'new runtime size outside bound')
        binaries.append(payload)
        dis = subprocess.check_output(['arm-none-eabi-objdump','-d',str(elf)],text=True)
        (folder/'disassembly.txt').write_text(dis.replace(str(elf),'circus.elf'))
        listing = subprocess.check_output(['arm-none-eabi-nm','-S','-n',str(elf)],text=True)
        (folder/'symbols.json').write_bytes(stable(symbols(listing)))
    need(binaries[0] == binaries[1], 'independent linked ARM output differs')
    return dict(payload=identity(binaries[0]), independent_links=2,
        placement_is_link_test_only=True, no_rom_payload_inserted=True, owners=owners)


def run(archive, candidate):
    OUT.mkdir(parents=True,exist_ok=True)
    need(not any(p.is_symlink() for p in (archive, candidate, OUT, *OUT.parents)), 'symlink input/output')
    raw = candidate.read_bytes();need(identity(raw) == PARENT, 'accepted scoped candidate differs')
    head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    need(head == os.environ['GITHUB_SHA'], 'fixed checkout differs')
    elf, elf_raw, rows, binding = cached_elf(archive, raw)
    (OUT/'symbols.json').write_bytes(stable(rows))
    wanted = {}
    for name in sorted(WANTED & set(rows)):
        row = dict(rows[name]);address, size = row['address'] & ~1, row['size']
        if size and BASE <= address < BASE+len(raw):
            old = elf_span(elf_raw,address,size)
            now = raw[address-BASE:address-BASE+size]
            row.update(elf_bytes=identity(old), candidate_bytes=identity(now), matches_candidate=old == now)
            if name in OWNERS:
                need(old == now, 'actual pending owner bytes differ: '+name)
            dis = subprocess.check_output(['arm-none-eabi-objdump','-d','--start-address='+hex(address),
                '--stop-address='+hex(address+size),str(elf)],text=True)
            (OUT/(name+'.txt')).write_text(dis.replace(str(elf),'fixed-cfru.elf'))
        wanted[name] = row
    need(all(wanted[name].get('matches_candidate') is True for name in OWNERS), 'actual pending owner unverified')
    linked = link_new({name:rows[name]['address'] for name in OWNERS})
    routes = rooted_routes(raw,rows)
    report = dict(schema_version=1, task='USER-20260918-CIRCUS',
        classification='CIRCUS_OWNER_LINKED_NOT_PHYSICAL_ACCEPTANCE', source_head=head,
        run_id=int(os.environ['GITHUB_RUN_ID']), candidate=PARENT, fixed_build=binding,
        symbols=wanted, missing_symbols=sorted(WANTED-set(rows)), new_runtime=linked, routes=routes,
        source_bindings={name:identity((ROOT/name).read_bytes()) for name in (SELF,
            'overlays/circus_admission/circus_admission.c','overlays/circus_admission/circus_admission.h',
            'tests/test_pr16_circus_link_probe.py','.github/workflows/pr16-circus-link.yml')},
        new_emulator_processes=0, accepted_native_cases_replayed=0, rom_changes=0,
        physical_admission_accepted=False, release_ready=False)
    (OUT/'report.json').write_bytes(stable(report))
    print(json.dumps(dict(classification=report['classification'], runtime=linked,
        selected_rooted_references=len(routes['selected_references']), missing_symbols=report['missing_symbols'])))
    need(identity(candidate.read_bytes()) == PARENT, 'candidate changed by link test')
    subprocess.run(['git','diff','--exit-code'],cwd=ROOT,check=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    args=parser.parse_args();run(args.archive,args.candidate)
