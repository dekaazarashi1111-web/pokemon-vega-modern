#!/usr/bin/env python3
"""保存message生成callerから設定検証・slot0・task割当・font callbackを結合する。"""
from __future__ import annotations
import copy
from dataclasses import dataclass
import functools
import hashlib
import sys
import pr16_ring_message_owner_frontier as prior
import pr16_ring_text_export_recovery as export
import pr16_ring_explicit_text_machine as strict
import pr16_ring_remaining_contracts as config
import pr16_ring_caller_contracts as tasks
import pr16_ring_gate_contracts as gate
import pr16_ring_text_state_contracts as text
import pr16_ring_followup_v2 as s

BASE = '4a41b452f4144091a7816fb6284f18c68e18905e'
SLUG = 'pr16-ring-message-owner-contracts'
TASK = 'PR-P08-7-RING-MESSAGE-OWNER-CONTRACTS'
TITLE = 'message生成から設定検証・slot0書込・task割当とfont callbackを結合'
SELF = 'scripts/pr16_ring_message_owner_contracts.py'
TEST = 'tests/test_pr16_ring_message_owner_contracts.py'
WORKFLOW = '.github/workflows/pr16-ring-message-owner-contracts.yml'
PRIOR = prior.REPORT
REPORT = 'content/modernization/pr16_ring_message_owner_contracts.json'
KEY = 'latest_ring_diagnostic'
MIN_TESTS = 35
EXTRA_CODE = ()
SOURCES = tuple(dict.fromkeys((prior.SELF, *prior.SOURCES, strict.SELF,
    config.SELF, tasks.SELF, gate.SELF, text.SELF)))
NO_REPEAT = ('保存7309命令によるmessage生成→設定検証→slot0→task割当とfont callback結合は保存原本を再利用。'
    '設定byte256値、stack LR由来残留、task満杯/null fontの部分成功を通常story受入へ昇格しない。'
    '次は登録task callback08068C31とその上流実到達・window初期化を限定する。'
    '本工程/速度採取/混在333/音声/renderer/BP/nativeは単独再実行しない。')
need = s.need
b = strict.b
SRC = 0x02002000
CHOOSER = 0x0203700e
SHADOW = 0x0203e400
CONTEXT = 0x02020010
CALLBACK = 0x08068c31
META = config.vm.META
FLAGS = text.TEXT_FLAGS
RESIDUE_AT = b.vm.SP - 58
SAVED_LR = 0x09378dbb
RELEVANT = (0x08068d8e, 0x08068d94, 0x080f7dd8, 0x0937855e,
            0x080f7e00, 0x080f7e30, 0x080f7e58, 0x080f7da4, 0x08068cd2)


@dataclass(frozen=True)
class Case:
    speed: int = 2
    chooser: int = 0
    flags: int = 0
    config_kind: str = 'valid'
    task_layout: str = 'empty'
    null_fonts: bool = False
    full_pool: bool = False
    source: bytes = b'\xff'

    def validate(self):
        need(type(self.speed) is int and 0 <= self.speed < 256, '設定byte u8')
        need(type(self.chooser) is int and 0 <= self.chooser < 65536 and self.chooser != 255, '明示chooser u16/通常fallback別工程')
        need(type(self.flags) is int and 0 <= self.flags < 256, 'flags u8')
        need(type(self.null_fonts) is bool and type(self.full_pool) is bool, 'bool型')
        need(self.config_kind in ('valid', 'bad_crc', 'bad_magic'), 'config種別')
        need(self.task_layout in ('empty', 'front', 'middle', 'tail', 'last', 'full'), 'task layout')
        need(type(self.source) is bytes and 1 <= len(self.source) <= 32
             and self.source[-1] == 255 and all(v < 250 for v in self.source[:-1]), '有限単純文字列')
        return self

    def label(self):
        return f'{self.speed}-{self.chooser}-{self.flags}-{self.config_kind}-{self.task_layout}-{int(self.null_fonts)}-{int(self.full_pool)}-{self.source.hex()}'

    @property
    def font(self):
        return 4 if self.chooser & 255 == 0 else 5 if self.chooser & 255 == 1 else 2

    @property
    def mode(self):
        return 1 if self.config_kind != 'valid' else 127 if self.speed == 0 else 1 if self.speed == 1 else 2


