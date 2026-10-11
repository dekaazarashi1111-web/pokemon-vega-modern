"""新party consumer局所診断。未閉鎖root/lifetimeを分類へ昇格しない。"""
from dataclasses import dataclass
import hashlib
import pr16_dex_hof_donor as d
import pr16_dex_hof_reference_code as code

need, identity, chunk = d.need, d.identity, d.chunk
CANDIDATE = {'size': 33554432, 'sha256': '0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583'}
DIAGNOSTIC = {'size': 33554432, 'sha256': '06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5'}
HIT = 0x08124573
SOURCE_IDS = {
 'BPRJ.ld': (68505, 'e371c23b9c9ea914c9ca3f644983e0b4e05be07bf11054492fa37afcfd58892a', 'cf5363abd8439d63c7bd12cbe83ade861b0ebb51'),
 'pret-party_menu.c': (211085, '8290dfd5b6444e743029ab76543ed5e4b5b32c1c2f475c686946545f934d5f9b', '7f3a881e6c56773aee03da475c9a1adc50530223'),
}
SOURCE_META = {
 'BPRJ.ld': ('kapibarasan000/CFRU-JP','e24a16fe39e27ae162faf5b78596d1f3df18489d','BPRJ.ld'),
 'pret-party_menu.c': ('pret/pokefirered','c75f352304d529f6ba92d4f74b9cf8b5c3810788','src/party_menu.c'),
}
HEAP_CELL, TASKS = 0x0203B010, 0x030050D0
# 意味ごとの独立encoder。命令byteやrawhexを成果物へ複写しない。
@dataclass(frozen=True)
class Ins:
    address: int
    kind: str
    args: tuple
    @property
    def size(self): return 4 if self.kind == 'call' else 2


def block(address, specs):
    rows = []
    for spec in specs:
        row = Ins(address, spec[0], tuple(spec[1:])); rows.append(row); address += row.size
    return rows


BLOCKS = {}
def put(label, address, specs): BLOCKS[label] = block(address, specs)

# Alloc成功時の同一戻り値をpointerセルへ置き、第6引数と空exit fieldを保存する。
put('constructor_entry', 0x0811F24C, [
 ('push', 0xF0, True), ('movhi',7,10), ('movhi',6,9), ('movhi',5,8), ('push',0xE0,False), ('spadd',-4),
 ('spmem',True,4,0x24), ('shift','lsl',0,0,24), ('shift','lsr',0,0,24), ('movhi',9,0),
 ('shift','lsl',1,1,24), ('shift','lsr',1,1,24), ('movhi',10,1), ('shift','lsl',2,2,24), ('shift','lsr',2,2,24), ('movhi',8,2),
 ('shift','lsl',3,3,24), ('shift','lsr',3,3,24), ('spmem',False,3,0), ('shift','lsl',4,4,24), ('shift','lsr',7,4,24),
 ('call',0x0811F6B0), ('literal',6,0x0811F294), ('imm','mov',0,0x8E), ('shift','lsl',0,0,2), ('call',0x08002B9C),
 ('addi',5,0,0), ('mem',False,'word',5,6,0), ('imm','cmp',5,0), ('branch',1,0x0811F298),
 ('spmem',True,0,0x2C), ('call',0x08000544), ('jump',0x0811F388)])
put('constructor_success_fields',0x0811F298,[
 ('literal',3,0x0811F2E8), ('imm','mov',1,15), ('movhi',0,9), ('alu','and',1,0), ('mem',True,'byte',2,3,8),
 ('imm','mov',0,16), ('alu','neg',0,0), ('alu','and',0,2), ('alu','orr',0,1), ('mem',False,'byte',0,3,8),
 ('spmem',True,1,0x2C), ('mem',False,'word',1,3,0), ('imm','mov',4,0), ('movhi',0,8), ('mem',False,'byte',0,3,11),
 ('shift','lsl',2,7,2), ('mem',True,'half',1,5,10), ('imm','mov',0,3), ('alu','and',0,1), ('alu','orr',0,2),
 ('mem',False,'half',0,5,10), ('spmem',True,0,0x28), ('mem',False,'word',0,5,0), ('mem',False,'word',4,5,4)])
