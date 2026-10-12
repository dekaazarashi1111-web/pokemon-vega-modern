#!/usr/bin/env python3
"""根付きM4A command/Voice/Waveの型監査。donor容量の使用権限は発行しない。"""
from __future__ import annotations
import collections
import copy
import hashlib
import io
import json
import re
import struct
import wave
from dataclasses import dataclass
from pathlib import Path
import pr16_dex_hof_donor as prior
BASE=prior.BASE
need,identity,chunk,u32,contains=prior.need,prior.identity,prior.chunk,prior.u32,prior.contains
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=dict(size=33554432,sha256='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583')
SCALARS={0xBA,0xBB,0xBC,0xBD,0xBE,0xBF,0xC0,0xC1,0xC2,0xC3,0xC4,0xC5,0xC8}
CLOCK=tuple(range(25))+(28,30,32,36,40,42,44,48,52,54,56,60,64,66,68,72,76,78,80,84,88,90,92,96)


def window(raw,address,size):
    return dict(address=address,**identity(chunk(raw,address,size)))


def data_pointer(raw,address,alignment=4):
    """DataではThumb bitを消さず、未対応mirrorも暗黙canonical化しない。"""
    need(type(address) is int and BASE<=address<BASE+len(raw) and address%alignment==0,
         'bounded aligned data/command pointer')
    return address


def source_song_ids(text):
    """無条件の明示IDだけ。条件付きUNBOUND、別名式、random sentinelを推定しない。"""
    ids=collections.defaultdict(list); depth=0
    for number,line in enumerate(text.splitlines(),1):
        line=line.split('//',1)[0]
        if re.match(r'\s*#\s*if(?:def|ndef)?\b',line): depth+=1;continue
        if re.match(r'\s*#\s*endif\b',line): need(depth>0,'balanced source conditionals');depth-=1;continue
        match=re.fullmatch(r'\s*#define\s+([A-Z][A-Z0-9_]*)\s+(0x[0-9A-Fa-f]+|[0-9]+)\s*',line)
        if depth or not match: continue
        name,value=match.groups();value=int(value,0)
        if value==0xFEFE: continue
        need(0<=value<=65535,'u16 song source ID');ids[value].append(dict(name=name,line=number))
    need(depth==0 and ids,'closed explicit song ID source')
    # Fixed songs generator explicitly replaces these two entries.
    for sid,name in ((250,'sand_footstep'),(251,'grass_footstep')):
        ids[sid].append(dict(name=name,source='songs'))
    return dict(sorted(ids.items()))


@dataclass(frozen=True)
class TrackState:
    pc:int
    running:int=0
    voice:int=-1
    key:int=0
    velocity:int=0
    repeat:int=0
    stack:tuple=()
    keyshift:int=0


class Unsupported(ValueError):
    pass


class Reader:
    def __init__(self,raw): self.raw=raw;self.roles={};self.structures={}
    def structure(self,address,size,role):
        out=chunk(self.raw,address,size);self.structures[(address,size,role)]=window(self.raw,address,size);return out
    def read(self,address,size,role):
        out=chunk(self.raw,address,size)
        for a in range(address,address+size):
            previous=self.roles.setdefault(a,(address,size,role))
            need(previous==(address,size,role),'overlapping command interpretations')
        return out
    def byte(self,address,role): return self.read(address,1,role)[0]
    def peek(self,address): return chunk(self.raw,address,1)[0]
    def target(self,address,role):
        return data_pointer(self.raw,int.from_bytes(self.read(address,4,role),'little'),1)
    def windows(self):
        addresses=sorted(self.roles); spans=[]
        for a in addresses:
            if spans and spans[-1][1]==a: spans[-1][1]+=1
            else:spans.append([a,a+1])
        return [window(self.raw,a,b-a)for a,b in spans]