def task_data(layout):
    choices = {'empty': ((), ()), 'front': ((3, 7), (90, 100)),
        'middle': ((5, 2, 9), (20, 80, 100)), 'tail': ((2, 7), (10, 80)),
        'last': (tuple(range(15)), tuple(range(15))),
        'full': (tuple(range(16)), tuple(range(16)))}
    return tasks.task_fixture(*choices[layout])


def config_data(case):
    raw = bytearray(config.validator_data()); raw[28] = case.speed
    raw = bytearray(config.seal(bytes(raw)))
    if case.config_kind == 'bad_crc': raw[8] ^= 1
    if case.config_kind == 'bad_magic': raw[0] = 0
    return bytes(raw)


def table(row, length):
    raw = bytes.fromhex(row['hex']); at = row.get('address', row.get('start'))
    need(type(at) is int and len(raw) == length and s.identity(raw) == row['identity'], '保存表identity')
    return at, raw, False


def fixture(case, analysis, inherited):
    case.validate()
    pool = bytearray([0xa5] * (1024 if case.full_pool else 32))
    for slot in range(1, len(pool)//32): pool[slot*32+27] = 0
    strings = next(r for r in inherited['tables'] if r.get('label') == 'string_dispatch')
    return [(SRC, case.source, False), (prior.TEXT, b'\xcc'*len(case.source), True),
        (FLAGS, b.word(0x78654300 | case.flags), True),
        (CHOOSER, case.chooser.to_bytes(2, 'little'), False),
        (prior.GFONTS, b.word(0 if case.null_fonts else analysis['tables'][0]['address']), False),
        (b.BUFFER, config_data(case), False), (META, config.vm.metadata_expected(), True),
        (SHADOW, b'\xaa'*2048, True), (CONTEXT, b'\xcc'*32, True),
        (prior.POOL, bytes(pool), True), (gate.COMBINATIONS, b'\xcc'*168, True),
        (tasks.TASKS, task_data(case.task_layout), True),
        (text.KEYS+44, bytes(4), False), table(strings, 24),
        *[table(row, length) for row, length in ((analysis['tables'][0],192),
            (analysis['state_table'],28), (analysis['dispatch_tables'][0],32), (analysis['dispatch_tables'][1],24))]]


class Machine(strict.Machine):
    """計算は既存strictのまま。stack残留byteの最後のwriterだけを記録する。"""
    def __init__(self, *args, **kwargs):
        self.stack_provenance = {}
        super().__init__(*args, **kwargs)

    def write(self, at, size, value):
        super().write(at, size, value)
        for address in range(max(at, RESIDUE_AT), min(at+size, RESIDUE_AT+2)):
            self.stack_provenance[address] = {'site': self.last_pc, 'address': at, 'size': size,
                                             'value': value & ((1 << (size*8))-1)}


def expected(case, segments):
    """実traceを読まず、保存callerの供給値と独立した既存効果契約を合成する。"""
    e = b.Expected(segments)
    for i, value in enumerate(case.source): e.write(prior.TEXT+i, 1, value)
    e.write(FLAGS, 1, case.flags | 1)
    e.write(META+35, 1, 0)
    if case.config_kind == 'valid':
        for i, value in enumerate(config_data(case)): e.write(SHADOW+i, 1, value)
        e.write(META+35, 1, 1)
    e.write(FLAGS, 1, (case.flags | 1) & ~2)
    if not case.null_fonts:
        mode = 1 if case.mode == 127 else case.mode
        template = b.word(prior.TEXT) + bytes([0,case.font,6,2,6,2,1,3,0x20,0x31]) + b.word(SAVED_LR)[2:]
        for offset,value in ((27,1),(28,0),(29,mode),(30,0),(31,0),*((i,0) for i in range(26,19,-1))):
            e.write(CONTEXT+offset,1,value)
        for i in range(4): e.write(CONTEXT+i*4,4,int.from_bytes(template[i*4:i*4+4],'little'))
        e.write(CONTEXT+16,4,0)
        for write in gate.expansion((2,1,3))[1]: e.write(*write)
        e.write(CONTEXT+29,1,mode-1)
        for i in range(8): e.write(prior.POOL+i*4,4,e.read(CONTEXT+i*4,4))
    final_tasks, target, writes, order = tasks.created(task_data(case.task_layout), CALLBACK, 80)
    for write in writes: e.write(*write)
    return e, {'allocated': bool(writes), 'slot': target if writes else None, 'order': order,
               'task_callback': CALLBACK, 'priority':80, 'task_image':s.identity(final_tasks)}


def check_result(case, m, e, allocation, fonts):
    need(m.nonstack_writes() == e.writes, '生成callerの順序write')
    need(all(m.mem.get(at) == value for at,value in e.mem.items()), '生成callerの最終object')
    need(m.r[0] == b.vm.RETURN and m.r[13] == b.vm.SP and tuple(m.r[4:12]) == tuple(m.original[4:12]), '上流帰還/SP/r4-r11')
    wanted = {'site':0x093bd9a8,'address':b.vm.SP-60,'size':4,'value':SAVED_LR}
    need(all(m.stack_provenance.get(at) == wanted for at in range(RESIDUE_AT, RESIDUE_AT+2)), 'stack残留LR出自')
    calls = m.call_arguments
    builds = [r for r in calls if r['target'] == prior.BUILDER]
    need(len(builds)==1 and builds[0]['args']==[0,case.font,prior.TEXT,case.mode], '実builder引数')
    gate_call = next(r for r in calls if r['target'] == tasks.GATE)
    need(gate_call['args'][:3]==[b.vm.SP-72,case.mode,0], '実template/速度/null callback')
    create = [r for r in calls if r['target']==tasks.CREATE]
    need(len(create)==1 and create[0]['args'][:2]==[CALLBACK,80], '実task callback/priority')
    need(CALLBACK & ~1 not in m.executed_sites, '登録だけをcallback実行へ昇格しない')
    need(not any((r['callback'] & ~1) in m.executed_sites for r in fonts), '非即時messageはfont未実行')
    need(all(all(at+i in m.writable for i in range(size)) for at,size,_ in m.writes), '明示object外write')
    return {'case':case.label(), 'speed_byte':case.speed, 'chooser':case.chooser, 'font':case.font,
        'config_kind':case.config_kind, 'builder_speed':case.mode, 'task':allocation,
        'null_fonts':case.null_fonts, 'text_slot_written':not case.null_fonts,
        'flags_word':int.from_bytes(m.data(FLAGS,4),'little'),'input_flags':case.flags,
        'pool0_bytes':m.data(prior.POOL,32).hex(),'task_layout':case.task_layout,
        'source_size':len(case.source), 'full_pool':case.full_pool,
        'returned':True, 'return_value':m.r[0], 'return_sp_r4_r11_proven':True,
        'steps':m.steps, 'maximum_stack_bytes':b.vm.SP-m.low_sp,
        'nonstack_write_count':len(e.writes), 'write_sha256':hashlib.sha256(s.stable(e.writes)).hexdigest(),
        'final_object_sha256':e.image(), 'pool0':s.identity(m.data(prior.POOL,32)),
        'calls':[r for r in calls if r['site'] in RELEVANT], 'residue_provenance':wanted,
        'native_observation':False}


def invoke(nodes, segments, entry=prior.PRODUCER, args=(SRC,)):
    m = Machine(nodes, segments, args)
    try: m.run(entry)
    except ValueError as exc: return m, (str(exc), m.last_pc)
    return m, None


def configurations():
    rows = [Case(speed=i) for i in range(256)]
    rows += [Case(speed=sp,chooser=ch) for ch in (1,2,127,254,256,257,258,511,65535) for sp in (0,1,2)]
    rows += [Case(flags=flag,chooser=ch) for flag in (1,2,3,127,128,255) for ch in (0,1,2)]
    rows += [Case(config_kind=kind,speed=sp,chooser=ch) for kind in ('bad_crc','bad_magic') for sp in (0,2,255) for ch in (0,1,2)]
    rows += [Case(task_layout=layout,chooser=ch) for layout in ('front','middle','tail','last','full') for ch in (0,1,2)]
    rows += [Case(null_fonts=True,speed=sp,chooser=ch,task_layout=layout) for sp in (0,2) for ch in (0,1,2) for layout in ('empty','full')]
    rows += [Case(source=b'\x01\x07\xff',speed=sp,chooser=ch) for sp in (0,1,2) for ch in (0,1,2)]
    rows += [Case(full_pool=True,speed=sp,chooser=ch,flags=1) for sp in (0,1,2) for ch in (0,1,2)]
    need(len(rows)==len(set(rows)), '結合条件の重複')
    return tuple(rows)


def snapshot(segments,m):
    return [(at,m.data(at,len(data)),writable) for at,data,writable in segments]


def validate_saved(nodes,a,inherited,owner):
    need(len(nodes)==len({r['address'] for r in nodes})==7309,'保存7309命令')
    need(a['candidate']==s.CANDIDATE and owner['candidate']==s.CANDIDATE,'candidate')
    need(owner['new_node_count']==18 and owner['new_window_bytes']==42,'速度採取原本')
    by={r['address']:r for r in nodes}
    for at,raw in ((0x0937855e,'00f025fc'),(0x0937856c,'7e32'),(0x0937857a,'1000'),
                   (0x093bd9a8,'f7b5'),(0x09378db6,'00f03af8')):
        # callsite/押込LRと速度prefixを変更した証拠は再利用しない。
        need(by[at]['hex']==raw,'保存caller byte '+hex(at))
    need(CALLBACK & ~1 not in by,'登録task callbackは次の未読境界')
    for key in ('ring_acquisition_accepted','release_ready','actual_callback_table_observed','initializer_runtime_observed'):
        need(owner[key] is False, '未受入境界 '+key)
    for row in inherited['tables']:
        need(s.identity(bytes.fromhex(row['hex']))==row['identity'],'継承表hash')


@functools.lru_cache(maxsize=1)
def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    nodes,_,context,a = prior.saved_inputs()
    report=s.load(PRIOR);saved.bindings_fresh(s.ROOT,report['source_bindings'])
    nodes=[*nodes,*report['analysis']['new_nodes']]
    validate_saved(nodes,a,context,report['analysis'])
    return nodes,a,context,report['analysis']


def resource_fixture(inherited):
    row=next(r for r in inherited['tables'] if r['start']==b.engine.TABLE)
    at,raw,_=table(row,32)
    return b.engine.fixture(raw,slot=0,enabled=0,dims=(1,1),source=0x02005000)['segments']


def drain_expected(case, segments):
    e=b.Expected(segments);at=prior.POOL
    e.write(at+20,1,case.font);e.write(at+21,1,128)
    e.write(at+30,1,1 if ((case.flags|1)&4) else int(case.mode==2))
    e.write(at,4,prior.TEXT+1)
    if case.speed==0:e.resource(0,2)
    e.write(at+27,1,0)
    return e


def trim(segments, at, size):
    need(sum(p==at for p,_,_ in segments)==1,'縮小対象一意')
    return [(p,data[:size] if p==at else data,w) for p,data,w in segments]


def check_prefix(label, m, stop, wanted_stop, wanted_fault, full_writes, count, segments):
    need(stop==wanted_stop and m.read_fault==wanted_fault,'不足停止 '+label+' '+str((stop,m.read_fault)))
    writes=list(full_writes[:count]);need(m.nonstack_writes()==writes,'不足前の正確write '+label)
    e=b.Expected(segments)
    for w in writes:e.write(*w)
    need(all(m.mem.get(p)==v for p,v in e.mem.items()),'不足後のobject '+label)
    return {'case':label,'returned':False,'stop':list(stop),'read_fault':m.read_fault,
        'nonstack_write_count':count,'write_sha256':hashlib.sha256(s.stable(writes)).hexdigest(),
        'final_object_sha256':e.image(),'maximum_stack_bytes':b.vm.SP-m.low_sp,
        'return_sp_r4_r11_proven':False,'successful_stub_used':False}


def negative_producer(nodes,a,inherited):
    case=Case(source=b'\x01\x07\xff');segments=fixture(case,a,inherited)
    e,_=expected(case,segments)
    # 保存callerの命令/範囲から固定した停止点。実traceの長さで期待値を短縮しない。
    specs=(
        ('source-terminator',SRC,2,'未map read',0x08008b4e,(SRC+2,1),2),
        ('destination-terminator',prior.TEXT,2,'未許可 write',0x08008c2a,None,2),
        ('chooser',CHOOSER,0,'未map read',0x080ccf94,(CHOOSER,2),4),
        ('config-prefix',b.BUFFER,28,'未map read',0x093bd98e,(b.BUFFER+28,1),5),
        ('config-shadow',SHADOW,2047,'未許可 write',0x093bee16,None,2052),
        ('metadata',META,0,'未map read',0x093bee7a,(META,4),4),
        ('slot-last-word',prior.POOL,31,'未許可 write',0x08002d6e,None,2164),
        ('task-table',tasks.TASKS,39,'未map read',0x08076d66,(tasks.TASKS+44,1),2167),
        ('color-output',gate.COMBINATIONS,167,'未許可 write',0x08002ea0,None,2074),
        ('gfonts-global',prior.GFONTS,0,'未map read',0x08002cfc,(prior.GFONTS,4),2055))
    rows=[];sites=set()
    for label,at,size,error,pc,read,count in specs:
        seg=trim(segments,at,size);m,stop=invoke(nodes,seg)
        fault=None if read is None else dict(address=read[0],size=read[1],site=pc)
        rows.append(check_prefix('producer-short-'+label,m,stop,(error,pc),fault,e.writes,count,seg))
        sites.update(m.executed_sites)
    return rows,sites


def joined_drain(nodes,case,segments,producer,inherited,fonts):
    snapshot_segments=snapshot(segments,producer)+resource_fixture(inherited)
    e=drain_expected(case,snapshot_segments)
    m,stop=invoke(nodes,snapshot_segments,b.RUN,())
    need(stop is None,'生成slotのdrain停止 '+str((stop,m.read_fault)))
    need(m.nonstack_writes()==e.writes and all(m.mem.get(p)==v for p,v in e.mem.items()),'生成slotのdrain効果')
    need(m.r[0]==b.vm.RETURN and m.r[13]==b.vm.SP,'drain帰還')
    selected=next(row['callback'] for row in fonts if row['selector']==case.font)
    need(selected & ~1 in m.executed_sites,'選択fontの実命令を未実行')
    need(all((row['callback']&~1) not in m.executed_sites for row in fonts if row['selector']!=case.font),'他font混入')
    need(CALLBACK&~1 not in m.executed_sites,'task callbackをfont callbackへ読み替えない')
    row={'case':'drain-'+case.label(),'parent_producer':case.label(),'font':case.font,
        'callback':selected,'callback_executed_in_saved_model':True,'native_observation':False,
        'input_pool0':s.identity(producer.data(prior.POOL,32)),'returned':True,
        'return_sp_r4_r11_proven':True,'maximum_stack_bytes':b.vm.SP-m.low_sp,
        'nonstack_write_count':len(e.writes),'write_sha256':hashlib.sha256(s.stable(e.writes)).hexdigest(),
        'final_object_sha256':e.image(),'resource_queue_requests':1 if case.speed==0 else 0,
        'actual_dma_execution':False}
    return row,m,snapshot_segments,e


def negative_drain(nodes,case,snap,expected_writes,a):
    specs=(
        ('only-slot0',prior.POOL,32,0x0937859e,prior.POOL+32+27,1,12),
        ('text',prior.TEXT,0,0x0800580e,prior.TEXT,1,3),
        ('gfonts-global',prior.GFONTS,0,0x08002e54,prior.GFONTS,4,0),
        ('callback-word',a['tables'][0]['address'],case.font*12+3,0x08002e5e,a['tables'][0]['address']+case.font*12,4,0),
        ('keys',text.KEYS+44,0,0x0800579a,text.KEYS+44,2,2),
        ('window-record',b.WINDOWS,0,0x08003f06,b.WINDOWS,4,4))
    rows=[];sites=set()
    for label,at,size,pc,address,width,count in specs:
        seg=trim(snap,at,size);m,stop=invoke(nodes,seg,b.RUN,())
        rows.append(check_prefix('drain-short-'+label,m,stop,('未map read',pc),
            dict(address=address,size=width,site=pc),expected_writes,count,seg))
        sites.update(m.executed_sites)
    return rows,sites


@functools.lru_cache(maxsize=1)
def evaluated():
    nodes,a,inherited,owner=saved_inputs()
    validate_saved(nodes,a,inherited,owner)
    rows=[];drains=[];pending=[];sites=set();negative_drains=[]
    for case in configurations():
        seg=fixture(case,a,inherited);m,stop=invoke(nodes,seg)
        need(stop is None,'生成caller停止 '+case.label()+' '+str((stop,m.read_fault)))
        e,allocation=expected(case,seg)
        rows.append(check_result(case,m,e,allocation,a['selected_fonts']));sites.update(m.executed_sites)
        if case.full_pool:
            r,after,snap,de=joined_drain(nodes,case,seg,m,inherited,a['selected_fonts'])
            drains.append(r);sites.update(after.executed_sites)
            if case.speed==0 and case.chooser==0:
                negative_drains,used=negative_drain(nodes,case,snap,de.writes,a);sites.update(used)
        if case==Case() or case==Case(task_layout='last'):
            snap=snapshot(seg,m);pending_machine,stopped=invoke(nodes,snap,CALLBACK,(allocation['slot'],))
            pending.append(check_prefix('registered-task-pending-'+str(allocation['slot']),pending_machine,
                stopped,('保存node境界で停止',CALLBACK&~1),None,(),0,snap))
    negatives,used=negative_producer(nodes,a,inherited);sites.update(used)
    return {'producer':rows,'drain':drains,'negative_producer':negatives,
        'negative_drain':negative_drains,'pending_task':pending,'executed_sites':sorted(sites)}


def analyze(previous,out):
    nodes,a,inherited,owner=saved_inputs();evaluations=evaluated()
    groups={k:len(v) for k,v in evaluations.items() if k!='executed_sites'}
    need(evaluated.cache_info().misses==1,'結合条件の重複実行禁止')
    speed_cases=evaluations['producer'][:256]
    need([r['speed_byte'] for r in speed_cases]==list(range(256)), '全256設定byte')
    result={'classification':'MESSAGE_PRODUCER_CONFIG_SLOT_TASK_AND_FONT_JOIN_NOT_NATIVE_ACCEPTANCE',
        'candidate':dict(s.CANDIDATE),'saved_node_count':len(nodes),'new_node_count':0,'new_window_bytes':0,
        'contract_cases':sum(groups.values()),'conditional_return_cases':groups['producer']+groups['drain'],
        'pending_stop_cases':groups['negative_producer']+groups['negative_drain']+groups['pending_task'],
        'groups':groups,'maximum_stack_bytes':max(r['maximum_stack_bytes'] for k,v in evaluations.items()
            if k!='executed_sites' for r in v),'config_byte_coverage':list(range(256)),
        'selected_speed_values':sorted(set(r['builder_speed'] for r in evaluations['producer'])),
        'slot0_caller_bound':True,'producer_callee_stubs':0,'stack_residue_injected':False,
        'evaluation_cache_misses':evaluated.cache_info().misses,
        'stack_residue_contract':{'bytes':[0x37,0x09],'origin':'validator PUSH of LR 09378DBB at 093BD9A8',
            'range':[RESIDUE_AT,RESIDUE_AT+2],'live_native_stack_observed':False},
        'task_allocation':{'entry':tasks.CREATE,'callback':CALLBACK,'priority':80,'capacity':16,
            'full_table_allocates':False,'caller_checks_task_failure':False,
            'text_slot_updated_before_allocation':True,'runtime_allocation_observed':False},
        'null_fonts':{'text_slot_written':False,'task_allocation_still_attempted':True},
        'slot_extent':{'message_write_bytes':32,'RunTextPrinters_required_pool_bytes':1024,
            'truncated_pool_stops_after_slot0_effects':True,'all_live_slot_bounds_proven':False},
        'selected_font_callbacks':copy.deepcopy(a['selected_fonts']),
        'pending_registered_task_callback':CALLBACK,'next_work_ja':'登録task08068C31の未読byte/実到達、window初期化と実gFontsを限定する。',
        'actual_callback_table_observed':False,'initializer_runtime_observed':False,'all_live_slot_bounds_proven':False,
        'dma_execution_observed':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'saved_nodes_redecoded':0,
        'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,'full_rom_scans':0,
        'boundary_ja':'保存callerの明示RAM/設定/表を条件とする結合証明。task登録・font選択を通常story到達/heap初期化/画面・音声へ昇格しない。',
        'cases':{k:v for k,v in evaluations.items() if k!='executed_sites'},
        'executed_saved_sites':evaluations['executed_sites']}
    (out/'analysis.json').write_bytes(s.stable(result))
    compact={k:v for k,v in a.items() if k not in ('cases','executed_saved_sites','comparisons')}
    export.bundle({'saved-context.json':s.stable({'nodes':nodes,'analysis':compact,'inherited_analysis':inherited,
        'owner_analysis':owner,'message_summary':{k:v for k,v in result.items() if k not in ('cases','executed_saved_sites')}}),
        SELF:(s.ROOT/SELF).read_bytes(),TEST:(s.ROOT/TEST).read_bytes()},out/'export')
    result['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(result))
    return result


def summaries(r):
    return (f'実message生成callerから設定検証・slot0・task割当・font callbackを{r["contract_cases"]}条件で結合。'
        '設定256値、LR由来stack残留、null font/task満杯/不足時の部分writeを区別。新byte/native/候補復元0。',
        '次は登録task callback08068C31とその上流実到達・window初期化の保存caller/必要byteを限定する。'
        'slot0・task割当は明示RAMでの条件付き証明で、通常story/実gFonts/画面・音声は未観測。'
        '本結合/速度採取/混在333/audio/renderer/BP/nativeは単独再実行しない。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可')
    # unittest importとanalyzeで同じcacheを共有し、全条件の二重実行を防ぐ。
    sys.modules['pr16_ring_message_owner_contracts']=sys.modules[__name__]
    s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12)
    s.run(sys.modules[__name__])