put('constructor_callback_tail',0x0811F37E,[('call',0x08040330),('literal',0,0x0811F3A4),('call',0x08000544),
 ('spadd',4),('pop',0x38,False),('movhi',8,3),('movhi',9,4),('movhi',10,5),('pop',0xF0,False),('pop',1,False),('bx',0)])
put('constructor_reset',0x0811F6B0,[('literal',0,0x0811F6C4),('imm','mov',1,0),('mem',False,'word',1,0,0),
 ('literal',0,0x0811F6C8),('mem',False,'word',1,0,0),('literal',0,0x0811F6CC),('mem',False,'word',1,0,0),
 ('literal',0,0x0811F6D0),('mem',False,'word',1,0,0),('bx',14)])
put('init_callback',0x0811F3D8,[('push',0,True),('call',0x080C0918),('shift','lsl',0,0,24),('shift','lsr',0,0,24),('imm','cmp',0,1),('branch',0,0x0811F3FE),
 ('call',0x0811F404),('shift','lsl',0,0,24),('shift','lsr',0,0,24),('imm','cmp',0,1),('branch',0,0x0811F3FE),
 ('call',0x080C08D8),('shift','lsl',0,0,24),('shift','lsr',0,0,24),('imm','cmp',0,1),('branch',1,0x0811F3DA),('pop',1,False),('bx',0)])
put('init_state_selector',0x0811F404,[('push',16,True),('spadd',-4),('literal',0,0x0811F424),('imm','mov',1,0x87),('shift','lsl',1,1,3),
 ('add',0,0,1),('mem',True,'byte',0,0,0),('imm','cmp',0,22),('branch',9,0x0811F418),('jump',0x0811F61C),
 ('shift','lsl',0,0,2),('literal',1,0x0811F428),('add',0,0,1),('mem',True,'word',0,0,0),('movhi',15,0)])
put('state20_task_consumer',0x0811F5BC,[('literal',4,0x0811F5D4),('mem',True,'word',0,4,0),('mem',True,'word',0,0,0),('imm','mov',1,0),('call',0x08076BB4),
 ('mem',True,'word',0,4,0),('mem',True,'half',0,0,10),('shift','lsr',0,0,2),('call',0x081224D8),('jump',0x0811F604)])
put('state_increment',0x0811F604,[('literal',1,0x0811F618),('imm','mov',0,0x87),('shift','lsl',0,0,3),('add',1,1,0),
 ('mem',True,'byte',0,1,0),('imm','add',0,1),('mem',False,'byte',0,1,0),('jump',0x0811F634)])
put('state_default_scheduler_registration',0x0811F61C,[('literal',0,0x0811F62C),('call',0x080006F4),('literal',0,0x0811F630),('call',0x08000544),('imm','mov',0,1),('jump',0x0811F636)])
put('party_scheduler',0x0811F3A8,[('push',0,True),('call',0x08076D10),('call',0x080066D8),('call',0x08006724),('call',0x080F7810),('call',0x0806FC74),('pop',1,False),('bx',0)])
# Mail submenu producer: same taskId in r5, action type9, real scheduler function field0.
put('mail_submenu_producer',0x081244D0,[('push',0x30,True),('addi',5,0,0),('shift','lsl',5,5,24),('shift','lsr',5,5,24),('imm','mov',0,5),('call',0x08071A70),
 ('literal',4,0x08124520),('mem',True,'word',0,4,0),('imm','add',0,12),('call',0x081224B0),('mem',True,'word',0,4,0),('imm','add',0,13),('call',0x081224B0),
 ('literal',0,0x08124524),('literal',1,0x08124528),('mem',True,'byte',1,1,9),('imm','mov',2,9),('call',0x08123178),
 ('imm','mov',0,2),('call',0x08122628),('imm','mov',0,26),('call',0x081224D8),('literal',1,0x0812452C),
 ('shift','lsl',0,5,2),('add',0,0,5),('shift','lsl',0,0,3),('add',0,0,1),('imm','mov',1,255),('mem',False,'half',1,0,8),
 ('literal',1,0x08124530),('mem',False,'word',1,0,0),('pop',0x30,False),('pop',1,False),('bx',0)])