def trace_track(raw,root,group,reader=None,max_steps=200000):
    """外部変更なしの確定的command型走査。実演奏・channel確保の証明ではない。"""
    reader=reader or Reader(raw);data_pointer(raw,root,1);data_pointer(raw,group)
    state=TrackState(root);seen={};notes=[];steps=0;elapsed=0;commands=collections.Counter()
    while True:
        if state in seen:
            if elapsed==seen[state]: raise Unsupported('non-yielding cycle can starve later tracks')
            return dict(status='CLOSED_YIELDING_STATE_CYCLE',notes=notes,steps=steps,commands=dict(commands),reader=reader)
        need(steps<max_steps,'command state budget exhausted')
        seen[state]=elapsed;steps+=1
        pc=state.pc;first=reader.peek(pc); running=state.running
        if first>=0x80:
            opcode=reader.byte(pc,'opcode');pc+=1
            if opcode>=0xBD:running=opcode
        else:
            opcode=running
            if not 0xBD<=opcode<=0xFF: raise Unsupported('unset or unsupported running status')
        commands[hex(opcode)]+=1
        d=dict(pc=pc,running=running,voice=state.voice,key=state.key,velocity=state.velocity,
               repeat=state.repeat,stack=state.stack,keyshift=state.keyshift)
        if 0x80<=opcode<=0xB0:
            elapsed+=CLOCK[opcode-0x80]
        elif opcode==0xB1:
            return dict(status='FINE',notes=notes,steps=steps,commands=dict(commands),reader=reader)
        elif opcode in (0xB2,0xB3):
            if opcode==0xB3 and len(state.stack)==3:
                return dict(status='FOURTH_PATTERN_TERMINATES',notes=notes,steps=steps,commands=dict(commands),reader=reader)
            target=reader.target(pc,'control-target')
            if opcode==0xB3:d['stack']=state.stack+(pc+4,)
            d['pc']=target
        elif opcode==0xB4:
            if state.stack:d['pc']=state.stack[-1];d['stack']=state.stack[:-1]
        elif opcode==0xB5:
            count=reader.byte(pc,'repeat-count');target=reader.target(pc+1,'control-target');repeated=state.repeat+1
            if count==0:d['pc']=target
            elif repeated<count:d['repeat']=repeated;d['pc']=target
            else:d['repeat']=0;d['pc']=pc+5
        elif opcode in SCALARS:
            value=reader.byte(pc,'scalar-operand');d['pc']=pc+1
            if opcode==0xBB and value==0:raise Unsupported('shared zero tempo may stop future ticks')
            if opcode==0xBD:d['voice']=group+12*value;reader.structure(d['voice'],12,'voice-copy')
            if opcode==0xBC:d['keyshift']=value-256 if value>=128 else value
        elif opcode==0xCC:
            # PORT can modify sound IO and is unnecessary for proving sample schemas.
            raise Unsupported('PORT external hardware mutation is not modeled')
        elif opcode in (0xB9,0xCD):
            raise Unsupported('MEMACC shared memory / XCMD mutable tone is not modeled')
        elif opcode==0xCE:
            if reader.peek(pc)<0x80:d['key']=reader.byte(pc,'eot-key');d['pc']=pc+1
        elif 0xCF<=opcode<=0xFF:
            gate=CLOCK[opcode-0xCF]
            for field in ('key','velocity','extra_gate'):
                if reader.peek(pc)>=0x80:break
                value=reader.byte(pc,'note-'+field);pc+=1
                if field=='extra_gate':gate=(gate+value)&255
                else:d[field]=value
            d['pc']=pc
            # Default type=1 has no WaveData; do not fabricate VOICE0.
            if d['voice']!=-1:
                note=dict(command=state.pc,voice_address=d['voice'],key=d['key'],velocity=d['velocity'],gate=gate,keyshift=d['keyshift'])
                note_structure(reader,note);notes.append(note)
        else:raise Unsupported('unmodeled effective command slot '+hex(opcode))
        state=TrackState(**d)


def note_structure(reader,note):
    raw=reader.raw;address=note['voice_address'];data_pointer(raw,address)
    parent=reader.structure(address,12,'parent-tone');selected=address
    if parent[0]&0xC0:
        key=note['key']
        if parent[0]&0x40:
            keysite=data_pointer(raw,int.from_bytes(parent[8:12],'little'),1)+key
            key=reader.structure(keysite,1,'key-map')[0]
        selected=data_pointer(raw,int.from_bytes(parent[4:8],'little'))+12*key
        tone=reader.structure(selected,12,'child-tone')
    else:tone=parent
    if tone[0]&0xC7==0:
        address=data_pointer(raw,int.from_bytes(tone[4:8],'little'));reader.structure(address,16,'wave-header')


