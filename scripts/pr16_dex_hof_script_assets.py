"""固定公開sourceと実map/object/animation consumerで有限raw4bpp frameを束縛する。"""
from pathlib import Path
import hashlib,json,re,struct
import pr16_dex_hof_donor as d
import pr16_dex_hof_reference_gaps as gaps
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE=gaps.CANDIDATE
EXPECTED=[(0x0834AF06,53,1,39,11,2,2),(0x0834B90A,53,1,39,11,6,7),(0x0834BB0A,53,1,39,11,6,8),(0x08353E7F,144,2,38,0,4,4)]

def source_animations(sources,review):
 for row in review['sources']:
  need(row['repository']=='pret/pokefirered'and row['commit']=='c75f352304d529f6ba92d4f74b9cf8b5c3810788','locked public animation source')
  value=sources[row['local']]
  need(identity(value)=={k:row[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(value)).encode()+b'\0'+value).hexdigest()==row['git_blob_sha'],'whole fixed source size/SHA/Git blob')
 text=sources['object_event_anims.h'].decode();constants=sources['anim-constants.h'].decode()
 const={k:int(v,0)for k,v in re.findall(r'#define\s+(ANIM_\w+)\s+(\d+|0x[0-9a-fA-F]+)',constants)}
 const.update({k:const[a]+int(b)for k,a,b in re.findall(r'#define\s+(ANIM_\w+)\s+\((ANIM_\w+) \+ (\d+)\)',constants)})
 anims={}
 for name,body in re.findall(r'static const union AnimCmd (\w+)\[\] = \{(.*?)\};',text,re.S):
  words=[]
  for line in body.strip().splitlines():
   m=re.search(r'ANIMCMD_(FRAME|JUMP|LOOP)\((.*?)\)|ANIMCMD_(END)',line);need(m is not None,'closed source animation grammar')
   if m[3]:a,b=65535,0
   else:
    kind,args=m[1],m[2].split(',')
    if kind=='FRAME':a=int(args[0]);b=int(args[1])+(64 if '.hFlip = TRUE'in m[2]else 0)+(128 if '.vFlip = TRUE'in m[2]else 0)
    else:a,b={'JUMP':65534,'LOOP':65533}[kind],int(args[0])
   words.extend((a,b))
  anims[name]=struct.pack('<'+'H'*len(words),*words)
 body=re.search(r'static const union AnimCmd \*const sAnimTable_Standard\[\] = \{(.*?)\};',text,re.S)
 need(body is not None,'exact source Standard animation table')
 rows=[(const[key],name)for key,name in re.findall(r'\[(\w+)\]\s*=\s*(\w+)',body[1])]
 need(sorted(i for i,n in rows)==list(range(21)),'all source Standard slots, exact finite21')
 return anims,[name for i,name in sorted(rows)]

