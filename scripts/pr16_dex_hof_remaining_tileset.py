"""既受入JP tileset consumerを再利用し、map7/5の有限LZ asset一件を分類する。"""
import json,hashlib
import pr16_dex_hof_donor as d
import pr16_dex_hof_reference_gaps as gaps
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE=gaps.CANDIDATE

def _regions(raw,inherited,review,root):
 need(review['required_candidate']==CANDIDATE,'exact current target')
 binding=review['accepted_consumer_review'];p=root/binding['path'];need(p.is_file()and not p.is_symlink(),'regular prior fixed consumer proof');b=p.read_bytes()
 need(identity(b)=={k:binding[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==binding['git_blob_sha'],'whole accepted prior consumer proof retained')
 prior=json.loads(b)['tilesets'];gaps.bind_code_windows(raw,prior)
 m=review['map'];need((m['group'],m['number'])==(7,5),'one exact finite map selector')
 for key in('groups_literal','group_slot','map_slot','header'):d.signed(raw,m[key])
 groups,group,slot,header=[m[k]for k in('groups_literal','group_slot','map_slot','header')]
 for w in(groups,group,slot):need(w['size']==4 and d.u32(raw,w['address'])==w['value'],'actual finite map pointer')
 need(groups['address']==0x08054B0C and group['address']==groups['value']+7*4 and slot['address']==group['value']+5*4 and header['address']==slot['value']and header['size']==28,'exact current map7/5 root chain')
 literal,ls,layout,tileset,asset=[review[k]for k in('layouts_literal','layout_slot','layout','tileset','asset')]
 for w in(literal,ls,layout,tileset,asset):d.signed(raw,w)
 need(literal['address']==0x08054A54 and d.u32(raw,literal['address'])==literal['value']and ls['address']==literal['value']+11*4 and d.u32(raw,ls['address'])==ls['value']==layout['address'],'actual layout ID12 selected slot')
 need(d.u32(raw,header['address'])==header['layout']==layout['address']and int.from_bytes(chunk(raw,header['address']+18,2),'little')==header['layout_id']==12,'map header selects this layout by both pointer and ID')
 need(layout['size']==28 and d.u32(raw,layout['address']+20)==layout['secondary_tileset']==tileset['address'],'actual secondary tileset layout field')
 need(tileset['size']==24 and chunk(raw,tileset['address'],2)==bytes([1,1])and tileset['is_compressed']==tileset['is_secondary']==1 and d.u32(raw,tileset['address']+4)==tileset['graphics']==asset['address'],'actual compressed secondary graphics pointer')
 enc,dec=d.decode_lz_at(raw,asset['address']);need(identity(enc)=={k:asset[k]for k in('size','sha256')}and identity(dec)==asset['decoded']and len(enc)==4599 and len(dec)==12288,'whole strict LZ grammar/extent/decoded identity')
 hit=review['hit'];need(hit['address']==0x082544C4 and next(h for h in inherited['hits']if h['address']==hit['address'])==hit and not hit['accepted']and not hit['owner_candidates'],'one exact original unowned unknown');d.signed(raw,hit)
 need(d.contains(asset['address']+4,asset['address']+asset['size'],hit['address'],4),'only compressed payload bytes, no header or padding')
 return[d.TypedRegion(asset['address']+4,asset['address']+asset['size'],'rooted_tileset_lz77',dict(asset={k:asset[k]for k in('address','size','sha256')},decoded=asset['decoded'],layout_id=12,map=[7,5],actual_screen_rendered=False))],dict(status='PASS_CURRENT_MAP7_5_TILESET_LZ',count=1,actual_screen_rendered=False)

def regions(raw,inherited,review,root):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'current whole candidate mandatory')
 return _regions(raw,inherited,review,root)