put('actions_producer',0x08123178,[('push',16,True),('shift','lsl',1,1,24),('shift','lsr',1,1,24),('shift','lsl',2,2,24),('shift','lsr',2,2,24),('imm','cmp',2,0),
 ('branch',1,0x0812318C),('call',0x081231D8),('jump',0x081231C4),('literal',4,0x081231CC),('mem',True,'word',1,4,0),('literal',0,0x081231D0),('add',0,2,0),
 ('mem',True,'byte',0,0,0),('mem',False,'byte',0,1,23),('imm','mov',3,0),('mem',True,'word',0,4,0),('mem',True,'byte',0,0,23),('compare',3,0),('branch',2,0x081231C4),
 ('literal',1,0x081231D4),('shift','lsl',0,2,2),('add',2,0,1),('mem',True,'word',1,4,0),('imm','add',1,15),('add',1,1,3),
 ('mem',True,'word',0,2,0),('add',0,0,3),('mem',True,'byte',0,0,0),('mem',False,'byte',0,1,0),('addi',0,3,1),('shift','lsl',0,0,24),('shift','lsr',3,0,24),
 ('mem',True,'word',0,4,0),('mem',True,'byte',0,0,23),('compare',3,0),('branch',3,0x081231A8),('pop',16,False),('pop',1,False),('bx',0)])
put('selection_input_prefix',0x08123438,[('push',0xF0,True),('shift','lsl',0,0,24),('shift','lsr',6,0,24),('literal',0,0x08123470),('mem',True,'byte',1,0,7),
 ('imm','mov',0,128),('alu','and',0,1),('imm','cmp',0,0),('branch',1,0x0812351A),('call',0x080C0918),('shift','lsl',0,0,24),('shift','lsr',0,0,24),
 ('imm','cmp',0,1),('branch',0,0x0812351A),('shift','lsl',0,6,2),('add',0,0,6),('shift','lsl',0,0,3),('literal',1,0x08123474),('add',7,0,1),
 ('literal',0,0x08123478),('mem',True,'word',0,0,0),('mem',True,'byte',0,0,23),('imm','cmp',0,3),('branch',8,0x0812347C),('call',0x08110624),('jump',0x08123480)])
put('selection_large_input',0x0812347C,[('call',0x081105B8)])
put('selection_input_and_cancel_filter',0x08123480,[('shift','lsl',0,0,24),('shift','lsr',5,0,24),('imm','mov',0,0),('signed_load','half',4,7,0),
 ('call',0x081104C0),('shift','lsl',0,0,24),('shift','lsr',0,0,24),('compare',4,0),('branch',0,0x081234AA),('literal',0,0x081234F0),('mem',True,'word',4,0,0),
 ('call',0x081104C0),('shift','lsl',0,0,24),('shift','lsr',0,0,24),('imm','add',4,15),('add',4,4,0),('mem',True,'byte',0,4,0),('call',0x08122904),
 ('call',0x081104C0),('shift','lsl',0,0,24),('shift','lsr',0,0,24),('mem',False,'half',0,7,0),('shift','lsl',0,5,24),('shift','asr',5,0,24),
 ('imm','mov',0,2),('alu','neg',0,0),('compare',5,0),('branch',0,0x0812351A),('imm','add',0,1),('compare',5,0),('branch',1,0x081234F8)])