def select_tone(raw,note):
    address=note['voice_address'];data_pointer(raw,address)
    parent=chunk(raw,address,12);typ=parent[0];selected=address
    evidence=dict(parent=window(raw,address,12),unshifted_key=note['key'],keyshift=note['keyshift'])
    if typ&0xC0:
        if typ&0x40:
            keys=data_pointer(raw,int.from_bytes(parent[8:12],'little'),1);where=keys+note['key']
            index=chunk(raw,where,1)[0];evidence['key_map_byte']=window(raw,where,1)
        else:index=note['key']
        base=data_pointer(raw,int.from_bytes(parent[4:8],'little'));selected=base+12*index
        evidence.update(child_index=index,child=window(raw,selected,12))
    tone=chunk(raw,selected,12)
    need(tone[0]&0xC0==0,'one-level split/rhythm: nested selected group rejected')
    need((tone[0]&7)<=4,'unsupported CGB channel type can exceed four initialized channels')
    if tone[0]&7:raise Unsupported('selected CGB tone has no direct-sound WaveData')
    address=data_pointer(raw,int.from_bytes(tone[4:8],'little'))
    evidence.update(selected=window(raw,selected,12),pointer_field=window(raw,selected+4,4),tone_type=tone[0],wave_address=address)
    return address,tone[0],evidence


def song_regions(raw,ids,engine,hits,footsteps=None):
    table=engine['song_table'];mplayers=engine['mplay_table']; capacities=engine['player_capacities']
    regions={};songs=[];diagnostics=[];waves={};protected={}
    def protect(address,size,role):
        if size>0:protected[(address,size,role)]=window(raw,address,size)
    for w in engine.get('proof',{}).get('windows',[]):protect(w['address'],w['size'],'engine')
    for sid,names in ids.items():
        reader=None
        try:
            site=table+8*sid;protect(site,8,'song-row');header,player,end_player=struct.unpack('<IHH',chunk(raw,site,8))
            need(player in range(len(capacities)),'selected rooted music player index')
            protect(site,8,'song-row');data_pointer(raw,header);count=chunk(raw,header,1)[0];used=min(count,capacities[player]);need(used<=16,'MPlayOpen clamped capacity')
            row=dict(id=sid,source_names=names,song_row=window(raw,site,8),header=window(raw,header,8+4*used),
                     player_row=window(raw,mplayers+12*player,12),declared_tracks=count,consumed_tracks=used)
            protect(header,8+4*used,'song-header');protect(mplayers+12*player,12,'player-row')
            group=u32(raw,header+4);reader=Reader(raw);traces=[];local=[]
            for track in range(used):
                start=u32(raw,header+8+track*4);trace=trace_track(raw,start,group,reader)
                trace_notes=trace.pop('notes');trace.pop('reader');traces.append(dict(index=track,root=start,**trace))
                for note in trace_notes:
                    try:
                        protect(note['voice_address'],12,'parent-tone')
                        # Protect every accessed child/key-map even when selected type is unsupported.
                        parent=chunk(raw,note['voice_address'],12)
                        if parent[0]&0xC0:
                            key=note['key']
                            if parent[0]&0x40:
                                keysite=data_pointer(raw,int.from_bytes(parent[8:12],'little'),1)+key
                                protect(keysite,1,'key-map');key=chunk(raw,keysite,1)[0]
                            child=data_pointer(raw,int.from_bytes(parent[4:8],'little'))+12*key
                            protect(child,12,'child-tone')
                        address,typ,evidence=select_tone(raw,note)
                        protect(address,16,'wave-header')
                        if address not in waves:
                            encoded,decoded,kind=prior.wave_asset(raw,address)
                            # A typed sample prefix is not a complete runtime read footprint.
                            need(address+len(encoded)<=prior.DONOR_LO or prior.DONOR_HI<=address,'declared wave overlaps donor')
                            waves[address]=(encoded,decoded,kind)
                        encoded,decoded,kind=waves[address]
                        need((kind=='dpcm4'and bool(typ&0x30)) or kind=='pcm8',
                             'selected tone and WaveData codec path disagree')
                        witness=dict(song=sid,track=track,note=dict(command=note['command'],key=note['key']),**evidence)
                        if footsteps is not None and sid in (250,251):
                            expected=footsteps[sid]
                            source_match=(group==0x084539B4 and note['voice_address']==group+12*expected['voice'] and note['key']==60 and kind=='pcm8'and decoded==expected['pcm'])
                            witness['source_footstep_match']=source_match
                            if source_match:witness['source_exact_wav']=expected['source_identity']
                        local.append((address,encoded,decoded,kind,witness))
                    except Unsupported as exc:
                        diagnostic=dict(song=sid,track=track,voice_address=note['voice_address'],reason=str(exc),scope='unsupported_selected_tone')
                        if diagnostic not in diagnostics:diagnostics.append(diagnostic)
            row['tracks']=traces;row['command_windows']=reader.windows();songs.append(row)
            # Only complete modeled songs contribute new exclusions. No partial track promotion.
            for address,encoded,decoded,kind,witness in local:
                if not any(contains(address+16,address+len(encoded),hit['address'],hit['size'])for hit in hits):continue
                key=(address,len(encoded),kind)
                if key not in regions:
                    evidence=dict(asset=window(raw,address,len(encoded)),header=window(raw,address,16),decoded=identity(decoded),codec=kind,
                                  minimal_encoded_prefix_only=True,complete_runtime_read_footprint_claimed=False,consumers=[])
                    regions[key]=prior.TypedRegion(address+16,address+len(encoded),kind,evidence)
                # Retain every independently validated consumer chain but collapse repeated identical notes.
                consumers=regions[key].evidence['consumers']
                command=witness.pop('note')['command']
                found=next((c for c in consumers if {k:v for k,v in c.items()if k!='commands'}==witness),None)
                if found is None:consumers.append(dict(**witness,commands=[command]))
                elif command not in found['commands']:found['commands'].append(command)
        except (ValueError,IndexError) as exc:
            diagnostics.append(dict(song=sid,reason=str(exc),scope='whole_song_rejected'))
        finally:
            if reader is not None:
                for (a,z,role),w in reader.structures.items():protect(a,z,role)
                for w in reader.windows():protect(w['address'],w['size'],'command')
    accepted=[]
    for region in regions.values():
        conflicts=[dict(role=role,**w)for (a,z,role),w in protected.items()if a<region.end and region.start<a+z]
        if conflicts:diagnostics.append(dict(scope='conflicting_sample_role',asset=region.evidence['asset'],conflicts=conflicts))
        else:accepted.append(region)
    return accepted,songs,diagnostics


