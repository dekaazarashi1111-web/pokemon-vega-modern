#!/usr/bin/env python3
"""保存445命令からvalidator/VACQ/初期化/4書込契約を結合。ROM/nativeは再採取しない。"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import sys
import zlib
import pr16_ring_contract_machine as model
import pr16_ring_remaining_frontier as frontier
import pr16_ring_saved_contracts as vm

BASE='8ffeb8427a35b8569e7ea12c201f508f2c6e6940'
SLUG='pr16-ring-remaining-contracts'
TASK='PR-P08-7-RING-REMAINING-CONTRACTS'
TITLE='version1/VACQ正常継続・初期化・flash byte列の保存契約と未読dataを結合'
SELF='scripts/pr16_ring_remaining_contracts.py'
TEST='tests/test_pr16_ring_remaining_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-remaining-contracts.yml'
PRIOR=frontier.REPORT
REPORT='content/modernization/pr16_ring_remaining_contracts.json'
KEY='latest_ring_diagnostic'
EXTRA_CODE=(model.SELF,)
SOURCES=(model.SELF,frontier.SELF,*frontier.SOURCES)
MIN_TESTS=42
NO_REPEAT=('445保存命令によるversion1/VACQ正常・CRC拒否、version2初期化、flash4byte書込の合成契約を再利用。'
    '既読採取/native/BPを再実行せず、未読6calleeと3data範囲だけを次の有限結合へ渡す。'
    '合成I/O書込を実flash操作やstory到達と同一視しない。')
CTX=0x02001000
INITIALIZE=0x093bde81
FLASH=0x081c27dd
TABLES=(
    {'label':'string_dispatch','start':0x08008b68,'length':24,'count':6,'stride':4,'site':0x08008b60},
    {'label':'v2_rule_records','start':0x093bf9ec,'length':368,'count':23,'stride':16,'site':0x093bdbc6},
    {'label':'v2_counter_limits','start':0x093bfce8,'length':48,'count':6,'stride':8,'site':0x093bdc18})
need=model.need


def seal(data):
    need(type(data)is bytes and len(data)==2048,'VGS長')
    out=bytearray(data);out[8:12]=vm.checksum(data).to_bytes(4,'little');return bytes(out)


def validator_data(block=None):
    data=bytearray(2048);data[:4]=(0x31534756).to_bytes(4,'little')
    data[4:6]=(1).to_bytes(2,'little');data[6:8]=(2048).to_bytes(2,'little')
    if block is not None:
        need(type(block)is bytes and len(block)==240,'VACQ長');data[0x44:0x134]=block
    return seal(bytes(data))


def acquisition(seed):
    need(type(seed)is int and 0<=seed<=255,'seed範囲')
    data=bytearray((i*73+seed)&255 for i in range(240));data[:4]=(0x51434156).to_bytes(4,'little')
    data[4:6]=(1).to_bytes(2,'little');data[6:8]=(240).to_bytes(2,'little')
    data[8:12]=bytes(4);data[8:12]=zlib.crc32(data).to_bytes(4,'little');return bytes(data)


def initialized_data(arg):
    need(type(arg)is int and 0<=arg<=0xffffffff,'r1範囲')
    data=bytearray(2048);data[:4]=(0x31534756).to_bytes(4,'little')
    data[4:6]=(2).to_bytes(2,'little');data[6:8]=(2048).to_bytes(2,'little')
    data[29]=1;data[30]=int(arg!=0)
    for offset,value in ((0x73f,1),(0x740,64),(0x745,1),(0x763,1)):data[offset]=value
    return seal(bytes(data))


def effects(machine,label):
    writes=machine.nonstack_writes();points=sorted({at+i for at,size,_ in writes for i in range(size)})
    ranges=[]
    for at in points:
        if ranges and ranges[-1][1]==at:ranges[-1][1]+=1
        else:ranges.append([at,at+1])
    return {'case':label,'return_r0':machine.r[0],'steps':machine.steps,
        'maximum_stack_bytes':vm.SP-machine.low_sp,'nonstack_write_count':len(writes),
        'nonstack_write_ranges':ranges,'sp_and_r4_r11_restored':True,'synthetic_only':True}


def saved_nodes(prior):
    import pr16_ring_followup_v2 as s
    import pr16_ring_effective_frontier as f
    import pr16_ring_owner_frontier as old
    import pr16_ring_flagset_continuation as saved
    reports={p:s.load(p) for p in (*f.REPORTS,f.REPORT)}
    for report in reports.values():saved.bindings_fresh(s.ROOT,report['source_bindings'])
    graphs=[*reports[f.PATCH]['frontier']['graphs'],*reports[f.TRANSITIVE]['native_owners'].values(),
        *(reports[p]['analysis']['graph'] for p in f.SAMPLES),
        *({'nodes':reports[p]['analysis']['new_nodes']} for p in (f.OLD,f.REPORT)),
        {'nodes':prior['analysis']['new_nodes']}]
    return list(old.cache_nodes(graphs).values())


def verify(nodes,prior):
    mapping=vm.flow.node_map(nodes);rows=[]
    def validate(label,data,expected):
        machine=model.Machine(nodes,[(CTX,data,False)],(CTX,2048)).run(vm.VALIDATE)
        need(machine.r[0]==expected and not machine.nonstack_writes(),'validator契約 '+label)
        row=effects(machine,label);row['input_sha256']=hashlib.sha256(data).hexdigest();rows.append(row)
    validate('v1-empty-acquisition-normal',validator_data(),0)
    for seed in (0,1,17,255):validate('v1-vacq-crc-normal-'+str(seed),validator_data(acquisition(seed)),0)
    for label,offset,value in (('magic',0,0),('version',4,2),('length-short',6,239),('length-long',6,241),('crc',8,255)):
        block=bytearray(acquisition(17))
        if label=='crc':block[offset]^=1
        else:block[offset]=value
        validate('v1-vacq-reject-'+label,validator_data(bytes(block)),15)
    init_rows=[]
    for arg in (0,1,2,127,128,255,256,65535,0x80000000,0xffffffff):
        machine=model.Machine(nodes,[(CTX,bytes([0xcc])*2048,True)],(CTX,arg)).run(INITIALIZE)
        need(machine.data(CTX,2048)==initialized_data(arg),'version2初期値差分')
        row=effects(machine,'initialize-'+hex(arg));need(row['nonstack_write_ranges']==[[CTX,CTX+2048]],'初期化範囲')
        need(row['nonstack_write_count']==2139,'初期化書込列件数');init_rows.append(row)
    null=model.Machine(nodes,[],(0,1)).run(INITIALIZE)
    need(not null.nonstack_writes(),'null初期化write');init_rows.append(effects(null,'initialize-null'))
    flash_rows=[]
    io=(0x0e000000,0x0e002aaa,0x0e005555)
    for arg in (*range(256),0x100,0x80000000,0xffffffff):
        machine=model.Machine(nodes,[(at,b'\0',True) for at in io],(arg,)).run(FLASH)
        want=[(0x0e005555,1,0xaa),(0x0e002aaa,1,0x55),(0x0e005555,1,0xb0),(0x0e000000,1,arg&255)]
        need(machine.nonstack_writes()==want and machine.r[0]==arg&255,'4byte I/O契約')
        flash_rows.append(effects(machine,'flash-byte-sequence-'+hex(arg)))
    stops=[]
    for arg in (0,1):
        machine=model.Machine(nodes,[(CTX,initialized_data(arg),False)],(CTX,2048))
        try:machine.run(vm.VALIDATE)
        except ValueError as exc:
            need(str(exc)=='未map read' and machine.read_fault=={'address':0x093bf9f6,'size':1,'site':0x093bdbc6},'v2停止差分')
        else:raise ValueError('未読v2表を推測して通過')
        stops.append({'case':'v2-canonical-'+str(arg),'read_fault':machine.read_fault,'steps':machine.steps,
            'return_proven':False,'sp_and_r4_r11_restored':False,'nonstack_write_count':len(machine.nonstack_writes())})
    for at in (vm.BUFFER,vm.BACKUP):
        machine=model.Machine(nodes,[(at,validator_data(),False),(vm.META,vm.metadata_expected(),True)],(at,2048))
        try:machine.run(vm.VALIDATE)
        except ValueError as exc:need(str(exc)=='保存node境界で停止' and machine.last_pc==0x093bee0a,'owner copy停止差分')
        else:raise ValueError('未読copyを推測して通過')
        need(machine.r[:3]==[0x0203e400,at,2048],'backup copy引数')
        stops.append({'case':'v1-owner-buffer-'+hex(at),'stopped_at':machine.last_pc,'arguments':machine.r[:3],
            'return_proven':False,'nonstack_writes':machine.nonstack_writes()})
    for index in range(6):
        machine=model.Machine(nodes,[(CTX,bytes(64),True),(CTX+128,bytes([250+index,255]),False)],(CTX,CTX+128))
        try:machine.run(0x08008b49)
        except ValueError as exc:
            need(str(exc)=='未map read' and machine.read_fault=={'address':0x08008b68+index*4,'size':4,'site':0x08008b60},'string表境界')
        else:raise ValueError('未読string表を推測して通過')
        stops.append({'case':'string-control-'+str(250+index),'read_fault':machine.read_fault,'return_proven':False})
    bindings=[]
    for entry in (0x08068ccd,0x080f7dbd):
        flow=vm.flow.contexts({'entry':entry,'nodes':nodes})
        bindings.append({'entry':entry,'calls':[{'site':at,'target':c['target'],
            'arguments':{f'r{i}':vm.flow.show(c['registers'][i]) for i in range(4)},
            'unproven_prior_callee_requirements':sorted(c['requirements'])} for at,c in sorted(flow['calls'].items())],
            'stops':flow['stops'],'runtime_reachable':False,'return_proven':False})
    need(bindings[0]['calls'][0]['arguments']['r0']=='0x08068C31'
         and bindings[0]['calls'][0]['arguments']['r1']=='0x00000050','callback/priority結合')
    # data範囲は保存literal + loop定数から限定。未読data値を補完しない。
    for at,want in ((0x08008b5c,0x08008b68),(0x093bdbc2,0x093bf9f6),
                    (0x093bdc0a,0x093bfce8),(0x093bdc36,0x093bf9ec)):
        need(mapping[at]['literal_value']==want,'data pointer結合')
    return {'validator_v1_cases':rows,'initializer_cases':init_rows,'flash_cases':flash_rows,
        'synthetic_contract_cases':len(rows)+len(init_rows)+len(flash_rows),
        'initializer_layout':{'version':2,'marker_offset':29,'boolean_offset':30,'bytes_written_union':2048},
        'vacq_crc':{'start':0x44,'length':240,'zeroed_crc_slot':[8,12],'oracle':'zlib.crc32'},
        'limited_prefix_stops':stops,'callsite_bindings':bindings,
        'pending_direct_callees':copy.deepcopy(prior['pending_direct_callees']),
        'pending_data_ranges':copy.deepcopy(TABLES),'pending_continuations':[],
        'validator_v1_external_buffer_return_proven':True,'validator_v2_normal_return_proven':False,
        'validator_live_buffer_return_proven':False,'all_live_frames_proven':False,
        'all_callers_resolved':False,'all_runtime_owners_excluded':False,'caller_pointer_size_limit_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':0,'new_byte_samples':0,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,
        'preconditions':['保存命令と非alias合成buffer/stack、明示mapされた合成I/Oだけ',
            'ARMv4 MULの未定義C/V依存は停止。未知命令/未map/間接先の推測なし',
            '合成returnとnative到達・実周辺機器・正規story取得は別の受入条件']}


def analyze(prior,out):
    import pr16_ring_followup_v2 as s
    nodes=saved_nodes(prior);result=verify(nodes,prior['analysis'])
    result.update({'classification':'SAVED_REMAINING_ABI_AND_DATA_BOUNDARIES_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'saved_node_count':len(nodes)})
    (out/'analysis.json').write_bytes(s.stable(result))
    (out/'development-source.json').write_bytes(s.stable({p:(s.ROOT/p).read_text(encoding='utf-8')
        for p in (SELF,TEST,model.SELF,frontier.SELF,vm.SELF,vm.flow.SELF)}))
    (out/'saved-context.json').write_bytes(s.stable({'nodes':nodes,'analysis':result}))
    return result


def summaries(result):
    return (f'保存{result["saved_node_count"]}命令を結合し{result["synthetic_contract_cases"]}新規合成契約。'
        'v1外部buffer/VACQ正常とCRC拒否、v2初期化、4byte I/O列を検証。ROM/native再採取0。',
        '残る6calleeとstring6要素表・v2規則23件/上限6件の3data範囲だけを有限採取して保存結合する。'
        'v2正常return、実buffer copy、string分岐、callback/wait帰還を次に検証。'
        '既読採取/単独ABI/BPを再実行せず、Ring正規story取得・装備実戦・保存とpolicy/Circus/P08は未受入。')


if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
