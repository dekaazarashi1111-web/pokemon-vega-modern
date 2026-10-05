"""実EasyChat/ability consumerから有限隣接textだけ分類する候補実装。"""
import hashlib,json,re,struct
from pathlib import Path
import pr16_dex_hof_donor as d
import pr16_dex_hof_reference_code as code
import pr16_dex_hof_reference_gaps as gaps
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE=gaps.CANDIDATE
EASY_HITS=(0x083AF719,0x083AF71E,0x083AFDEF,0x083AFDF4,0x083B0D55,0x083B0D67,0x083B15B5,0x083B15E1,0x083B1A3B,0x083B1A44,0x083B1A49,0x083B1A52,0x083B1A5D,0x083B1A61,0x083B1EA4,0x083B29E0)
ABILITY_HITS=(0x09094D37,0x09094E72,0x09094F31,0x0909504B,0x090956F4,0x09095769)
def half(raw,a):return int.from_bytes(chunk(raw,a,2),'little')
def literal(raw,a,reg):
 op=half(raw,a);need(op&0xF800==0x4800 and(op>>8)&7==reg,'exact literal-load target register');return((a+4)&~3)+(op&255)*4

def source_proof(review,sources,root):
 values={}
 for name,exp in review['source_bindings'].items():
  if 'local'in exp:b=sources[exp['local']]
  else:
   path=root/name;need(path.is_file()and not path.is_symlink(),'regular fixed source');b=path.read_bytes()
  need(identity(b)=={k:exp[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==exp['git_blob_sha'],'whole source SHA and Git blob');values[name]=b
 return values

def bind_consumer(raw,part):
 d.signed(raw,part['consumer_windows']);d.signed(raw,part['literals']);d.signed(raw,part['calls'])
 for row in part['literals']:need(d.u32(raw,row['address'])==row['value'],'actual whole literal word')
 for row in part['calls']:need(code.thumb_bl(chunk(raw,row['address'],4),row['address'])==row['target'],'each complete direct Thumb BL')
 return{r['label']:r for r in part['literals']}

def pair(raw,inherited,row):
 hit=row['hit'];original=next(h for h in inherited['hits']if h['address']==hit['address']);need(original==hit and not original['accepted']and not original['owner_candidates'],'exact prior unknown unowned row');d.signed(raw,hit)
 texts=row['texts'];need(len(texts)==2,'closed adjacent two-text crossing')
 left,right=[t['text']for t in texts]
 for w in(left,right):
  d.signed(raw,w);b=chunk(raw,w['address'],w['size']);need(0<len(b)<=128 and b[-1]==255 and 255 not in b[:-1],'finite terminal-only EOS byte text')
 need(left['address']+left['size']==right['address']and left['address']<=hit['address']<right['address']<hit['address']+4<=right['address']+right['size'],'complete exact two-text boundary crossing')
 return hit,left,right

def _regions(raw,inherited,review,sources,root):
 need(review['required_candidate']==CANDIDATE and review['unknown_count']==22,'closed current-candidate text review')
 src=source_proof(review,sources,root);easy=review['easy_chat'];ability=review['ability_descriptions'];need(tuple(r['hit']['address']for r in easy['rows'])==EASY_HITS and tuple(r['hit']['address']for r in ability['rows'])==ABILITY_HITS,'closed sixteen plus six hit sets')
 literals=bind_consumer(raw,easy);table=easy['groups'];d.signed(raw,table)
 need({(c['address'],c['target'])for c in easy['calls']}=={(0x080BEB16,0x080BEA4C),(0x080BEB34,0x080BEAB8),(0x080BEB3C,0x08008900)}and len(easy['calls'])==3,'complete finite EasyChat call chain')
 need(table['address']==0x083B3A44 and table['size']==176 and(easy['word_info_stride'],easy['group_stride'],easy['group_count'])==(12,8,22)and easy['excluded_value_list_groups']==[0,18,19,21],'source EasyChat group/word ABIs')
 counts=[int(n)for n in re.findall(rb'\.numWords\s*=\s*(\d+)',src['vendor/upstream/pokefirered/src/data/easy_chat/easy_chat_groups.h'])]
 need(len(counts)==22 and all(half(raw,table['address']+8*i+4)==n for i,n in enumerate(counts)),'whole source group counts agree with actual JP table')
 need(literal(raw,0x080BEA62,0)==0x080BEA80 and literal(raw,0x080BEAF0,1)==0x080BEB08 and literals['group_table_for_bound']['value']==literals['group_table_for_word']['value']==table['address'],'same actual bounds and lookup table roots')
 need(literals['word_index_mask_validation']['value']==literals['word_index_mask_copy']['value']==511,'same nine-bit index for bounds and lookup')
 need(literal(raw,0x080BEA52,0)==literals['undefined_validation']['address']==0x080BEA78 and literal(raw,0x080BEB28,0)==literals['undefined_copy']['address']==0x080BEB44 and literals['undefined_validation']['value']==literals['undefined_copy']['value']==65535,'actual undefined-word loads and shared sentinel')
 # The pinned actual consumer computes group*8, reads wordData, then index*12, reads text.
 for a,reg,imm in[(0x080BEA5E,3,21),(0x08008910,0,255)]:need(half(raw,a)&0xFF00==0x2800+(reg<<8)and half(raw,a)&255==imm,'actual group bound and byte EOS comparison')
 bprj=src['vendor/upstream/CFRU-JP/BPRJ.ld'].decode();need(re.search(r'StringCopy\s*=\s*0x8008900\s*\|\s*1',bprj),'pinned actual JP StringCopy root')
 regions=[];proof=[]
 for row in easy['rows']:
  hit,left,right=pair(raw,inherited,row)
  for text in row['texts']:
   group,index,g,w=text['group'],text['index'],text['group_row'],text['word_row'];d.signed(raw,g);d.signed(raw,w);need(((group<<9)|index)!=65535,'selected encoded word is not undefined')
   need(0<=group<22 and group not in easy['excluded_value_list_groups']and g['address']==table['address']+group*8 and g['size']==8 and 0<=index<counts[group]==g['count']==half(raw,g['address']+4),'actual bounded non-value-list EasyChat group and index')
   need(d.u32(raw,g['address'])==g['words']and w['address']==g['words']+index*12 and w['size']==12 and d.u32(raw,w['address'])==w['text']==text['text']['address'],'actual selected wordInfo.text root')
  evidence=dict(left=left,right=right,both_text_consumers_verified=True,source_pointer_interpretation=False,full_story_reachability_claimed=False,consumer='actual_jp_easy_chat_StringCopy',groups=[t['group']for t in row['texts']],indices=[t['index']for t in row['texts']])
  regions.append(d.TypedRegion(hit['address'],hit['address']+4,'adjacent_jp_text_crossing',evidence))
 # A current summary trampoline leads to the bounded table-index/read/copy helper.
 l=bind_consumer(raw,ability);t=ability['table'];contracts=json.loads(src['content/modernization/p04_species_runtime_contract.json'])['tables'];contract=contracts['ability_descriptions']
 need({(c['address'],c['target'])for c in ability['calls']}=={(0x093D1EF4,0x093D1E84),(0x093D1EAA,0x093D22CA),(0x093D1ECA,0x093D2898),(0x093D1E94,0x093D1EF0),(0x093D1EBE,0x093D2898)}and len(ability['calls'])==5,'complete getter/read/names/description caller chain')
 need((t['count'],t['stride'],t['address'])==(318,4,contract['new_address'])and contract['new_count']==318 and contract['stride']==4,'exact declared current ability pointer table')
 need(literal(raw,0x08136F04,3)==l['summary_hook_target']['address']and l['summary_hook_target']['value']==0x093D1EF5 and half(raw,0x08136F06)&0xFF87==0x4700 and(half(raw,0x08136F06)>>3)&15==3,'actual summary absolute Thumb root')
 need(literal(raw,0x093D1EF8,3)==l['summary_return_target']['address']and l['summary_return_target']['value']==0x08136F1B,'actual summary thunk returns outside old description path')
 need(literal(raw,0x093D1EA4,3)==l['derived_description_table']['address']and l['derived_description_table']['value']*4==t['address']==l['original_description_table']['value'],'same actual shifted and original typed table roots')
 need(literal(raw,0x093D1E84,3)==l['summary_state_pointer']['address']==0x093D1ED4 and l['summary_state_pointer']['value']==0x0203B0B4,'actual summary-state pointer root')
 need(literal(raw,0x093D1E8E,3)==l['summary_pokemon_offset']['address']==0x093D1ED8 and l['summary_pokemon_offset']['value']==0x323C,'actual summary Pokemon input offset')
 need(literal(raw,0x093D1E92,3)==l['current_ability_getter']['address']==0x093D1EDC and l['current_ability_getter']['value']==0x090DA23D,'actual current scalar ability getter literal')
 need(half(raw,0x093D1EF0)&0xFF87==0x4700 and(half(raw,0x093D1EF0)>>3)&15==3,'actual ability getter BX r3 consumer')
 need(literal(raw,0x093D1EB4,3)==l['ability_names_table']['address']==0x093D1EE4 and l['ability_names_table']['value']==contracts['ability_names']['new_address']and contracts['ability_names']['stride']==ability['names_stride']==17,'actual intervening names table and stride')
 need(literal(raw,0x093D1EB8,3)==l['summary_ability_name_destination']['address']==0x093D1EE8 and l['summary_ability_name_destination']['value']==0x318C,'actual distinct name destination')
 need(literal(raw,0x093D1EC2,3)==l['summary_ability_description_destination']['address']==0x093D1EEC and l['summary_ability_description_destination']['value']==0x3195,'actual description destination')
 need(half(raw,0x093D1EAE)&0xFF00==0x2100 and half(raw,0x093D1EAE)&255==17 and half(raw,0x093D1EBA)&0xFF00==0x2200 and half(raw,0x093D1EBA)&255==ability['names_copy_capacity']==9,'names stride and bounded names-copy arguments')
 # The description pointer moves r0→r6 before the names copy, then r6→r1 for its copy.
 save=half(raw,0x093D1EB0);restore=half(raw,0x093D1EC6)
 need(save&0xFFC0==0 and(save>>3)&7==0 and save&7==6 and restore&0xFFC0==0 and(restore>>3)&7==6 and restore&7==1,'actual r0-to-r6 preservation and r6-to-r1 description argument')
 push=half(raw,0x093D289A);pop=half(raw,0x093D28CA)
 need(push&0xFE00==0xB400 and push&0x100 and push&0xFF==0xF7 and pop&0xFF00==0xBC00 and pop&0xFF==0xF7,'bounded copy saves/restores same complete low-register frame including r6')
 need(ability['description_register']=='r6'and ability['description_register_preserved_by_copy']is True and half(raw,0x093D289C)&0xF800==0x9000 and(half(raw,0x093D289C)&255)*4==4,'callee scratch store cannot overwrite saved r6 slot20')
 need(half(raw,0x093D1E98)&0xFF00==0x2300 and(half(raw,0x093D1E98)&255)*2==318 and half(raw,0x093D1E9A)==0x005B,'actual318 bound in source argument path')
 need(ability['copy_capacity']==23 and ability['description_source_limit']==22 and half(raw,0x093D1EC4)&0xFF00==0x2200 and half(raw,0x093D1EC4)&255==23,'actual bounded description copy capacity')
 for row in ability['rows']:
  hit,left,right=pair(raw,inherited,row)
  for text in row['texts']:
   ix,w=text['index'],text['row'];d.signed(raw,w)
   need(0<=ix<318 and w['address']==t['address']+4*ix and w['size']==4 and d.u32(raw,w['address'])==w['value']==text['text']['address'],'actual bounded ability text pointer row')
   need(text['text']['size']<=22,'complete source text including EOS is read before copy bound')
  evidence=dict(left=left,right=right,both_text_consumers_verified=True,source_pointer_interpretation=False,full_story_reachability_claimed=False,consumer='actual_current_summary_bounded_byte_copy',indices=[t['index']for t in row['texts']])
  regions.append(d.TypedRegion(hit['address'],hit['address']+4,'adjacent_jp_text_crossing',evidence))
 return regions,dict(status='PASS_FINITE_EASYCHAT_AND_ABILITY_TEXT',easy_chat=16,ability_descriptions=6,total=22,actual_screen_rendered=False,full_story_reachability_claimed=False)

def regions(raw,inherited,review,sources,root):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'current whole candidate mandatory')
 return _regions(raw,inherited,review,sources,root)
