"""正規Save30からの抑制観測契約。受入済み30勝の再判定やROM生成はしない。"""
from __future__ import annotations
import hashlib
import json
import struct
from pathlib import Path

SHA = '2b107e7ef897844eff810ff0b40f82543640488696e8295194ceb3b66fb2c183'
CASE = 'circus-suppression-save'
MASK = 0x80000000
TYPE = 0x04000000
PREFIX_CASE = 'circus-continuous-30-save'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def strict(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    def bad(_):
        raise ValueError('nonfinite JSON')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)


def rows(raw, prefix):
    return [strict(line[len(prefix):]) for line in raw.splitlines() if line.startswith(prefix)]


def adapt(files):
    """固定生成Cの入口名・host上限だけを変更。旧ARM/builderは呼ばない。"""
    out = dict(files)
    changes = {
        'controller.c': [('int main(int argc,char **argv){', 'int ss_prefix_main(int argc,char **argv){'),
                         ('sc_events++<160U', 'sc_events++<800U')],
        'pr16_shop_breeding_helpers.c': [('b_frames<=600000U', 'b_frames<=4000000U')],
    }
    for name, replacements in changes.items():
        text = out[name].decode('utf-8')
        for old, new in replacements:
            need(text.count(old) == 1, 'source boundary: ' + name + ' / ' + old)
            text = text.replace(old, new)
        out[name] = text.encode()
    out['controller.c'] += b'\n#include "mgba_pr16_circus_suppression.h"\n'
    return out


def prefix_proof(old_stdout, old_stderr, new_stdout, new_stderr):
    need(new_stderr.startswith(old_stderr), 'accepted 143-event byte prefix changed')
    lines = new_stdout.splitlines()
    need(lines and lines[0] + b'\n' == old_stdout, 'accepted prefix result changed')
    events = rows(old_stderr, b'CIRCUS_CONTINUOUS ')
    need(len(events) == 143 and events[-1]['label'] == 'reloaded'
         and events[-1]['battle'] == 30 and events[-1]['bp'] == 90
         and events[-1]['save_counter'] == 3, 'normal Save30 evidence missing')
    return dict(exact_event_count=143, byte_prefix=identity(old_stderr),
                accepted_standalone_replays=0, continuation_prefix_wins=30,
                reason_ja='旧artifactはSRAMを保持していないため、未完抑制への継続prefixとして一度だけ真正Save30を確保。')


def routes(rom, config):
    need(identity(rom) == dict(size=33554432, sha256=SHA), 'candidate identity')
    result = []
    for row in config['parent_abi']['hooks']:
        root, width = int(row['address'], 16), row['width']
        need(width in (8, 12), 'hook width')
        offset = root - 0x08000000
        stub = rom[offset:offset + width]
        target = struct.unpack_from('<I', stub, width - 4)[0]
        need(target & 1 and 0x08000000 <= target < 0x0a000000, 'Thumb dispatcher')
        normal, suppressed = int(row['normal_address'], 16), int(row['suppressed_address'], 16)
        start = (target & ~1) - 0x08000000
        code = rom[start:start + 64]
        for address in (0x02022AAC, 0x0203DFBC, normal, suppressed):
            need(struct.pack('<I', address) in code, 'dispatcher literal: ' + row['name'])
        result.append(dict(name=row['name'], root=root, target=target & ~1,
                           normal=normal & ~1, suppressed=suppressed & ~1,
                           preserve_r3=width == 12, stub=identity(stub), dispatcher=identity(code)))
    need(len(result) == 29 and len({x['root'] for x in result}) == 29, '29 unique dispatchers')
    return result


def route_header(values):
    return ('static const struct SSRoute ss_routes[]={\n' + ''.join(
        '{"%s",0x%08xU,0x%08xU,0x%08xU,0x%08xU,%uU},\n' %
        (r['name'], r['root'], r['target'], r['normal'], r['suppressed'], r['preserve_r3'])
        for r in values) + '};\n').encode()


def validate_draws(values):
    need(1 <= len(values) <= 64, 'draw count')
    for number, row in enumerate(values):
        need(row['attempt'] == number and row['delay'] == number * 17, 'ordinary input sweep order')
        need(row['current'] == row['best'] == 30 and row['bp'] == 90 and row['counter'] == 3,
             'draw did not inherit real Save30')
        need(row['types'] & TYPE and row['flags'] and row['newbs'], 'actual battle absent')
        need(row['target'] is bool(row['flags'] & MASK), 'suppression predicate differs')
        if number < len(values) - 1:
            need(row['target'] is False, 'accepted draw replayed')
    return values[-1]['target']


