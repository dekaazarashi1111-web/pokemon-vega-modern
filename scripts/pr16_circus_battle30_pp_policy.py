"""未完30戦目から、同点の攻撃技は残PPの多い方を通常UIで選ぶ。"""
from __future__ import annotations
import hashlib
import json
import pr16_circus_reserve_fallback_policy as parent

OLD_TRACE=dict(size=987167,sha256='b735ac2ffc95aab7de1168ecb8b8a3ab992925e4bf4f3f125917b84c907d0982')
OLD_POLICY_SHA='08cfc991436262e2298582703969ed39828479b5547322df042d3b4f9da6d26a'
MARKER=b'CIRCUS_PP_TIE '
PURE=r'''
/* 同じ評価ダメージ/命中率なら残PPを温存する。低命中・無効・blockedは復活させない。
 * 新たな未完範囲である30戦目以降だけ。frame、種族、乱数、予測勝敗は参照しない。 */
static unsigned pc_pick(unsigned streak,unsigned selected,unsigned blocked,
    const uint64_t score[4],const unsigned accuracy[4],const unsigned pp[4])
{
    if(streak<29U || selected>=4U || (blocked&(1U<<selected))
        || !score[selected] || !accuracy[selected] || !pp[selected])return selected;
    unsigned best=selected;
    for(unsigned i=0U;i<4U;++i)
        if(!(blocked&(1U<<i)) && score[i]==score[selected]
            && accuracy[i]==accuracy[selected] && pp[i]>pp[best])best=i;
    return best;
}
'''
DECISION=r'''    unsigned reserves[4];
    for(unsigned i=0U;i<4U;++i)reserves[i]=read8(c,own+BATTLE_MON_PP_OFFSET+i);
    unsigned conserving=pc_pick(streak,actual,rr_memory.blocked,scores,reliability,reserves);
    if(conserving!=actual){
        fprintf(stderr,"CIRCUS_PP_TIE {\"frame\":%u,\"streak\":%u,\"selected\":%u,\"actual\":%u,\"blocked\":%u,\"score\":%llu,\"accuracy\":%u,\"old_pp\":%u,\"new_pp\":%u,\"old_move\":%u,\"new_move\":%u}\n",
            b_frames,streak,actual,conserving,rr_memory.blocked,(unsigned long long)scores[actual],
            reliability[actual],reserves[actual],reserves[conserving],
            read16(c,own+BATTLE_MON_MOVES_OFFSET+2U*actual),read16(c,own+BATTLE_MON_MOVES_OFFSET+2U*conserving));
        actual=conserving;
    }
'''
need=parent.need
identity=parent.identity
rows=parent.rows


def amend(text):
    need(hashlib.sha256(text.encode()).hexdigest()==OLD_POLICY_SHA,'saved reserve policy identity')
    anchor='static unsigned rr_move_slot(struct mCore *c)\n{'
    need(text.count(anchor)==1,'reentry definition anchor')
    text=text.replace(anchor,PURE+'\n'+anchor,1)
    anchor='    actual=ta_move(c,actual);\n'
    need(text.count(anchor)==1,'final move selection anchor')
    return text.replace(anchor,DECISION+anchor,1)


def adapt(text,header):return amend(parent.adapt(text,header))


def original(raw):
    need(identity(raw)==OLD_TRACE,'previous reserve trace identity')
    events=rows(raw,b'CIRCUS_CONTINUOUS ')
    settled=[e for e in events if e['label']=='settled']
    need(len(events)==143 and sum(e['outcome']==1 for e in settled)==29
         and sum(e['outcome']==2 for e in settled)==1,'previous actual outcome')
    need(events[135]['label']=='settled' and events[135]['frame']==480015 and events[135]['outcome']==1
         and events[137]['label']=='action' and events[137]['battle']==29 and events[137]['frame']==482072,'accepted29 boundary')
    need(events[-2]['label']=='saved' and events[-1]['label']=='reloaded' and events[-1]['save_counter']==3
         and events[-1]['bp']==81,'previous save boundary')
    need(raw.count(parent.MARKER)==1 and MARKER not in raw,'previous policy marker scope')
    for line in (b'BP_WIN_MOVE frame=482072 slot=1 move=58 pp=16 power=90 type=15 split=1 score=458737',
                 b'BP_WIN_MOVE frame=482072 slot=2 move=352 pp=32 power=60 type=11 split=1 score=458737'):
        need(line+b'\n' in raw,'actual equal-damage move boundary')
    return dict(events=143,wins=29,losses=1,uncompleted_battle=30,first_action_frame=482072,
                original_conclusion='failure',previous_lifecycle_preserved=True,
                reason_ja='29戦目を通常交代で突破。30戦目初手は実評価458737で技58(PP16)と352(PP32)が同点。前29勝を保ち、この同点選択から未完を継続。')


def prefix_proof(old,new):
    original(old)
    before,found,tail=new.partition(MARKER)
    need(found and old.startswith(before),'changed before battle30 tie')
    first=json.loads(tail.splitlines()[0])
    expected=dict(frame=482072,streak=29,selected=1,actual=2,blocked=0,score=458737,
                  accuracy=100,old_pp=16,new_pp=32,old_move=58,new_move=352)
    need(first==expected and all(type(x) is int for x in first.values()),'battle30 tie marker differs')
    need(rows(new,b'CIRCUS_CONTINUOUS ')[:138]==rows(old,b'CIRCUS_CONTINUOUS ')[:138],
         'accepted29 and action30 event prefix changed')
    need(rows(new,parent.MARKER)[:1]==rows(old,parent.MARKER),'accepted29 reserve marker changed')
    need(b'CIRCUS_REENTRY frame=482072 streak=29 selected=1 actual=2 move=352 blocked=0 pp=32 foe_hp=167\n' in new,
         'selected normal move does not match tie decision')
    return dict(exact_event_count=138,byte_prefix=identity(before),first_tie=first,
                accepted_standalone_replays=0,continuation_prefix_wins=29)
