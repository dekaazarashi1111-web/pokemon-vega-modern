#!/usr/bin/env python3
"""現候補のlegacy seen書込先を検査。領域外ORを正当な差分へ昇格しない。"""
import struct
from pr16_story_rom_metadata import public_metadata
from pr16_story_after_maori import identity
from pr16_story_milestones import require,DiagnosticStop
CANDIDATE=dict(size=33554432,sha256='06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5')
ROOT=0x09575F68
LEGACY_DEX_COUNT=386
PHYSICAL_FLAG_BYTES=52
MIRRORS=(('save2',0x5C),('save1_seen1',0x5F8),('save1_seen2',0x3A18))

def addresses(national):
    require(type(national)is int and 1<=national<=2048,'national_number_range')
    index=(national-1)//8;bit=1<<((national-1)%8)
    return dict(national=national,byte_index=index,bit=bit,stock_physical_capacity=PHYSICAL_FLAG_BYTES*8,physical_in_bounds=index<PHYSICAL_FLAG_BYTES,legacy_species_number=national<=LEGACY_DEX_COUNT,writes=[dict(mirror=name,offset=offset+index,mask=bit)for name,offset in MIRRORS])

def inspect(rom,trainers):
    require(identity(rom)==CANDIDATE,'fixed_candidate_for_seen_abi')
    def raw(at,n):return rom[at-0x08000000:at-0x08000000+n]
    require(struct.unpack('<I',raw(0x080429A0,4))[0]==ROOT,'current_species_national_table')
    # Fixed original GetSetPokedexFlag direct triple setter, not DPE's replacement.
    legacy=[(135289126, 2, '662fb906c0fb671022f9914d6bba12250ea6adfb12dbae81cebb353b3685083e'), (135289128, 2, '146da586036684deee1acba1ae0520a79e7502da8b302dc4b683bd4f88f7c8e1'), (135289140, 2, '08a3e2cbce599d75b970e99c39d71b418e7d1e96af3cbfc300253575a28ccc8c'), (135289168, 4, '1913480be96bee194b5411be8e45e9b51327ca13e69f68720b484aad76d44c85')]
    for at,size,digest in legacy:require(identity(raw(at,size))==dict(size=size,sha256=digest),'known_legacy_seen_setter_required')
    rows=[];bindings=[dict(address=at,size=size,sha256=digest,meaning='retained legacy seen setter; DPE replacement absent')for at,size,digest in legacy]
    bindings.append(dict(address=0x080429A0,size=4,hex=raw(0x080429A0,4).hex(),meaning='active species-to-national root'))
    for trainer in trainers:
        team=[]
        for m in trainer['party']:
            species=m['species'];require(type(species)is int and 1<=species<=2048,'current_trainer_species_bounds')
            at=ROOT+2*(species-1);b=raw(at,2);national=struct.unpack('<H',b)[0]
            bindings.append(dict(address=at,size=2,hex=b.hex(),meaning='active species '+str(species)+' national mapping'))
            row=dict(slot=m['slot'],species=species,level=m['level'],**addresses(national));team.append(row)
        rows.append(dict(trainer_id=trainer['id'],safe_to_complete=all(x['physical_in_bounds']for x in team),party=team))
    return public_metadata(dict(status='BLOCKED_UNSAFE_LEGACY_DEX_SEEN_ABI',candidate=CANDIDATE,legacy_dex_count=LEGACY_DEX_COUNT,physical_capacity=PHYSICAL_FLAG_BYTES*8,trainers=rows,bindings=bindings,rom_modified=False,new_save_created=False,unsafe_writes_executed=False,repair_accepted=False))

def require_safe_party(live,audit):
    tid=live['route']['trainer_id'];rows=[x for x in audit['trainers']if x['trainer_id']==tid]
    require(len(rows)==1,'audited_trainer_required');row=rows[0]
    actual=[(x['species'],x['level'])for x in live['enemy_mons']]
    require(actual==[(x['species'],x['level'])for x in row['party']],'same_actual_four_enemies_as_audit')
    unsafe=[x for x in row['party']if not x['physical_in_bounds']]
    if unsafe:raise DiagnosticStop('unsafe_legacy_dex_seen_target',dict(trainer_id=tid,unsafe_party=unsafe,no_battle_input_sent=True,ordinary_save_permitted=False,repair_required=True))
    return row
