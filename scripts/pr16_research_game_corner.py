#!/usr/bin/env python3
"""実GAME_CORNERの既採取traceと別core Continueを独立照合する。再実行しない。"""
from __future__ import annotations
import base64
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path
import pr16_research_bug as prior

ROOT = Path(__file__).resolve().parents[1]
C = 'tools/mgba_pr16_research_game_corner.c'
CANDIDATE = prior.CANDIDATE
MODEL = 'content/research_economy_v1/canonical_model.json'
TOKEN = 1 ^ (300 << 16) ^ 923
FLASH = {'size': 131072, 'sha256': 'eed9d6c233bc3d4012db6d033db907d0b18ba732704a229bb468ea4708739a5c'}
SAVE = {'size': 131088, 'sha256': 'c7f6a40cb830308cbd8721561edf4c0de257c4477176febc7ec473e8b74547c8'}
need, identity, load, exact = prior.need, prior.identity, prior.load, prior.exact
integer = prior.photo.catalog.integer

def generate(seed: bytes) -> bytes:
    text = prior.generate(seed).decode('utf-8')
    token = 'int main(int argc,char**argv){'
    need(text.count(token) == 1, 'unique inherited main')
    return (text.replace(token, 'int accepted_bug_main(int argc,char**argv){')
            + '\n' + (ROOT / C).read_text(encoding='utf-8')).encode('utf-8')

def unpack_text(encoded: bytes, meta: dict, limit: int = 1200000) -> bytes:
    """原本stdout用。ROM/saveや実行コードを展開する汎用transportではない。"""
    need(type(encoded) is bytes and len(encoded) <= 150000, 'bounded text transport')
    integer(meta.get('size'), 1, limit)
    need(type(meta.get('sha256')) is str and re.fullmatch('[0-9a-f]{64}', meta['sha256']), 'text digest')
    try:
        packed = base64.b85decode(encoded.strip())
        dec = zlib.decompressobj()
        raw = dec.decompress(packed, meta['size'] + 1)
        need(dec.eof and not dec.unused_data and not dec.unconsumed_tail, 'one complete bounded stream')
        raw.decode('utf-8')
    except (ValueError, UnicodeError, zlib.error) as exc:
        raise ValueError('invalid text transport') from exc
    need(identity(raw) == meta and b'\0' not in raw, 'exact UTF-8 original text')
    return raw

def _hex(value, size):
    need(type(value) is str and len(value) == size * 2 and re.fullmatch('[0-9a-f]*', value), 'canonical byte record')
    return bytes.fromhex(value)

def _digest(value):
    need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'canonical digest')

def _owner(minute: int, phase: str) -> bytes:
    integer(minute, 0, 59)
    b = bytearray(64)
    b[0], b[1], b[6], b[7], b[36] = 1, 64, 1, minute, 1
    if phase == 'prepared':
        b[36] = 2
        struct.pack_into('<I', b, 44, TOKEN)
        b[48], b[49], b[50], b[52] = 1, 1, 2, 3
    elif phase == 'credited':
        b[4] = b[10] = b[18] = 3
        b[36] = 2
        struct.pack_into('<I', b, 40, TOKEN)
    else:
        need(phase == 'initial', 'closed owner phase')
    return bytes(b)