def validate_calls(values):
    predicates, delegates = [], []
    for row in values:
        need(row['flags'] & MASK and row['types'] & TYPE, 'call outside actual suppression')
        need(row['host_writes'] == 0 and row['host_calls'] == 0, 'injected call')
        chain = row['pcs']
        need(type(chain) is list and 2 <= len(chain) <= 128
             and all(type(pc) is int and 0x08000000 <= pc < 0x0a000000 for pc in chain), 'PC chain')
        if row['kind'] == 'predicate':
            need(chain[0] == 0x090D7BB0 and chain[-1] == row['return_pc']
                 and row['bank'] in (0, 1) and row['raw_ability'] > 0
                 and row['result'] == 1, 'natural IsAbilitySuppressed return')
            predicates.append(row)
        elif row['kind'] == 'dispatch':
            need(chain[0] == row['root'] and chain[-1] == row['delegate']
                 and row['delegate'] == row['expected_suppressed'], 'wrong Stage77 delegate')
            need(not row['preserve_r3'] or row['r3_before'] == row['r3_after'], 'fourth argument corrupted')
            delegates.append(row)
        else:
            raise ValueError('unknown call kind')
    return dict(predicate_returns=len(predicates), suppressed_dispatches=len(delegates),
                hook_names=sorted({r['name'] for r in delegates}),
                observed=bool(predicates and delegates))


def validate_lifecycle(raw, stderr, code):
    need(code == 0 and b'mGBA[' not in stderr, 'native process or logger failed')
    result = strict(raw.splitlines()[-1])
    exact = dict(schema_version=1, case=CASE, candidate_sha256=SHA,
                 status='PASS_CIRCUS_SUPPRESSION_LIFECYCLE', save_counter_before=3,
                 save_counter_after=4, owner_bytes_verified=64, party_bytes_verified=600,
                 host_write_barriers=7, input_only_after_guard=True,
                 physical_admission_accepted=False, suppression_accepted=False,
                 release_ready=False, warnings_errors=0)
    for key, expected in exact.items():
        need(type(result.get(key)) is type(expected) and result[key] == expected, 'result ' + key)
    draws = rows(stderr, b'CIRCUS_SUPPRESSION_DRAW ')
    need(validate_draws(draws), 'suppression draw not observed')
    calls = validate_calls(rows(stderr, b'CIRCUS_SUPPRESSION_CALL '))
    need(calls['observed'], 'natural suppression trace remains open')
    from pr16_circus_continuous_probe import owner
    events = rows(stderr, b'CIRCUS_CONTINUOUS ')
    starts = [i for i, e in enumerate(events) if e['label'] == 'resume30']
    need(len(starts) == len(draws), 'missing genuine Continue attempt')
    tail = events[starts[-1]:]
    need([e['label'] for e in tail[-3:]] == ['returned', 'saved', 'reloaded'], 'terminal lifecycle')
    before, returned, saved, loaded = tail[0], *tail[-3:]
    baseline = owner(bytes.fromhex(before['owner']))
    need(baseline['current'] == baseline['best'] == 30 and baseline['phase'] == 0, 'Save30 owner')
    need(before['bp'] == 90 and before['save_counter'] == 3 and before['count'] == 1, 'Save30 counters')
    actions = [e for e in tail if e['label'] == 'action']
    outcomes = [e for e in tail if e['label'] == 'outcome']
    need(1 <= len(actions) == len(outcomes) <= 3 and actions[0]['flags'] & MASK, 'suppressed battle lifecycle')
    wins = sum(e['outcome'] == 1 for e in outcomes)
    losses = sum(e['outcome'] == 2 for e in outcomes)
    need(wins + losses == len(outcomes) and losses <= 1
         and (losses or wins == 3), 'native outcomes')
    need(all(e['battle'] == 30 + i for i, e in enumerate(actions)), 'new battle ordering')
    expected_bp = 90 + 9 * (wins // 3)
    for e in (returned, saved, loaded):
        own = owner(bytes.fromhex(e['owner']))
        need(own['current'] == (0 if losses else 30 + wins) and own['best'] == 30 + wins
             and own['phase'] == 0 and own['identity'] == baseline['identity'], 'earned owner lost')
        need(e['party'] == before['party'] and e['factory'] == before['factory'] and e['count'] == 1
             and e['bp'] == expected_bp and not any(e[k] for k in ('flags','newbs','snapshot','marker','pending')),
             'restoration/cleanup/BP')
    need(returned['owner'] == saved['owner'] == loaded['owner']
         and saved['save_counter'] == loaded['save_counter'] == 4, 'Save/fresh Continue64')
    need(all(e['save_counter'] == 3 for e in tail[:-2]), 'unexpected standard Save')
    need(result['new_battles'] == len(outcomes) and result['new_wins'] == wins
         and result['new_losses'] == losses and result['attempts'] == len(draws)
         and result['bp_after'] == expected_bp and result['total_frames'] == loaded['frame'], 'result accounting')
    return dict(result=result, calls=calls, actual_suppression_observed=True,
                lifecycle_verified=True, visual_review_completed=False,
                physical_admission_accepted=False, suppression_accepted=False, release_ready=False)
