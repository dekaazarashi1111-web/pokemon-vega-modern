#!/usr/bin/env python3
"""保存message callerのslot/font供給と未結合速度delegate一根を限定する。"""
from __future__ import annotations
import copy
import sys
import pr16_ring_text_audio_sequence as current
import pr16_ring_text_export_recovery as export
import pr16_ring_followup_v2 as s

BASE = '868eb7a6caf2bdc42d5997d18e9e1707acc61718'
SLUG = 'pr16-ring-message-owner-frontier'
TASK = 'PR-P08-7-RING-MESSAGE-OWNER-FRONTIER'
TITLE = 'message実callerのslot0・font分岐と未結合速度delegateを保存'
SELF = 'scripts/pr16_ring_message_owner_frontier.py'
TEST = 'tests/test_pr16_ring_message_owner_frontier.py'
WORKFLOW = '.github/workflows/pr16-ring-message-owner-frontier.yml'
PRIOR = export.REPORT
REPORT = 'content/modernization/pr16_ring_message_owner_frontier.json'
KEY = 'latest_ring_diagnostic'
MIN_TESTS = 24
EXTRA_CODE = ()
RESTORE = '.github/workflows/pr16-ring-callee-bytes.yml'
SOURCES = tuple(dict.fromkeys((current.SELF, *current.SOURCES, export.SELF,
    'scripts/pr16_ring_zero_bytes.py', RESTORE, 'scripts/pr16_ring_transitive_owner.py',
    'scripts/pr16_ring_remaining_frontier.py', 'scripts/pr16_ring_owner_frontier.py')))
NO_REPEAT = ('message実callerのslot0/font2/4/5供給と速度delegate一根を保存。'
    '同じ採取・混在列333/旧renderer/audio/glyph/BP/nativeを単独再実行しない。'
    '次は保存速度byteとmessage callerの設定/不足/slot書込/callback選択を一体検証。')
need = s.need
MESSAGE = 0x080f7dbd
PRODUCER = 0x08068d89
BUILDER = 0x080f7d29
SPEED = 0x0937855d
LO, HI = SPEED & ~1, 0x09378588
TEXT = 0x02021c88
POOL = 0x02020030
GFONTS = 0x03003dd0
CALLS = ((0x080f7e00, 4, 'fff792ff'), (0x080f7e30, 5, 'fff77aff'), (0x080f7e58, 2, 'fff766ff'))


def saved_inputs():
    nodes, memory, context = current.saved_inputs()
    return nodes, memory, context, s.load(current.REPORT)['analysis']


def plan(nodes, analysis):
    by = {n['address']: n for n in nodes}
    need(len(by) == len(nodes) == 7291, '保存7291命令')
    need(analysis['candidate'] == s.CANDIDATE and analysis['contract_cases'] == 333, '保存candidate/混在列')
    for key in ('ring_acquisition_accepted', 'release_ready', 'initializer_runtime_observed', 'actual_callback_table_observed'):
        need(analysis[key] is False, '未受入境界 ' + key)
    def exact(at, raw, **fields):
        n = by.get(at, {})
        need(n.get('hex') == raw and n.get('size') == len(bytes.fromhex(raw)), 'caller byte ' + hex(at))
        need(all(n.get(k) == v for k, v in fields.items()), 'caller metadata ' + hex(at))
    exact(0x08068d8c, '0448', literal_value=TEXT)
    exact(0x08068d8e, '9ff7dbfe', kind='call', target=0x08008b48)
    exact(0x08068d92, '0120')
    exact(0x08068d94, '8ff012f8', kind='call', target=MESSAGE & ~1)
    exact(0x080f8908, '004b', literal_value=SPEED, literal_address=0x080f890c)
    exact(0x080f890a, '1847', kind='indirect', register=3)
    need(not any(LO <= at < HI for at in by), '速度命令の再採取禁止')
    rows = []
    for site, font, raw in CALLS:
        exact(site, raw, kind='call', target=BUILDER & ~1)
        exact(site-2, (0x2100|font).to_bytes(2,'little').hex())
        exact(site-4, '0020')
        exact(site-18, '064a' if font==5 else '074a', literal_value=TEXT)
        rows.append({'callsite':site, 'font':font, 'window_id':0, 'text_pointer':TEXT,
                     'predicate':'chooser_low8==0' if font==4 else 'chooser_low8==1' if font==5 else 'chooser_low8 not in (0,1)'})
    for at, raw in ((0x080f7d30,'0a9f'),(0x080f7d32,'0b9c'),(0x080f7d36,'0c9d'),(0x080f7d38,'0d9e'),
                    (0x080f7d44,'0092'),(0x080f7d48,'1071'),(0x080f7d4c,'4171'),
                    (0x080f7d9e,'6846'),(0x080f7da0,'191c'),(0x080f7da2,'3a1c')):
        exact(at,raw)
    exact(0x080f7da4,'0af7a4ff',kind='call',target=0x08002cf0)
    fonts = analysis['selected_fonts']
    need([r['selector'] for r in fonts] == [2,4,5], '選択font集合')
    table=analysis['tables'][0];raw=bytes.fromhex(table['hex'])
    need(table['address']==0x083e30e8 and len(raw)==192 and s.identity(raw)==table['identity'],'font表identity')
    for row in fonts:
        at=row['selector']*12;record=raw[at:at+12]
        need(row['record_address']==table['address']+at and row['hex']==record.hex()
             and row['callback']==int.from_bytes(record[:4],'little')
             and row['runtime_selection_observed'] is False,'callbackの表出自')
    return {'entry':PRODUCER, 'message_entry':MESSAGE, 'builder_entry':BUILDER,
        'text_pointer':TEXT, 'text_capacity_proven':False,
        'message_slot':{'id':0,'address':POOL,'size':32,'full_pool_required_for_message_write':False,
                        'full_pool_required_for_RunTextPrinters':True,'allocation_runtime_observed':False},
        'font_routes':rows, 'callbacks':copy.deepcopy(fonts),
        'new_root':SPEED, 'new_code_window':[LO,HI], 'maximum_new_code_bytes':HI-LO,
        'speed_source':'saved 080F8908 LDR-r3 / BX-r3 literal',
        'initializer_entry':0x080f8a29, 'initializer_entry_reached_from_message':False,
        'gfonts_global':GFONTS, 'runtime_reachability_proven':False,
        'boundary_ja':'caller入口に到達した条件付きdataflow。live gFonts/heap/進行/全文字列容量の観測ではない。'}