put('selection_confirm_consumer',0x081234F8,[('literal',4,0x08123520),('mem',True,'word',0,4,0),('imm','add',0,14),('call',0x081224B0),('literal',1,0x08123524),
 ('mem',True,'word',0,4,0),('imm','add',0,15),('add',0,0,5),('mem',True,'byte',0,0,0),('shift','lsl',0,0,3),('imm','add',1,4),('add',0,0,1),
 ('mem',True,'word',1,0,0),('addi',0,6,0),('call',0x081C7ACC),('pop',0xF0,False),('pop',1,False),('bx',0)])
put('read_mail_callback_writer',0x08124534,[('push',16,True),('addi',4,0,0),('shift','lsl',4,4,24),('shift','lsr',4,4,24),('imm','mov',0,5),('call',0x08071A70),
 ('literal',0,0x08124558),('mem',True,'word',1,0,0),('literal',0,0x0812455C),('mem',False,'word',0,1,4),('addi',0,4,0),('call',0x08120268),('pop',16,False),('pop',1,False),('bx',0)])
put('close_menu_same_task',0x08120268,[('push',16,True),('spadd',-4),('addi',4,0,0),('shift','lsl',4,4,24),('shift','lsr',4,4,24),('imm','mov',0,1),('alu','neg',0,0),
 ('imm','mov',1,2),('alu','neg',1,1),('imm','mov',2,0),('spmem',False,2,0),('imm','mov',3,16),('call',0x0806FD2C),('literal',1,0x0812029C),
 ('shift','lsl',0,4,2),('add',0,0,4),('shift','lsl',0,0,3),('add',0,0,1),('literal',1,0x081202A0),('mem',False,'word',1,0,0),('spadd',4),('pop',16,False),('pop',1,False),('bx',0)])
put('close_menu_exit_consumer',0x081202A4,[('push',0x30,True),('shift','lsl',0,0,24),('shift','lsr',5,0,24),('literal',0,0x081202D8),('mem',True,'byte',1,0,7),
 ('imm','mov',0,128),('alu','and',0,1),('imm','cmp',0,0),('branch',1,0x081202F4),('literal',4,0x081202DC),('mem',True,'byte',1,4,8),('imm','mov',0,15),
 ('alu','and',0,1),('imm','cmp',0,1),('branch',1,0x081202C6),('call',0x081289FC),('literal',0,0x081202E0),('mem',True,'word',0,0,0),
 ('mem',True,'word',0,0,4),('imm','cmp',0,0),('branch',0,0x081202E4),('call',0x08000544),('jump',0x081202EA)])
put('close_menu_fallback_and_free',0x081202E4,[('mem',True,'word',0,4,0),('call',0x08000544),('call',0x0811F878),('addi',0,5,0),('call',0x08076CA0),('pop',0x30,False),('pop',1,False),('bx',0)])
put('free_party_allocation',0x0811F878,[('push',0,True),('literal',0,0x0811F8B4),('mem',True,'word',0,0,0),('imm','cmp',0,0),('branch',0,0x0811F886),('call',0x08002BC4)])
put('read_mail_target',0x08124560,[('push',0,True),('literal',0,0x08124594),('imm','mov',1,9),('signed_load','byte',1,0,1),('imm','mov',0,100),('alu','mul',0,1),
 ('literal',1,0x08124598),('add',0,0,1),('imm','mov',1,64),('call',0x0803F354),('literal',2,0x0812459C),('shift','lsl',1,0,3),('add',1,1,0),('shift','lsl',1,1,2),
 ('literal',0,0x081245A0),('add',1,1,0),('mem',True,'word',0,2,0),('add',0,0,1),('literal',1,0x081245A4),('imm','mov',2,1),('call',0x080BFE0C),('pop',1,False),('bx',0)])
put('main_callback_setter',0x08000544,[('literal',1,0x08000554),('mem',False,'word',0,1,4),('imm','mov',0,135),('shift','lsl',0,0,3),('add',1,1,0),('imm','mov',0,0),('mem',False,'byte',0,1,0),('bx',14)])
put('interwork_r1',0x081C7ACC,[('bx',1)])