def _event(event: dict, ledger: dict, fixture: bytes | None, phase: str, counter: int):
    old = prior.photo.purchase.prior.prior.old
    at = prior.photo.purchase.prior.prior.OFFSET
    need(set(event) == old.lc.EVENT_FIELDS and set(ledger) == old.lc.LEDGER_FIELDS, 'closed full-state schema')
    need(type(event['counter']) is int and event['counter'] == counter, 'save count')
    owner = _hex(event['owner'], 64)
    need(owner == _owner(owner[7], phase), 'all 64 owner bytes')
    for k in ('inventory_sha256', 'other_inventory_sha256', 'party_sha256'):
        _digest(event[k])
    need(type(event['party_count']) is int and event['party_count'] == 6
         and type(event['item_quantity']) is int and event['item_quantity'] == 0, 'whole party/Bag shape')
    if fixture is not None:
        need(type(fixture) is bytes and len(fixture) == 131072, 'original-derived disk fixture')
        source = fixture[at:at + 2048]
        need(source[0x73f:0x77f] == _owner(0, 'initial'), 'zero-RP original fixture owner')
        need(old.checksum(source) == int.from_bytes(source[8:12], 'little'), 'fixture checksum')
        modeled = bytearray(source)
        modeled[0x73f:0x77f] = owner
        modeled = old.seal(modeled)
        unrelated = bytearray(modeled)
        unrelated[4:6] = bytes(2)
        unrelated[8:12] = bytes(4)
        unrelated[0x73f:0x77f] = bytes(64)
        need(exact(ledger, dict(ledger_event=event['event'], version=2, size=2048,
            checksum_valid=True, ledger_sha256=identity(modeled)['sha256'],
            unrelated_ledger_sha256=identity(unrelated)['sha256'], migration_dirty=0, recovery_blocked=0)),
            'independent entire ledger / checksum / unrelated owners')
    else:
        # 原本saveは公開しない。公開再検証では独立実測済みdigestを照合する。
        gold = {('initial',1): 'bdaae0a71b80b9dd0f133c1633bf13863fd6d42a9f3364c557e2db0ea12356ce',
                ('credited',28): '572c91b689ae5ece138273cbc29f456572ffae4f2f444486afe8d24a31bd411e',
                ('credited',18): '0d595dce782530fe0c7567c93cc50cf39a13310372975b78bf03d5e116b92794'}
        need((phase,owner[7]) in gold, 'recorded full-ledger state')
        need(exact(ledger, dict(ledger_event=event['event'], version=2, size=2048,
            checksum_valid=True, ledger_sha256=gold[(phase,owner[7])],
            unrelated_ledger_sha256='f94facc9b8c3ff8c744aab1065f7662b386e5ab8d78646d17d60f495ff26884e',
            migration_dirty=0, recovery_blocked=0)), 'full-ledger recorded digest')
    return owner

def _same_inventory(first, last):
    for k in ('inventory_sha256', 'other_inventory_sha256', 'party_sha256', 'party_count', 'item_quantity'):
        need(type(first[k]) is type(last[k]) and first[k] == last[k], 'Bag/party byte preservation: ' + k)

def _observation(row: dict):
    need(set(row) == {'observation', 'frame', 'coins', 'rp', 'counter', 'callback', 'field',
                     'map', 'state_address', 'state', 'owner', 'volatile'}, 'closed observation schema')
    for k, hi in [('frame', 300900), ('coins', 9999), ('rp', 9999), ('counter', 10), ('callback', 0x0a000000)]:
        integer(row[k], 0, hi)
    need(type(row['field']) is bool and exact(row['map'], [98, 56, 1, 7]), 'physical map and stance')
    need(row['callback'] in (0x08055e75, 0x08140071), 'native field or slot callback')
    p = row['state_address']
    need(type(p) is int and (p == 0 or 0x02000000 <= p <= 0x0203ffa0), 'bounded minigame owner')
    need(not row['field'] or (row['callback'] == 0x08055e75 and p == 0), 'idle field cannot own slot state')
    state = _hex(row['state'], 96 if p else 0)
    owner, volatile = _hex(row['owner'], 64), _hex(row['volatile'], 36)
    need(volatile[:4] == b'REV1' and volatile[20:22] == b'\xff\xff'
         and volatile[4:10] == bytes(6) and volatile[22:25] == bytes(3)
         and volatile[25] in (0, 1) and volatile[26:30] == bytes(4) and volatile[34:36] == bytes(2), 'no mocks/unlock/fault/rollback')
    need(int.from_bytes(owner[4:6], 'little') == row['rp'], 'observed credit equals full owner')
    return state, owner, volatile

def audit(rom: bytes, model: dict) -> dict:
    need(identity(rom) == CANDIDATE, 'exact candidate')
    def rd(a): return struct.unpack_from('<I', rom, a - 0x08000000)[0]
    def span(a, n): return rom[a - 0x08000000:a - 0x08000000 + n]
    event = rd(0x092c3a90)
    background = rd(event + 16) + 13 * 12
    script = rd(background + 8)
    need((event, background, script) == (0x09413f30, 0x09413e10, 0x094324dd), 'physical slot root')
    need(span(background, 8) == bytes.fromhex('0000070000000000'), 'slot background (0,7)')
    need(span(script, 13) == bytes.fromhex('69160480000005ea2443096b02'), 'slot0 authored script')
    need(span(0x094324ea, 6) == bytes.fromhex('2b60180600e8'), 'ordinary coin-case flag check')
    need(span(0x0943251d, 3) == bytes.fromhex('890d80'), 'actual playslotmachine opcode')
    targets = []
    for a in (0x0814061a, 0x0814065a):
        high, low = struct.unpack('<HH', span(a, 4))
        need(high & 0xf800 == 0xf000 and low & 0xf800 == 0xf800, 'Thumb BL')
        off = ((high & 0x7ff) << 12) | ((low & 0x7ff) << 1)
        if off & 0x400000: off -= 0x800000
        targets.append(a + 4 + off)
    need(targets == [0x0837bea4, 0x0837bea4], 'both payout hooks reach one veneer')
    row = model['activities'][2]
    need(row['activity'] == 'GAME_CORNER' and type(row['points_awarded']) is int
         and row['points_awarded'] == 3 and row['daily_cap'] == 18
         and row['completion_semantics'] == 'PAYOUT_NET_GAIN_AT_LEAST_100_COMMIT_ONCE', 'canonical payout contract')
    return dict(candidate=CANDIDATE, event=event, background=background, script=script,
                payout_hooks=[0x0814061a, 0x0814065a], veneer=targets[0], rom_changes=0)

