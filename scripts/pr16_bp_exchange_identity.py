#!/usr/bin/env python3
"""7f32初勝利prefixを延長し、交換から次戦までの個体をread-only照合する。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT)]
import pr16_bp_win_exchange as previous

SELF = 'scripts/pr16_bp_exchange_identity.py'
SOURCE = 'tools/mgba_pr16_bp_exchange_identity.c'
WORKFLOW = '.github/workflows/pr16-bp-exchange-identity.yml'
TEST = 'tests/test_pr16_bp_exchange_identity.py'
OUT = ROOT / '.local/pr16-bp-exchange-identity'
STATUS = 'DIAGNOSTIC_EXCHANGE_IDENTITY_BOUNDARIES_NOT_BP'
CASE = 'exchange-identity-boundaries'
SCOPE = 'PR16_P05_EXCHANGE_IDENTITY_BOUNDARIES'
need, replace_once = previous.need, previous.replace_once


def strict(raw):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            need(key not in out, 'duplicate identity key')
            out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=unique)


def unhex(value, size):
    need(type(value) is str and re.fullmatch('[0-9a-f]{%d}' % (size * 2), value), 'invalid identity bytes')
    return bytes.fromhex(value)


def individual(raw, battle=False):
    def u(offset, size):
        return int.from_bytes(raw[offset:offset + size], 'little')
    return dict(personality=u(0x48 if battle else 0, 4), ot=u(0x54 if battle else 4, 4),
                species=u(0 if battle else 0x20, 2),
                moves=[u((0x0c if battle else 0x2c) + 2 * i, 2) for i in range(4)])


def analyze(stderr, row):
    expected, samples = [], []
    for line in stderr.splitlines():
        if line.startswith(b'BP_IDENTITY_EXPECTED '):
            expected.append(strict(line.split(b' ', 1)[1]))
        elif line.startswith(b'BP_IDENTITY '):
            samples.append(strict(line.split(b' ', 1)[1]))
    need(len(expected) == 1 and 4 <= len(samples) <= 512, 'missing/bounded identity trace')
    e = expected[0]
    need(set(e) == {'frame', 'slot', 'party', 'script_bytes'}, 'expected schema differs')
    need(type(e['frame']) is int and type(e['slot']) is int and e['slot'] == row['exchange_slot'], 'expected slot differs')
    want = unhex(e['party'], 600)
    script = unhex(e['script_bytes'], 40)
    need(script[8] == 0x23 and script[36] == 0x5d, 'pinned PrepareBattle/launch script differs')
    fields = {'label', 'frame', 'script', 'native', 'callback2', 'battle_struct', 'count', 'active_index', 'party', 'battle_mon', 'order'}
    last = e['frame']
    for s in samples:
        need(set(s) == fields, 'sample schema differs')
        need(s['label'] in ('before-confirm', 'transition', 'committed', 'action'), 'unknown identity phase')
        need(all(type(s[k]) is int and 0 <= s[k] <= 0xffffffff for k in fields - {'label', 'party', 'battle_mon', 'order'}), 'integer schema differs')
        need(last <= s['frame'] <= row['total_frames'] and 0 <= s['count'] <= 6, 'identity frame/count differs')
        unhex(s['party'], 600); unhex(s['battle_mon'], 88); unhex(s['order'], 6)
        last = s['frame']
    phases = {label: [s for s in samples if s['label'] == label] for label in ('before-confirm', 'committed', 'action')}
    need(all(len(v) == 1 for v in phases.values()), 'missing/duplicate identity checkpoint')
    begin, committed, action = [phases[k][0] for k in phases]
    need(begin is samples[0] and action is samples[-1], 'identity endpoints differ')
    need(begin['frame'] == e['frame'] == row['exchange_confirm_frame'] - 1, 'identity start differs')
    need(committed['frame'] == row['exchange_commit_frame'] and action['frame'] == row['next_battle_action_frame'], 'identity result frames differ')
    need(committed['party'] == e['party'] and committed['count'] == action['count'] == 3, 'committed exact600 absent')
    need(action['battle_struct'] > 0 and action['active_index'] < 3, 'next battle absent')
    want_ids = [individual(want[i*100:(i+1)*100]) for i in range(3)]
    need(len({json.dumps(v, sort_keys=True) for v in want_ids}) == 3, 'ambiguous expected individuals')
    def describe(s):
        raw = unhex(s['party'], 600)
        ids = [individual(raw[i*100:(i+1)*100]) for i in range(3)]
        return dict(frame=s['frame'], script=s['script'], native=s['native'], callback2=s['callback2'],
                    count=s['count'], party_sha256=hashlib.sha256(raw).hexdigest(),
                    changed_bytes=sum(a != b for a,b in zip(raw,want)), individuals=ids,
                    exchanged_slots=[i for i,v in enumerate(ids) if v == want_ids[e['slot']]])
    after = [s for s in samples if s['frame'] >= committed['frame']]
    changed = [s for s in after if s['party'] != e['party']]
    final = describe(action)
    active = individual(unhex(action['battle_mon'], 88), battle=True)
    need(active == final['individuals'][action['active_index']], 'active battler does not match native party index')
    chooser = [s for s in after if s['callback2'] == 0x0811f3a9]
    need(chooser, 'next chooser boundary absent')
    return dict(schema_version=1, classification='DIAGNOSTIC_ONLY_NOT_ACCEPTANCE',
                candidate_sha256=previous.SHA, snapshot_count=len(samples),
                expected_individuals=want_ids, exchange_slot=e['slot'],
                committed=describe(committed), first_changed=describe(changed[0]) if changed else None,
                next_chooser=describe(chooser[0]), next_action=final, active_battler=active,
                exchanged_individual_retained=len(final['exchanged_slots']) == 1,
                all_three_individuals_retained=all(v in final['individuals'] for v in want_ids),
                exact600_retained=action['party'] == e['party'],
                observation_boundary='READ_ONLY_FRAME_SNAPSHOTS_NOT_CPU_FUNCTION_ENTRY_RETURN',
                native_bp_earning_accepted=False, p05_native_bp_gap_closed=False, release_ready=False)


def assemble_controller():
    text = previous.assemble_controller()
    text = replace_once(text, 'struct BPProgress {', (ROOT / SOURCE).read_text() + '\nstruct BPProgress {')
    text = replace_once(text, 'w.confirm=b_frames+1U;b_press(c,QOL_KEY_A,2U);',
                        'ei_begin(c,expected,w.slot);w.confirm=b_frames+1U;b_press(c,QOL_KEY_A,2U);')
    text = replace_once(text, 'w.replaced=100U;w.preserved=500U;',
                        'ei_sample(c,"committed");w.replaced=100U;w.preserved=500U;')
    text = replace_once(text, 'c->setKeys(c,0U);br_trace(c,"exchange-next-action");',
                        'ei_sample(c,"action");ei_active=false;c->setKeys(c,0U);br_trace(c,"exchange-next-action");')
    for old,new in [(previous.STATUS,STATUS),(previous.CASE,CASE),(previous.SCOPE,SCOPE)]:
        text = replace_once(text, old, new)
    return text


def instrument_driver(text):
    anchor = '            for name,text in generated.items():(work/name).write_text(text)'
    injected = '''            key='pr16_shop_breeding_helpers.c'
            helper=generated[key]
            helper=previous.transform(helper,'static void b_frame(struct mCore *c,unsigned key) {',
                'static void ei_observe(struct mCore *c);\\nstatic void b_frame(struct mCore *c,unsigned key) {')
            helper=previous.transform(helper,'c->setKeys(c,key);c->runFrame(c);++b_frames;',
                'c->setKeys(c,key);c->runFrame(c);++b_frames;ei_observe(c);')
            generated[key]=helper
'''
    return replace_once(text, anchor, injected + anchor)


def validate(raw, stderr, code):
    row = strict(raw)
    need(row.get('status') == STATUS and row.get('case') == CASE and row.get('scope') == SCOPE, 'identity scope differs')
    parent = dict(row, status=previous.STATUS, case=previous.CASE, scope=previous.SCOPE)
    previous.validate(json.dumps(parent).encode(), stderr, code)
    analyze(stderr, row)
    return row


def run():
    # 元runner/既存成果は変更せず、新しいoutputへ同一入力列を1回だけ実行。
    text = (ROOT / previous.SELF).read_text()
    text = replace_once(text, 'paths=[first.OLD_DRIVER,', "paths=['tools/mgba_pr16_bp_win_exchange.c',first.OLD_DRIVER,")
    anchor = "        module=types.ModuleType('pr16_win_exchange_derived');"
    text = replace_once(text, anchor, '        text=instrument_driver(text)\n' + anchor)
    module = types.ModuleType('pr16_identity_derived'); module.__file__ = str(ROOT / previous.SELF)
    exec(compile(text, module.__file__, 'exec'), module.__dict__)
    module.__dict__.update(SELF=SELF, SOURCE=SOURCE, WORKFLOW=WORKFLOW, TEST=TEST,
                          OUT=OUT, STATUS=STATUS, CASE=CASE, SCOPE=SCOPE,
                          assemble_controller=assemble_controller, instrument_driver=instrument_driver, validate=validate)
    report = module.run()
    if report['status'] == STATUS:
        result = analyze((OUT / (CASE + '.stderr')).read_bytes(), report['results'][0]['result'])
        (OUT / 'identity.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        receipt = strict((OUT / 'receipt.json').read_bytes())
        raw = (OUT / 'identity.json').read_bytes()
        receipt['members']['identity.json'] = dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        (OUT / 'receipt.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    return report


if __name__ == '__main__':
    r = run()
    print(json.dumps({k:r[k] for k in ('status','actual_new_processes','successful_fresh_cores','failures')}))
    sys.exit(0 if r['status'] == STATUS else 1)