def validate_new(result, known):
    need(result['initial_roots'] == [SPEED] and not result['saved_roots_reused'], '新規一根')
    need(result['saved_nodes_redecoded'] == 0 and result['direct_calls_recursively_expanded'] == 0, '旧命令/再帰禁止')
    need(not result['wave_limit_reached'] and not result['deferred_by_wave_limit'], '窓予算')
    nodes = result['new_nodes']; starts = [n['address'] for n in nodes]
    need(0 < len(nodes) <= 22 and starts == sorted(set(starts)) and starts[0] == LO, '新node集合')
    used = set()
    for n in nodes:
        at,size=n['address'],n['size']; span=set(range(at,at+size))
        need(size in (2,4) and at%2==0 and LO<=at<at+size<=HI, '速度code窓境界')
        need(not span & (used|set(known)), '速度code重複'); used |= span
        need(len(bytes.fromhex(n['hex']))==size, '速度node byte長')
        if 'literal_address' in n:
            need(LO<=n['literal_address']<=HI-4, '速度literal窓境界')
    return used


def analyze(previous, out):
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_remaining_frontier as walk
    import pr16_ring_owner_frontier as old
    nodes,memory,context,analysis=saved_inputs(); owner=plan(nodes,analysis)
    paths=tuple(dict.fromkeys((SELF,TEST,WORKFLOW,PRIOR,*SOURCES)))
    preflight={'plan':owner,'source_bindings':{p:s.identity((s.ROOT/p).read_bytes()) for p in paths}}
    (out/'preflight.json').write_bytes(s.stable(preflight))
    missing=[at for at in range(LO,HI) if at not in memory]
    restored=bool(missing)
    if restored:
        restore.OUT=out; restore.restore()
        candidate=s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
        raw=candidate.read_bytes(); saved.candidate_identity(raw)
    else:
        # 保存windowに全byteがある場合、候補の再構築は不要。許可窓だけdecodeする。
        buf=bytearray(s.CANDIDATE['size'])
        for at in range(LO,HI):buf[at-0x08000000]=memory[at]
        raw=bytes(buf)
    def decode(data,at):
        need(LO<=at<=HI-2,'新規速度窓外decode禁止')
        n=decoder.thumb_instruction(data,at)
        need(at+n['size']<=HI, '速度命令窓終端')
        if 'literal_address'in n:need(LO<=n['literal_address']<=HI-4,'速度literal窓外禁止')
        return n
    result=walk.bounded_walk(raw,[SPEED],old.cache_nodes([{'nodes':nodes}]),decode,old.inspect_frontier,
                             max_nodes=22,max_bytes=44,max_roots=2,max_rounds=2)
    points=result.pop('points');validate_new(result,{p for n in nodes for p in range(n['address'],n['address']+n['size'])})
    windows,reused=old.new_windows(raw,points,memory)
    if restored:need(s.identity(candidate.read_bytes())==s.identity(raw),'candidate不変')
    all_nodes=[*nodes,*result['new_nodes']]
    result.update({'classification':'MESSAGE_CALLER_SLOT_AND_FONT_BOUND_NEW_SPEED_BYTES_NOT_NATIVE_ACCEPTANCE',
        'candidate':dict(s.CANDIDATE),'owner_plan':owner,'new_windows':windows,
        'new_node_count':len(result['new_nodes']),'saved_node_count':len(all_nodes),
        'new_window_bytes':sum(w['end']-w['start']for w in windows),'saved_bytes_reused':reused,
        'candidate_reconstructions':int(restored),'rom_changes':0,'new_emulator_processes':0,
        'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,
        'ring_acquisition_accepted':False,'release_ready':False,'all_live_slot_bounds_proven':False,
        'initializer_runtime_observed':False,'actual_callback_table_observed':False,
        'full_rom_scans':0,'speed_behavior_proven':False,
        'boundary_ja':'slot0とfont分岐は保存callerに束縛。新速度byteは次の帰還/設定/不足試験用。実allocationと通常取得は未受入。'})
    files={'saved-context.json':s.stable({'nodes':all_nodes,'analysis':analysis,'inherited_analysis':context,'owner_analysis':result}),
           SELF:(s.ROOT/SELF).read_bytes(), TEST:(s.ROOT/TEST).read_bytes()}
    manifest=export.bundle(files,out/'export')
    result['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    result['export_logical_files']=len(manifest['files'])
    (out/'analysis.json').write_bytes(s.stable(result))
    return result


def summaries(r):
    return (f'message実callerのslot0/font2/4/5供給を束縛。速度delegate0937855Dの新規{r["new_node_count"]}命令/{r["new_window_bytes"]}byteを保存。旧7291命令再解読/native0。',
        '次は保存速度byteとmessage callerを結合し、設定分岐・有効slot書込・callback選択・不足時停止・返却frameを検証する。'
        'initializer到達/heap allocation/通常storyの実観測は未受入。新速度採取/混在333/audio/renderer/BP/nativeは単独再実行しない。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可')
    s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12)
    s.run(sys.modules[__name__])