def validate_trace(raw: bytes, fixture: bytes | None = None, *, _screens: bool = True) -> dict:
    need(type(raw) is bytes and 0 < len(raw) < 1200000, 'bounded trace')
    rows = [load(line) for line in raw.splitlines()]
    group, prefix = (3, 5) if _screens else (2, 4)
    need(len(rows) >= prefix + group + 3 and (len(rows) - prefix - 3) % group == 0, 'complete trace groups')
    need(exact(rows[0], dict(root_event=0x09413f30, root_script=0x094324dd)), 'root observation')
    need(exact(rows[-1], dict(status='STOPPED', case='game-corner-diagnostic', native_acceptance=False,
        fresh_cores=1, guarded_host_writes=0, accepted_case_reruns=0)), 'diagnostic status retained, never relabelled')
    initial_owner = _event(rows[1], rows[2], fixture, 'initial', 2)
    end_owner = _event(rows[-3], rows[-2], fixture, 'credited', 4)
    need(rows[1]['event'] == 'fixture' and rows[-3]['event'] == 'end', 'full-state endpoints')
    _same_inventory(rows[1], rows[-3])
    need(rows[1]['inventory_sha256'] == rows[1]['other_inventory_sha256'] ==
         '688c3d52d630e445add9fb46d2b1d85448f8637d8262457aeba156c64704c3ec'
         and rows[1]['party_sha256'] ==
         '55514c6b16a517c723e3cdfe4826075020b214905950ada9cd65b41a97419430',
         'fixed original fixture party and all Bag pockets')
    _observation(rows[3])
    need(rows[3]['observation'] == 'fixture' and rows[3]['frame'] == 900
         and rows[3]['coins'] == 1000 and rows[3]['rp'] == 0 and rows[3]['counter'] == 2
         and _hex(rows[3]['owner'], 64) == initial_owner, 'zero-RP entry')
    observations = [rows[3]]
    screens = [rows[4]] if _screens else []
    frame, previous_minute, phase_index, phase_counts = 900, initial_owner[7], 0, [0, 0, 0, 0]
    jackpot, small_payout, early_no_credit = [], False, False
    for n, i in enumerate(range(prefix, len(rows) - 3, group), 1):
        command, obs = rows[i:i+2]
        need(set(command) == {'input', 'keys', 'frames', 'start_frame'}, 'physical command schema')
        need(type(command['input']) is int and command['input'] == n
             and type(command['start_frame']) is int and command['start_frame'] == frame, 'continuous command ordinal/frame')
        integer(command['keys'], 0, 1023)
        frame += integer(command['frames'], 1, 10000)
        need(frame <= 300900 and obs['frame'] == frame
             and obs['observation'] == f'step-{n:03d}', 'continuous observations')
        state, owner, volatile = _observation(obs)
        need(previous_minute <= owner[7] <= initial_owner[7] + (frame - 900) // 3500 + 2, 'bounded natural minute advancement')
        previous_minute = owner[7]
        if owner == _owner(owner[7], 'initial'): phase = 0
        elif owner == _owner(owner[7], 'prepared'): phase = 1
        else:
            need(owner == _owner(owner[7], 'credited'), 'exclusive payout mutation')
            phase = 2 if obs['counter'] == 3 else 3
        need(phase_index <= phase <= phase_index + 1, 'ordered prepare / credit / durable phases')
        need(obs['counter'] == [2, 2, 3, 4][phase], 'one phase1 and one phase2 save')
        phase_index = phase
        phase_counts[phase] += 1
        if volatile[25]:
            need(state, 'active payout has a live minigame owner')
            initial = int.from_bytes(volatile[10:12], 'little')
            pre = int.from_bytes(volatile[12:14], 'little')
            remaining = int.from_bytes(state[80:82], 'little')
            need(0 < remaining < initial and obs['coins'] + remaining == min(9999, pre + initial),
                 'all observed partial payout coins are conserved')
        if volatile[25] and int.from_bytes(volatile[10:12], 'little') == 300:
            need(state and int.from_bytes(volatile[12:14], 'little') == 923, 'payout origin')
            remaining = int.from_bytes(state[80:82], 'little')
            need(obs['coins'] + remaining == 1223 and phase == 0 and 0 < remaining < 300, 'animated payout accounting before commit')
            jackpot.append([frame, obs['coins'], remaining])
            if obs['coins'] >= 1023: early_no_credit = True
        before = observations[-1]
        before_state = bytes.fromhex(before['state'])
        if before_state and int.from_bytes(before_state[80:82], 'little') == 4:
            if obs['coins'] - before['coins'] == 4 and obs['rp'] == before['rp'] == 0 and obs['counter'] == 2:
                small_payout = True
        observations.append(obs)
        if _screens: screens.append(rows[i+2])
    need(all(phase_counts) and phase_index == 3 and len(jackpot) >= 2
         and small_payout and early_no_credit, 'real small payout / deferred 300 payout / completed transaction')
    need(observations[-1]['field'] is True and observations[-1]['state_address'] == 0
         and _hex(observations[-1]['owner'], 64) == end_owner, 'physical exit / end snapshot')
    for n, (screen, obs) in enumerate(zip(screens, observations)):
        label = 'fixture' if n == 0 else f'step-{n:03d}'
        need(set(screen) == {'screen', 'sha256', 'frame'} and screen['screen'] == f'game-corner-{label}.ppm'
             and type(screen['frame']) is int and screen['frame'] == obs['frame'], 'one original image per observation')
        _digest(screen['sha256'])
    return dict(status='PASS_ANIMATED_PAYOUT_TRACE_SCOPED', candidate=CANDIDATE,
        stdout=identity(raw), screen_records_included=_screens, commands=len(observations)-1, frame_end=frame,
        phase_observation_counts=phase_counts, jackpot_observations=jackpot,
        payout_before=923, payout_after=1223, payout=300, rp_earned=3,
        small_payout_no_rp=True, credit_only_after_payout_finalization=True,
        transaction_saves=2, final_unsaved_coins=observations[-1]['coins'],
        final_unsaved_minutes=end_owner[7], final_event=rows[-3], final_ledger=rows[-2],
        bulk_payout_native_accepted=False, daily_cap_native_accepted=False,
        natural_arrival_accepted=False, all_activities_accepted=False, accepted_case_reruns=0)

def validate_continue(raw: bytes, fixture: bytes | None, trace: dict) -> dict:
    need(type(raw) is bytes and 0 < len(raw) < 16000, 'bounded Continue trace')
    rows = [load(line) for line in raw.splitlines()]
    need(len(rows) == 8, 'complete Continue records')
    expected = dict(status='PASS', case='game-corner-continue', fresh_cores=1,
        coins=1223, rp=3, counter=4, flash_sha256=FLASH['sha256'], manual_saves=0,
        new_earning_processes=0, guarded_host_writes=0, accepted_case_reruns=0, warnings_errors=0)
    need(exact(rows[-1], expected), 'Continue exact terminal scope')
    for a, b, c, label in ((0,1,2,'continued'),(4,5,6,'continued-idle')):
        _observation(rows[a])
        need(rows[a]['field'] is True and rows[a]['state_address'] == 0 and rows[a]['observation'] == label
             and rows[a]['coins'] == 1223 and rows[a]['rp'] == 3 and rows[a]['counter'] == 4, 'payout snapshot restored, no slot replay')
        owner = _event(rows[b], rows[c], fixture, 'credited', 4)
        need(rows[b]['event'] == label and _hex(rows[a]['owner'],64) == owner, 'Continue endpoint owner agreement')
        _same_inventory(trace['final_event'], rows[b])
    need(rows[0]['frame'] == 0 and rows[4]['frame'] == 600, 'new core and bounded idle observation')
    need(set(rows[3]) == {'screen','sha256','frame'} and rows[3]['screen'] == 'game-corner-continued.ppm'
         and rows[3]['frame'] == 0, 'Continue real field screen')
    _digest(rows[3]['sha256'])
    return dict(expected, stdout=identity(raw), save_file=SAVE, flash=FLASH,
                rtc_trailer_bytes=16, unsaved_post_payout_bets_restored_on_continue=True,
                end_owner=rows[5]['owner'], screen=rows[3], natural_arrival_accepted=False)


def validate_events(raw: bytes, fixture: bytes | None = None) -> dict:
    """未確認画像行だけを除いた全native観測行。値や順序は変更しない。"""
    return validate_trace(raw, fixture, _screens=False)