def midi_events(raw):
    """固定footstep原本の全chunk境界とMIDI eventを独立解読する。"""
    need(raw[:4]==b'MThd' and int.from_bytes(raw[4:8],'big')==6,'MIDI header extent')
    format_,count,division=struct.unpack('>HHH',raw[8:14]);need(format_ in(0,1) and count>0 and 0<division<0x8000,'supported MIDI header')
    cursor=14;tracks=[]
    for _ in range(count):
        need(raw[cursor:cursor+4]==b'MTrk','MIDI track tag');size=int.from_bytes(raw[cursor+4:cursor+8],'big');cursor+=8
        end=cursor+size;need(end<=len(raw),'MIDI track bounded');running=0;tick=0;events=[];ended=False
        def vlq():
            nonlocal cursor
            value=0
            for _ in range(4):
                need(cursor<end,'bounded MIDI VLQ');b=raw[cursor];cursor+=1;value=(value<<7)|(b&127)
                if b<128:return value
            raise ValueError('MIDI VLQ overflow')
        while cursor<end:
            tick+=vlq();need(cursor<end,'MIDI status present');status=raw[cursor]
            if status>=128:cursor+=1
            else:status=running
            if status==255:
                need(cursor<end,'MIDI meta type');typ=raw[cursor];cursor+=1;n=vlq();need(cursor+n<=end,'MIDI meta bounded');cursor+=n
                events.append(dict(tick=tick,meta=typ,length=n));running=0
                if typ==47:need(n==0 and cursor==end,'MIDI end-of-track exact');ended=True
            elif status in (240,247):
                n=vlq();need(cursor+n<=end,'MIDI SysEx bounded');cursor+=n;running=0
            else:
                need(128<=status<240,'MIDI channel running status');running=status;kind=status>>4;n=1 if kind in(12,13)else 2
                need(cursor+n<=end and all(x<128 for x in raw[cursor:cursor+n]),'MIDI channel operands')
                values=list(raw[cursor:cursor+n]);cursor+=n
                events.append(dict(tick=tick,event={8:'note_off',9:'note_on',12:'program'}.get(kind,'channel_'+str(kind)),channel=status&15,values=values))
        need(cursor==end and ended,'complete MIDI track with terminator');tracks.append(events)
    need(cursor==len(raw),'no trailing MIDI bytes')
    return dict(format=format_,track_count=count,division=division,tracks=tracks)


