"""Stage84: normalize MOVE_NONE's canonical PP sentinel, preserving every real move.

The Stage83 physical forget regression leaves PP=35 in the trailing empty slot.
Native SetMonMoveSlot uses the Stage81 canonical PP table even for MOVE_NONE.
Only the ID-zero sentinel PP byte is changed; no real move balance is altered.
"""
import hashlib
import struct

PARENT_SHA='09e9d8cf085d175299b58e93347e3beb2467c3c09016130f7d35ce033fa50096'
SIZE=33554432
TABLE=0x090421F4
OFFSET=TABLE-0x08000000+4
LITERALS=(69060,69480,254052,254220,263636)

def identity(raw):return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def patch(raw):
    if type(raw) is not bytes or len(raw)!=SIZE:raise ValueError('immutable full ROM required')
    if struct.unpack_from('<I',raw,0x1cc)[0]!=TABLE:raise ValueError('canonical move root differs')
    if any(struct.unpack_from('<I',raw,p)[0]!=TABLE+4 for p in LITERALS):raise ValueError('Stage81 native PP literals differ')
    if raw[OFFSET]!=35:raise ValueError('MOVE_NONE PP preimage is not 35')
    child=raw[:OFFSET]+b'\0'+raw[OFFSET+1:]
    if child[:OFFSET]!=raw[:OFFSET] or child[OFFSET+1:]!=raw[OFFSET+1:] or len(child)!=len(raw):raise ValueError('unrelated ROM changed')
    return child

def build(raw):
    if identity(raw)!={'size':SIZE,'sha256':PARENT_SHA}:raise ValueError('exact Stage83 parent required')
    child=patch(raw)
    report={'schema_version':1,'status':'BUILT_NOT_ACCEPTED','stage':84,'scope':'MOVE_NONE_CANONICAL_PP_SENTINEL_ONLY','parent':identity(raw),'candidate':identity(child),'patch':{'offset':OFFSET,'move_id':0,'field':'pp','before':35,'after':0},'changed_byte_count':1,'real_move_rows_unchanged':True,'p06_stage83_species_rows_unchanged':True,'save_abi_unchanged':True,'active_baseline_changed':False,'full_p03_acceptance':False,'full_p05_acceptance':False,'release_ready':False}
    return child,report
