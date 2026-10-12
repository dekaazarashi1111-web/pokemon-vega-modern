"""25戦目の通常入力だけを変更し、変更前prefixを原本と完全照合する。"""
import hashlib
import json

MARKER = b'CIRCUS_BATTLE25_INPUT_CHANGE '
POLICY_SHA = 'a740eaba10cfb7f8bfc97585ef9fe84c40181cb9c616e113a7ce72d108d47515'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def replace_once(text, old, new):
    need(text.count(old) == 1, 'policy exact anchor differs: ' + old[:60])
    return text.replace(old, new)


def adapt(text, header):
    need(hashlib.sha256(text.encode()).hexdigest() == POLICY_SHA, 'original generated policy differs')
    need('b25_rank' in header and 'b25_legacy_plan' in header, 'policy header incomplete')
    text = replace_once(text, 'uint64_t score=scores[i];',
                        'uint64_t score=b25_rank(read16(c,0x0203DB20U),scores[i],types[i]);')
    old = '    for(unsigned n=0;n<3U;++n){unsigned k=order[n],best=planned[k];'
    new = '''    unsigned legacy_plan[3],legacy_order[3],legacy_j=0U;
    b25_legacy_plan(scores,types,legacy_plan);
    unsigned legacy_lead=ta_lead(read16(c,0x0203DB20U),legacy_plan,capable);
    bp_require(c,legacy_lead<3U,"Circus legacy selection permutation");
    legacy_order[legacy_j++]=legacy_lead;
    for(unsigned i=0;i<3U;++i)if(i!=legacy_lead)legacy_order[legacy_j++]=i;
    for(unsigned n=0;n<3U;++n){unsigned k=order[n],best=planned[k];
        if(best!=legacy_plan[legacy_order[n]])
            fprintf(stderr,"CIRCUS_BATTLE25_INPUT_CHANGE {\\"frame\\":%u,\\"streak\\":%u,\\"index\\":%u,\\"old_slot\\":%u,\\"new_slot\\":%u}\\n",
                b_frames,read16(c,0x0203DB20U),n,legacy_plan[legacy_order[n]],best);'''
    return header + '\n' + replace_once(text, old, new)


def prefix_proof(old, new, old_events, new_events):
    need(type(old) is type(new) is bytes and MARKER not in old, 'original/input trace type')
    before, found, after = new.partition(MARKER)
    need(found and old.startswith(before), 'input changed before declared boundary')
    marker = json.loads(after.splitlines()[0])
    need(set(marker) == {'frame', 'streak', 'index', 'old_slot', 'new_slot'} and
         all(type(x) is int for x in marker.values()), 'input boundary schema')
    need(marker['streak'] == 24 and marker['index'] == 2 and marker['old_slot'] == 5 and
         marker['new_slot'] == 0 and marker['frame'] > 402479, 'first changed input not battle25 slot3')
    need(len(old_events) == 121 and len(new_events) >= 114, 'prefix event count')
    need(old_events[:113] == new_events[:113], 'accepted 24-win event prefix differs')
    need(old_events[112]['label'] == 'returned' and old_events[112]['battle'] == 24 and
         old_events[112]['frame'] == 402479, '24-win boundary differs')
    selection = new_events[113]
    need(selection['label'] == 'selected' and selection['battle'] == 24 and
         selection['frame'] > marker['frame'] and selection['order'] == [3, 2, 1], 'new ordinary selection differs')
    return dict(exact_event_count=113, byte_prefix_size=len(before),
                byte_prefix_sha256=hashlib.sha256(before).hexdigest(), first_changed_input=marker,
                accepted_standalone_replays=0, accepted_prefix_battles_reexecuted_for_continuation=24)
