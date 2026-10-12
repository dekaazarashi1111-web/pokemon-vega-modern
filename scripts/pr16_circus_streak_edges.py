"""ハッシュ固定のCircus複製scriptから第3戦完走edgeだけを導出する。"""
import hashlib
import struct

BASE = 0x08000000
COMPLETION_OWNERS = {
    'facility_runtime_payload', 'factory_reward_runtime_payload',
    'factory_repeat_reward_runtime_payload', 'factory_special_event_runtime_payload',
    'factory_shiny_memorial_runtime_payload', 'factory_high_modes_v2_stage42_payload',
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def completion_binding(raw, continuation, afterbattle, clone, allocation):
    """AfterBattle→RESULT=2の唯一の完走枝。Stage20の古いnative値を推測しない。"""
    need(type(raw) is bytes, 'immutable ROM required')
    lo, hi = clone['start'], clone['end_exclusive']
    at = continuation - BASE
    need(0 <= lo <= at and at + 16 <= hi <= len(raw), 'third continuation escaped clone')
    expected = b'\x23' + struct.pack('<I', afterbattle) + bytes.fromhex('210d8002000601')
    need(raw[at:at + 12] == expected, 'third win condition or AfterBattle differs')
    target = struct.unpack_from('<I', raw, at + 12)[0]
    off = target - BASE
    need(lo <= off and off + 15 <= hi, 'completion script escaped clone')
    body = raw[off:off + 15]
    need(body[:1] == b'\x23' and body[5:7] == b'\x0f\x00'
         and body[11:] == bytes.fromhex('09046c02'), 'completion command boundary differs')
    native = struct.unpack_from('<I', body, 1)[0]
    need(native & 1 and BASE <= native < BASE + len(raw), 'completion target is not Thumb ROM')
    owners = [r for r in allocation['allocations']
              if r['start'] <= (native & ~1) - BASE < r['end_exclusive']]
    need(len(owners) == 1 and owners[0]['name'] in COMPLETION_OWNERS,
         f'completion target {native:#x} has no known Factory wrapper owner: {[r["name"] for r in owners]}')
    owner = owners[0]
    digest = hashlib.sha256(raw[owner['start']:owner['end_exclusive']]).hexdigest()
    need(digest == owner['content_sha256'], 'completion wrapper owner hash differs')
    return dict(afterbattle_call=continuation, condition=raw[at:at + 16].hex(),
                script=target, native=native, commands=body.hex(),
                allocation=owner['name'], allocation_sha256=digest,
                scope='THIRD_WIN_CLONE_EDGE_ONLY_FACTORY_ORIGINAL_UNCHANGED')