def verify_sources(directory,manifest,source_lock):
    """固定上流blob全文をSHAとGit object hash両方で確認。ROM/sourceを混同しない。"""
    roots={r['name']:r for r in source_lock['sources']}
    need(roots['cfru']['resolved_commit']=='e24a16fe39e27ae162faf5b78596d1f3df18489d','fixed CFRU source lock')
    need(any(r.get('resolved_commit')=='c75f352304d529f6ba92d4f74b9cf8b5c3810788'for r in roots.values()),'fixed pret source lock')
    contents={};bindings={}
    for row in manifest:
        path=Path(directory)/row['local'];need(path.is_file()and not path.is_symlink(),'regular pinned public source')
        raw=path.read_bytes();need(identity(raw)=={k:row[k]for k in('size','sha256')},'pinned source SHA drift '+row['local'])
        need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_blob_sha'],'pinned Git blob drift '+row['local'])
        contents[row['local']]=raw;bindings[row['local']]={k:row[k]for k in('repository','commit','source','git_blob_sha','size','sha256')}
    return contents,bindings


def footstep_sources(sources):
    result={}
    for sid,kind,voice,rate,frames in((250,'sand',14,12050,1562),(251,'grass',13,16000,4342)):
        midi=sources[kind+'_footstep.mid'];events=midi_events(midi);programs=[e['values'][0]for t in events['tracks']for e in t if e.get('event')=='program'];notes=[e['values'][0]for t in events['tracks']for e in t if e.get('event')=='note_on'and e['values'][1]>0]
        need(programs==[voice]and notes==[60],'independent fixed footstep MIDI voice/key')
        raw=sources['Wav_'+kind+'_footstep_sample.wav']
        with wave.open(io.BytesIO(raw),'rb')as wav:
            need((wav.getnchannels(),wav.getsampwidth(),wav.getframerate(),wav.getnframes())==(1,1,rate,frames),'fixed source WAV format')
            pcm=bytes(b^128 for b in wav.readframes(frames))
        need(len(pcm)==frames,'whole signed PCM extent')
        result[sid]=dict(voice=voice,pcm=pcm,source_identity=identity(raw),midi_identity=identity(midi),midi_events=events,pcm_identity=identity(pcm))
    return result


def bind_engine(raw,proof):
    """独立review済JP窓を現在候補に再束縛。root pointer単体署名ではない。"""
    need(identity(raw)==CANDIDATE,'engine proof requires current whole candidate')
    need(proof['status']=='OLD_FORMAL_STATIC_SEMANTIC_REVIEW_CURRENT_CANDIDATE_NOT_YET_BOUND','reviewed source semantic proof')
    for row in proof['windows']:
        need(window(raw,row['address'],row['size'])=={k:row[k]for k in('address','size','sha256')},'reviewed JP engine window drift '+row['name'])
    for row in proof['roots']:
        need(u32(raw,row['address'])==row['value'],'rooted JP literal binding '+row['name'])
    roots={r['name']:r['value']for r in proof['roots']}
    table=roots['song_table_literal'];mplay=roots['mplay_table_literal'];capacities=[]
    for i in range(roots['init_player_count']):
        row=chunk(raw,mplay+12*i,12);capacity=row[8]
        need(0<capacity<=16,'source-initialized MPlayOpen capacity');capacities.append(capacity)
    need(capacities==[p['capacity']for p in proof['players']],'all initialized player capacities')
    need(tuple(chunk(raw,roots['clock_dispatch_literal'],49))==CLOCK,'actual whole gClockTable')
    dispatch=proof['effective_jump_table'];targets=list(struct.unpack('<36I',chunk(raw,dispatch['template_address'],144)))
    need(targets==dispatch['template_targets'],'whole original command template')
    for patch in dispatch['extender_patches']:
        need(u32(raw,patch['literal_site'])==patch['target'],'exact effective command patch')
        targets[patch['slot']]=patch['target']
    need(targets==dispatch['effective_targets'],'all effective extended dispatch slots')
    current_proof=copy.deepcopy(proof);current_proof['status']='PASS_REVIEWED_ENGINE_WINDOWS_BOUND_TO_CURRENT_CANDIDATE';current_proof['current_candidate']=identity(raw)
    return dict(song_table=table,mplay_table=mplay,player_capacities=capacities,proof=current_proof)