LITERALS = {
 0x0811F294:HEAP_CELL,0x0811F2E8:0x0203B014,0x0811F3A4:0x0811F3D9,0x0811F6C4:HEAP_CELL,
 0x0811F6C8:0x0203B030,0x0811F6CC:0x0203B028,0x0811F6D0:0x0203B02C,
 0x0811F424:0x03003130,0x0811F428:0x0811F42C,0x0811F47C:0x0811F5BC,0x0811F5D4:HEAP_CELL,
 0x0811F618:0x03003130,0x0811F62C:0x0811F3C5,0x0811F630:0x0811F3A9,
 0x08124520:HEAP_CELL,0x08124524:0x020241E4,0x08124528:0x0203B014,0x0812452C:TASKS,0x08124530:0x08123439,
 0x081231CC:HEAP_CELL,0x081231D0:0x08419EF0,0x081231D4:0x08419EBC,
 0x08123470:0x020379EC,0x08123474:TASKS+8,0x08123478:HEAP_CELL,0x081234F0:HEAP_CELL,
 0x08123520:HEAP_CELL,0x08123524:0x08419DA8,0x08124558:HEAP_CELL,0x0812455C:0x08124561,
 0x0812029C:TASKS,0x081202A0:0x081202A5,0x081202D8:0x020379EC,0x081202DC:0x0203B014,0x081202E0:HEAP_CELL,
 0x0811F8B4:HEAP_CELL,0x08124594:0x0203B014,0x08124598:0x020241E4,0x0812459C:0x03005048,0x081245A0:0x2CD0,0x081245A4:0x081245A9,
 0x08000554:0x03003130,0x08419EE0:0x08419EAF,0x08419DEC:0x08124535,0x08419DDC:0x081244D1,
}
DATA_FIELDS = {'mail_action_count':(0x08419EF9,1,3), 'read_action_id':(0x08419EAF,1,8)}
BLOCKERS = [
 'outer_actual_menu_root_and_installed_hook_path_unproven',
 'all_setup_state_producers_and_success_path_unproven',
 'same_allocation_across_opaque_calls_and_scheduler_lifetime_unproven',
 'selector_input_range_and_mail_menu_entry_reachability_unproven',
]

