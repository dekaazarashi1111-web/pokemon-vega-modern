"""28戦目の交代直後の瀕死を通常の強制交代へ渡す。ROM/RAM注入はしない。"""
from __future__ import annotations
import hashlib
import json
import pr16_circus_battle25_policy as previous

MARKER = b'CIRCUS_SWITCH_HANDOFF '
ORIGINAL_STDERR = dict(size=921609, sha256='7a9ae4faf5b2e68e18883cf0f3507cfb6b2d12ba2ee631cebbb1d962949cba84')
HELPER = r'''
/* 戻り値1は同一個体の瀕死＋通常party UI、2は真正native勝敗のみ。 */
static unsigned sh_pending;
static unsigned sh_kind(unsigned streak, unsigned action, unsigned party,
    unsigned hp, unsigned identity, unsigned outcome)
{
    if (streak < 27U || action) return 0U;
    if (outcome == 1U || outcome == 2U) return 2U;
    return !outcome && party && !hp && identity ? 1U : 0U;
}
'''


def need(ok, text):
    if not ok:
        raise ValueError(text)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def events(raw):
    return [json.loads(line.split(b' ', 1)[1]) for line in raw.splitlines()
            if line.startswith(b'CIRCUS_CONTINUOUS ')]


def adapt(text, header):
    """旧生成Cの固定hashは25戦目adapterが検査。完全一致anchorだけを修正。"""
    text = previous.adapt(text, header)
    replace = previous.replace_once
    text = replace(text, 'static unsigned tp_streak=65535U,tp_switches,tp_seen;',
                   HELPER + '\nstatic unsigned tp_streak=65535U,tp_switches,tp_seen;')
    # 宣言はbr_move/rr_move_slotより前。定義の二重作成を避ける。
    text = replace(text, 'static unsigned sh_pending;\n', '')
    text = 'static unsigned sh_pending;\n' + text
    text = replace(text, 'static void tp_consider(struct mCore *c)\n{',
                   'static void tp_consider(struct mCore *c)\n{\n    sh_pending=0U;')
    anchor = '        bp_require(c,!read8(c,BATTLE_CORE_BATTLE_OUTCOME),"Circus tactical switch ended unexpectedly");'
    insertion = r'''        unsigned same=read32(c,own+0x48U)==target_pid && read32(c,own+0x54U)==target_ot && read16(c,own)==species;
        unsigned kind=sh_kind(streak,n_action(c),read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY,
            read16(c,own+BATTLE_CORE_MON_HP),same,read8(c,BATTLE_CORE_BATTLE_OUTCOME)&0x7FU);
        if(kind){
            fprintf(stderr,"CIRCUS_SWITCH_HANDOFF {\"frame\":%u,\"streak\":%u,\"kind\":%u,\"hp\":%u,\"same_individual\":%u}\n",
                b_frames,streak,kind,read16(c,own+BATTLE_CORE_MON_HP),same);
            sh_pending=kind;return;
        }
'''
    text = replace(text, anchor, insertion + anchor)
    text = replace(text, '    tp_consider(c);\n',
                   '    tp_consider(c);\n    if(sh_pending){bp_require(c,!n_action(c),"Circus handoff still action");return 4U;}\n')
    text = replace(text, '    slot=rr_move_slot(c);\n',
                   '    slot=rr_move_slot(c);\n    if(sh_pending){bp_require(c,slot==4U && !n_action(c),"Circus handoff sentinel");sh_pending=0U;return;}\n')
    need(text.count('CIRCUS_SWITCH_HANDOFF ') == 1, 'handoff trace anchor')
    return text


def diagnostic(raw, *, original=False):
    """未完processの成功prefixも失敗とは別に保存。Save成功へは昇格しない。"""
    if original:
        need(identity(raw) == ORIGINAL_STDERR, 'previous stderr identity')
    rows = events(raw)
    settled = [r for r in rows if r['label'] == 'settled']
    wins = sum(r['outcome'] == 1 for r in settled)
    losses = sum(r['outcome'] == 2 for r in settled)
    returned = [r for r in rows if r['label'] == 'returned']
    result = dict(events=len(rows), settled_wins=wins, settled_losses=losses,
                  last_event={k: rows[-1][k] for k in ('label', 'frame', 'battle', 'bp', 'save_counter')} if rows else None,
                  returned_batches=len(returned), normal_save_observed=any(r['label']=='saved' for r in rows),
                  fresh_continue_observed=any(r['label']=='reloaded' for r in rows),
                  trace=identity(raw), lifecycle_accepted=False)
    if original:
        need(len(rows)==130 and wins==27 and losses==0 and len(returned)==9, 'previous 27-win prefix')
        need(returned[-1]['battle']==27 and returned[-1]['bp']==81 and returned[-1]['frame']==435272, 'previous settlement')
        need(not result['normal_save_observed'] and not result['fresh_continue_observed'], 'previous Save scope')
        need(rows[-1]['label']=='action' and rows[-1]['battle']==27 and rows[-1]['frame']==438984, 'previous battle28')
        need(b'Circus tactical selected individual did not survive to action' in raw, 'previous failure reason')
        first=rows[0]
        for row in returned:
            need(row['count']==1 and row['party']==first['party'] and row['factory']==first['factory'], 'previous original600 restoration')
        result.update(original_conclusion='failure', native_processes=1, original_party_bytes_restored=600,
                      stop_ja='27勝81BP/9回元party復元。28戦目の通常交代先が瀕死となり強制交代UIで停止。Save/Continue未達。')
    return result


def prefix_proof(old, new):
    diagnostic(old, original=True)
    before, marker, tail = new.partition(MARKER)
    need(marker and old.startswith(before), 'changed before handoff boundary')
    value=json.loads(tail.splitlines()[0])
    need(set(value)=={'frame','streak','kind','hp','same_individual'} and
         all(type(x) is int for x in value.values()), 'handoff marker schema')
    need(value['streak']==27 and value['kind']==1 and value['hp']==0 and value['same_individual']==1 and
         451188<value['frame']<469624, 'first handoff not original battle28 faint')
    old_events, new_events=events(old), events(new)
    need(len(new_events)>=130 and old_events==new_events[:130], '27-win and battle28 event prefix changed')
    return dict(exact_event_count=130, byte_prefix=identity(before), first_handoff=value,
                accepted_standalone_replays=0, continuation_prefix_wins=27)