def extend(raw,inherited,engine,sources,source_bindings):
    need(identity(raw)==CANDIDATE==inherited['candidate'],'exact current candidate and inherited inventory')
    need(inherited['candidates']==874 and inherited['classified']==455 and inherited['unclassified']==419,'exact prior classification frontier')
    # Prior full scan is reused, not rerun. Every inherited hit retains its four actual bytes.
    for hit in inherited['hits']:need(identity(chunk(raw,hit['address'],hit['size']))=={k:hit[k]for k in('size','sha256')},'inherited actual hit bytes unchanged')
    ids=source_song_ids(sources['songs.h'].decode());feet=footstep_sources(sources)
    unknown=[h for h in inherited['hits']if not h['accepted']]
    regions,songs,diagnostics=song_regions(raw,ids,engine,unknown,feet)
    result=copy.deepcopy(inherited);witnesses=[]
    for i,region in enumerate(regions):
        witnesses.append(dict(id=i,start=region.start,end_exclusive=region.end,kind=region.kind,**region.evidence))
    changed=[]
    for i,hit in enumerate(result['hits']):
        if hit['accepted']:continue
        matched=[n for n,r in enumerate(regions)if contains(r.start,r.end,hit['address'],hit['size'])];kinds={regions[n].kind for n in matched}
        if len(kinds)!=1:continue
        kind=next(iter(kinds));result['hits'][i]={k:v for k,v in hit.items()if k not in('reason','owner_candidates')}
        result['hits'][i].update(accepted=True,classification='FALSE_POSITIVE_TYPED_SONG_'+kind.upper(),evidence=[dict(song_asset_witness=n,asset=witnesses[n]['asset'])for n in matched]);changed.append(hit['address'])
    classified=sum(h['accepted']for h in result['hits']);result.update(classified=classified,unclassified=874-classified,classifications=dict(collections.Counter(h['classification']for h in result['hits'])))
    footstep_observed=[]
    for sid in (250,251):
        row=next((r for r in songs if r['id']==sid),None)
        if row is None:footstep_observed.append(dict(song=sid,status='UNSUPPORTED_CURRENT_SONG'));continue
        header=u32(raw,engine['song_table']+sid*8);group=u32(raw,header+4);notes=trace_track(raw,u32(raw,header+8),group)['notes']
        programs=sorted({(n['voice_address']-group)//12 for n in notes});keys=sorted({n['key']for n in notes})
        match=programs==[feet[sid]['voice']]and keys==[60]
        footstep_observed.append(dict(song=sid,current_programs=programs,current_keys=keys,expected_program=feet[sid]['voice'],expected_key=60,
          source_midi_equivalence=match,status='MATCH'if match else 'CURRENT_SONG_DIFFERS_FROM_FIXED_CFRU_MIDI',source_midi=feet[sid]['midi_identity'],source_wav=feet[sid]['source_identity'],signed_pcm=feet[sid]['pcm_identity']))
    result['song_extension']=dict(status='PASS_ROOTED_TYPED_SONG_CONSUMERS_NOT_RUNTIME_PLAYBACK',source_bindings=source_bindings,engine=engine,
        explicit_source_ids=len(ids),accepted_complete_songs=len(songs),songs=songs,diagnostics=diagnostics,asset_witnesses=witnesses,
        newly_classified=len(changed),new_addresses=changed,footsteps=footstep_observed,old_full_rom_inventory_reused=True,
        all_previous_classifications_retained=True,external_mutation_free_command_model=True,actual_playback_claimed=False,
        complete_runtime_audio_read_footprint_claimed=False,indirect_reference_completeness_claimed=False)
    need(all(old==new for old,new in zip(inherited['hits'],result['hits'])if old['accepted']),'all previous accepted hits exactly retained')
    need(not result['donor_leased']and not result['donor_eligible'],'no donor lease')
    return result