def encoded(ins):
    k, x, a = ins.kind, ins.args, ins.address
    if k == 'call':
        delta=x[0]-a-4; need(delta%2==0 and -(1<<22)<=delta<(1<<22),'BL range');delta&=(1<<23)-1
        return ((0xF000|(delta>>12)) | ((0xF800|((delta>>1)&2047))<<16)).to_bytes(4,'little')
    if k in ('push','pop'): n=(0xB400 if k=='push' else 0xBC00)|x[0]|(int(x[1])<<8)
    elif k=='spadd':need(x[0]%4==0,'SP alignment');n=0xB000|(0x80 if x[0]<0 else 0)|abs(x[0])//4
    elif k=='spmem':load,reg,offset=x;need(offset%4==0,'SP field alignment');n=(0x9800 if load else 0x9000)|(reg<<8)|(offset//4)
    elif k=='movhi':rd,rs=x;n=0x4600|((rd&8)<<4)|(rs<<3)|(rd&7)
    elif k=='imm':kind,reg,value=x;n={'mov':0x2000,'cmp':0x2800,'add':0x3000,'sub':0x3800}[kind]|(reg<<8)|value
    elif k=='shift':kind,rd,rs,amount=x;n={'lsl':0,'lsr':0x800,'asr':0x1000}[kind]|(amount<<6)|(rs<<3)|rd
    elif k=='alu':kind,rd,rs=x;n=0x4000|({'and':0,'neg':9,'orr':12,'mul':13}[kind]<<6)|(rs<<3)|rd
    elif k=='addi':rd,rs,value=x;n=0x1C00|(value<<6)|(rs<<3)|rd
    elif k=='add':rd,rs,rt=x;n=0x1800|(rt<<6)|(rs<<3)|rd
    elif k=='compare':rn,rm=x;n=0x4280|(rm<<3)|rn
    elif k=='mem':
        load,width,rd,rb,offset=x;scale={'word':4,'half':2,'byte':1}[width];need(offset%scale==0,'field alignment')
        n={'word':0x6000,'half':0x8000,'byte':0x7000}[width]|(0x800 if load else 0)|((offset//scale)<<6)|(rb<<3)|rd
    elif k=='signed_load':width,rd,rb,ro=x;n={'byte':0x5600,'half':0x5E00}[width]|(ro<<6)|(rb<<3)|rd
    elif k=='literal':reg,slot=x;off=slot-((a+4)&~3);need(off%4==0 and 0<=off<=1020,'literal range');n=0x4800|(reg<<8)|(off//4)
    elif k=='branch':cond,target=x;off=target-a-4;need(off%2==0 and -256<=off<=254,'conditional range');n=0xD000|(cond<<8)|((off//2)&255)
    elif k=='jump':off=x[0]-a-4;need(off%2==0 and -2048<=off<=2046,'branch range');n=0xE000|((off//2)&2047)
    elif k=='bx':n=0x4700|(x[0]<<3)
    else: raise ValueError('unhandled semantic instruction')
    return n.to_bytes(2,'little')


def source_proof(review,sources):
    expected_names={'BPRJ.ld','pret-party_menu.c'}
    need(set(review['source_bindings'])==expected_names,'closed new party source roles')
    for name,binding in review['source_bindings'].items():
        need(tuple(binding[k] for k in ('size','sha256','git_blob_sha'))==SOURCE_IDS[name],'independent fixed source identity')
        repository,commit,source=SOURCE_META[name]
        need(tuple(binding[k] for k in ('repository','commit','source'))==(repository,commit,source) and binding['local']==name and binding['url']==f'https://github.com/{repository}/blob/{commit}/{source}', 'fixed source provenance metadata')
        raw=sources[name];need(identity(raw)=={k:binding[k] for k in ('size','sha256')},'whole pinned new party source')
        need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==binding['git_blob_sha'],'whole pinned source Git blob')
    text=sources['pret-party_menu.c'].decode()
    for token in ['static void CursorCB_Read(u8 taskId)','sPartyMenuInternal->exitCallback = CB2_ReadHeldMail;', 'sCursorOptions[sPartyMenuInternal->actions[input]].func(taskId);',
                  'sPartyMenuInternal->task = task;', 'CreateTask(sPartyMenuInternal->task, 0);', 'FreePartyPointers();']:
        need(token in text,'actual pinned party semantic role')
    linker=sources['BPRJ.ld'].decode()
    for token in ['InitPartyMenu = 0x811F24C | 1;', 'CB2_ShowPokemonSummaryScreen = 0x8123554 | 1;', 'FreePartyPointers = 0x811F878 | 1;']:
        need(token in linker,'JP symbols independently distinguish mail and summary')


def check_local(raw,review,sources):
    """局所機械診断のみ。currentでも新TypedRegionを返さない。"""
    need(review['schema_version']==1 and review['required_candidate']==CANDIDATE,'fixed scope candidate')
    need(review['unresolved_obligations']==BLOCKERS,'root/lifetime obligations cannot be removed by manifest')
    need(review['classifications_added']==0 and review['accepted_classifications_changed'] is False and review['donor_eligible'] is False,'no implied acceptance or lease')
    need(review['role']=='party_read_held_mail' and review['mislabel_rejected']=='party_summary','actual held-mail semantics')
    need(review['baseline_counts']=={'classified':728,'unknown':146,'all':874,'songs':133,'assets':50},'unchanged accepted accounting')
    source_proof(review,sources)
    need(set(review['instruction_windows'])==set(BLOCKS),'every local instruction block')
    for label,rows in BLOCKS.items():
        w=review['instruction_windows'][label];need((w['address'],w['size'])==(rows[0].address,sum(i.size for i in rows)),'exact bounded semantic block geometry')
        d.signed(raw,w)
        for ins in rows:need(chunk(raw,ins.address,ins.size)==encoded(ins),'semantic constraint: '+label+' '+ins.kind)
    need(set(review['literal_words'])=={str(a) for a in LITERALS},'all exact pointer roles')
    for a,value in LITERALS.items():
        w=review['literal_words'][str(a)];need((w['address'],w['size'])==(a,4),'literal geometry');d.signed(raw,w)
        need(d.u32(raw,a)==value,'exact pointer role')
    need(set(review['data_fields'])==set(DATA_FIELDS),'closed producer field roles')
    for label,(a,size,value) in DATA_FIELDS.items():
        w=review['data_fields'][label];need((w['address'],w['size'])==(a,size),'selector field geometry');d.signed(raw,w)
        need(int.from_bytes(chunk(raw,a,size),'little')==value,'typed selector field value')
    hit=review['hit'];d.signed(raw,hit);need(hit['address']==HIT and hit['size']==4,'unchanged new unknown hit')
    w=review['minimal_instruction_window'];d.signed(raw,w);need((w['address'],w['size'])==(0x08124572,6),'BL plus LDR complete crossing only')
    need(code.thumb_bl(chunk(raw,0x08124572,4),0x08124572)==0x0803F354,'complete GetMonData BL at new hit')
    import pr16_dex_hof_callback_party_task as task
    task_proof=task.check_local(raw,review['task_evidence'])
    return dict(status='PASS_LOCAL_PARTY_READ_MAIL_CONSUMERS_NOT_ACCEPTED',role='party_read_held_mail',
                semantic_instruction_count=sum(map(len,BLOCKS.values())),instruction_window_count=len(BLOCKS),task=task_proof,
                shared_heap_pointer_cell_address=HEAP_CELL,exit_callback_copied_before_free_locally=True,
                same_allocation_full_lifetime_proven=False,actual_root_proven=False,newly_classified=0,
                unresolved_obligations=list(BLOCKERS),donor_eligible=False,current_acceptance_claimed=False)


def regions(raw,inherited,review,sources,root=None):
    """不完全な局所証拠をcurrent ROM束縛だけで昇格する誤用を拒否。"""
    need(identity(raw)==inherited['candidate']==CANDIDATE,'whole current candidate mandatory')
    check_local(raw,review,sources)
    raise ValueError('party actual root and same-allocation lifetime remain unproven; unknown retained')


def _regions(raw,inherited,review,sources):
    proof=check_local(raw,review,sources)
    original=next(h for h in inherited['hits'] if h['address']==HIT)
    need(not original['accepted'] and not original['owner_candidates'], 'new owner-external unknown only')
    need({k:original[k] for k in ('address','size','sha256')}==review['hit'], 'exact inherited unknown identity')
    need((inherited['classified'],inherited['unclassified'])==(728,146), 'whole accepted728 parent retained')
    task_hit=review['task_evidence']['hit'];other=next(h for h in inherited['hits'] if h['address']==task_hit['address'])
    need(not other['accepted'] and not other['owner_candidates'] and {k:other[k] for k in ('address','size','sha256')}==task_hit, 'exact second inherited owner-external unknown')
    proof.update(status='PASS_LOCAL_PARTY_CALLBACKS_NOT_ACCEPTED',checked_unknown_hits=[HIT,task_hit['address']],diagnostic_only=True)
    return [],proof


def diagnose(raw,review,sources):
    """保存旧原本の実行receiptだけに使う、全体identity込みの診断入口。"""
    actual=identity(raw)
    need(actual in (DIAGNOSTIC,CANDIDATE), 'known diagnostic/current whole input')
    need(review['diagnostic_input']==actual, 'diagnostic metadata matches whole executed input')
    return check_local(raw,review,sources)