def _regions(raw,inherited,review,sources,root):
 need(review['required_candidate']==CANDIDATE,'fixed current target')
 binding=review['accepted_consumer_review'];p=root/binding['path'];need(p.is_file()and not p.is_symlink(),'regular accepted prior consumer review');v=p.read_bytes()
 need(identity(v)=={k:binding[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(v)).encode()+b'\0'+v).hexdigest()==binding['git_blob_sha'],'whole accepted consumer review identity')
 prior=json.loads(v)['sprite'];gaps.bind_code_windows(raw,prior)
 anims,sequence=source_animations(sources,review)
 need(len(review['rows'])==len(EXPECTED),'only four exact candidate rows')
 result=[];proof=[]
 for row,expected in zip(review['rows'],EXPECTED):
  hit=row['hit'];m=row['map_selector'];gid=row['graphics_id']
  need((hit['address'],gid,m['group'],m['number'],m['object_index'],row['animation_index'],row['frame_index'])==expected,'closed exact selectors')
  need(next(h for h in inherited['hits']if h['address']==hit['address'])==hit and not hit['accepted']and not hit['owner_candidates'],'exact retained unowned unknown')
  chain=row['root_chain'];need([w['role']for w in chain]==['map_groups_literal','group_slot','map_slot','map_header','events','object'],'complete selected map root path');d.signed(raw,chain)
  groups,group,slot,header,events,obj=chain
  for w in(groups,group,slot):need(w['size']==4 and d.u32(raw,w['address'])==w['value'],'actual map pointer')
  need(groups['address']==0x08054B0C and group['address']==groups['value']+m['group']*4 and slot['address']==group['value']+m['number']*4 and header['address']==slot['value']and header['size']==8,'finite selected map chain')
  need(d.u32(raw,header['address']+4)==header['events']==events['address']and events['size']==8 and chunk(raw,events['address'],1)[0]==events['count']>m['object_index'],'bounded object count')
  need(d.u32(raw,events['address']+4)==events['objects']and obj['address']==events['objects']+24*m['object_index']and obj['size']==24 and chunk(raw,obj['address']+1,1)[0]==obj['graphics_id']==gid<240,'actual selected graphics ID field')
  literal,gslot,info,atable,aslot,animation,frame,asset=[row[k]for k in('graphics_table_literal','graphics_slot','info','animation_table','animation_slot','animation','frame','asset')]
  for w in(literal,gslot,info,atable,aslot,animation,frame,asset,hit):d.signed(raw,w)
  need(literal['address']==0x0805EBB4 and literal['size']==4 and d.u32(raw,literal['address'])==literal['value']and gslot['address']==literal['value']+gid*4 and d.u32(raw,gslot['address'])==gslot['value']==info['address'],'actual bounded graphics lookup')
  need(info['size']==36 and struct.unpack('<HH',chunk(raw,info['address']+8,4))==(row['width'],row['height'])==(32,32),'actual complete graphics info dimensions')
  need(d.u32(raw,info['address']+24)==atable['address']and atable['size']==21*4 and row['animation_table_source']=='sAnimTable_Standard','complete source-shaped animation table')
  need(len(row['source_animation_rows'])==21,'all Standard commands independently typed')
  for i,(a,name)in enumerate(zip(row['source_animation_rows'],sequence)):
   s,w=a['slot'],a['animation'];d.signed(raw,s);d.signed(raw,w)
   need(a['index']==i and a['source']==name and s['address']==atable['address']+4*i and s['size']==4 and d.u32(raw,s['address'])==s['value']==w['address']and w['size']==len(anims[name])and chunk(raw,w['address'],w['size'])==anims[name],'entire selected pointer and source serialized animation commands')
  selected=row['source_animation_rows'][row['animation_index']]
  need(aslot==selected['slot']and animation==selected['animation']and row['animation_source']==selected['source'],'selected finite animation belongs to source table')
  data=anims[row['animation_source']];words=struct.unpack('<'+'H'*(len(data)//2),data)
  need(row['frame_index']in words[::2]and row['frame_index']<65533,'selected frame occurs in exact source sequence')
  frames=d.u32(raw,info['address']+28);need(row['image_table_pointer']==dict(address=info['address']+28,value=frames)and frame['address']==frames+row['frame_index']*8 and frame['size']==8,'image array row chosen by source frame index')
  need(struct.unpack('<IH',chunk(raw,frame['address'],6))==(asset['address'],asset['size'])and asset['size']==row['width']*row['height']//2==512,'actual data pointer and exact raw4bpp size')
  need(d.contains(asset['address'],asset['address']+asset['size'],hit['address'],4),'whole hit within finite pixel payload, no metadata or padding')
  evidence=dict(asset=asset,width=32,height=32,bits_per_pixel=4,root_verified=True,frame_index=row['frame_index'],frame_record=frame,graphics_id=gid,map_selector=m,animation_index=row['animation_index'],animation=animation,animation_source=row['animation_source'],source_extent=dict(command_count=animation['size']//4,command_stride=4,table_count=21,table_stride=4),actual_screen_rendered=False,full_story_reachability_claimed=False)
  result.append(d.TypedRegion(asset['address'],asset['address']+asset['size'],'rooted_object_sprite_4bpp_frame',evidence));proof.append(dict(hit=hit['address'],asset=asset,graphics_id=gid,animation_source=row['animation_source']))
 return result,dict(status='PASS_FINITE_SOURCE_ROOTED_OBJECT_FRAMES',count=len(result),rows=proof,actual_screen_rendered=False,full_story_reachability_claimed=False)

def regions(raw,latest,inherited,review,sources,root):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'current whole candidate mandatory')
 for owner in review['current_actual_owners']:gaps.bind_owner(raw,latest,owner)
 return _regions(raw,inherited,review,sources,root)
