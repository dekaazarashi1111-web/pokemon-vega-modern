"""追加field-moveの未接続根を保留する限定監査。型領域は生成しない。"""
import copy
import hashlib
import json
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_lifetime_menu as menu
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE,DIAGNOSTIC=party.CANDIDATE,party.DIAGNOSTIC
HITS=HELD_HITS=TARGET_HITS=(0x091494EA,)
CLASSIFIED_HITS=()
KIND='held_unconnected_extended_field_move_text'
TYPE_CATEGORY='guard'
SOURCE_IDS = {'cfru-hooks': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                'git_blob_sha': '51a0f10dd4cccad235b476edd534a0e3e7e612ad',
                'local': 'cfru-hooks',
                'path': 'hooks',
                'repository': 'kapibarasan000/CFRU-JP',
                'sha256': '19c730e12bcc8ee614b43745a1a6478429c1876a025fdce23b80a49599d8deb5',
                'size': 21787},
 'cfru-party_menu.c': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                       'git_blob_sha': 'b17bef5771a1887496e5cfc9e15ccf545fa18579',
                       'local': 'cfru-party_menu.c',
                       'path': 'src/party_menu.c',
                       'repository': 'kapibarasan000/CFRU-JP',
                       'sha256': '6b72ebe4b136af6d573c5e7079fe183497a7883ff2daceb4c519cd8dd8e66e59',
                       'size': 83459},
 'cfru-repoints': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                   'git_blob_sha': 'e56ff804cca49e38aa7d18466dceb54e776cc662',
                   'local': 'cfru-repoints',
                   'path': 'repoints',
                   'repository': 'kapibarasan000/CFRU-JP',
                   'sha256': 'b387e4239d00a59698407b1837b5573504bcb172fb41cae6afb7265c1008a12d',
                   'size': 7547},
 'cfru-strings_party_menu.string': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                    'git_blob_sha': 'a33a010d7ed77ca465dda2a634813af6c112ca49',
                                    'local': 'cfru-strings_party_menu.string',
                                    'path': 'strings/party_menu.string',
                                    'repository': 'kapibarasan000/CFRU-JP',
                                    'sha256': '7a24ce4901b43ab3ca4c13de292b26372b98be5b6d03d4f0130d30a207f8231c',
                                    'size': 2361}}
SPECS = {'description_argument_and_threshold': (135407876,
                                        [('push', 112, True),
                                         ('spadd', -20),
                                         ('shift', 'lsl', 0, 0, 24),
                                         ('shift', 'lsr', 0, 0, 24),
                                         ('addi', 6, 0, 0),
                                         ('literal', 0, 135407924),
                                         ('mem', True, 'word', 5, 0, 0),
                                         ('imm', 'cmp', 6, 17),
                                         ('branch', 8, 135407928)]),
 'description_table_read': (135407988,
                            [('literal', 1, 135408044),
                             ('addi', 0, 6, 0),
                             ('imm', 'sub', 0, 18),
                             ('shift', 'lsl', 0, 0, 2),
                             ('add', 0, 0, 1),
                             ('mem', True, 'word', 0, 0, 0),
                             ('spmem', False, 0, 16)]),
 'field_match_append': (135410234,
                        [('literal', 0, 135410260),
                         ('mem', True, 'word', 1, 0, 0),
                         ('addi', 0, 1, 0),
                         ('imm', 'add', 0, 15),
                         ('imm', 'add', 1, 23),
                         ('addi', 2, 4, 0),
                         ('imm', 'add', 2, 18),
                         ('shift', 'lsl', 2, 2, 24),
                         ('shift', 'lsr', 2, 2, 24),
                         ('call', 134674028),
                         ('jump', 135410284)]),
 'field_outer_loop': (135410284,
                      [('movhi', 1, 8),
                       ('shift', 'lsl', 0, 1, 24),
                       ('shift', 'lsr', 7, 0, 24),
                       ('imm', 'cmp', 7, 3),
                       ('branch', 9, 135410192),
                       ('spmem', True, 0, 4)]),
 'outer_field_move_compare': (135410204,
                              [('imm', 'mov', 0, 100),
                               ('movhi', 6, 10),
                               ('alu', 'mul', 6, 0),
                               ('literal', 5, 135410264),
                               ('movhi', 1, 9),
                               ('add', 0, 1, 6),
                               ('addi', 1, 7, 0),
                               ('imm', 'add', 1, 13),
                               ('call', 134476628),
                               ('shift', 'lsl', 1, 4, 1),
                               ('add', 1, 1, 5),
                               ('mem', True, 'half', 1, 1, 0),
                               ('compare', 0, 1),
                               ('branch', 1, 135410268)]),
 'outer_field_move_next': (135410268,
                           [('addi', 0, 4, 1),
                            ('shift', 'lsl', 0, 0, 24),
                            ('shift', 'lsr', 4, 0, 24),
                            ('shift', 'lsl', 0, 4, 1),
                            ('add', 0, 0, 5),
                            ('mem', True, 'half', 0, 0, 0),
                            ('imm', 'cmp', 0, 12),
                            ('branch', 1, 135410212)]),
 'outer_field_prefix': (135410136,
                        [('push', 240, True),
                         ('movhi', 7, 10),
                         ('movhi', 6, 9),
                         ('movhi', 5, 8),
                         ('push', 224, False),
                         ('spadd', -8),
                         ('movhi', 9, 0),
                         ('shift', 'lsl', 1, 1, 24),
                         ('shift', 'lsr', 1, 1, 24),
                         ('movhi', 10, 1),
                         ('literal', 2, 135410260),
                         ('mem', True, 'word', 1, 2, 0),
                         ('imm', 'mov', 0, 0),
                         ('mem', False, 'byte', 0, 1, 23),
                         ('mem', True, 'word', 1, 2, 0),
                         ('addi', 0, 1, 0),
                         ('imm', 'add', 0, 15),
                         ('imm', 'add', 1, 23),
                         ('imm', 'mov', 2, 0),
                         ('call', 134674028),
                         ('imm', 'mov', 7, 0),
                         ('literal', 0, 135410264),
                         ('mem', True, 'half', 0, 0, 0),
                         ('spmem', False, 0, 0),
                         ('movhi', 0, 9),
                         ('imm', 'add', 0, 100),
                         ('spmem', False, 0, 4),
                         ('imm', 'mov', 4, 0),
                         ('addi', 1, 7, 1),
                         ('movhi', 8, 1),
                         ('spmem', True, 0, 0),
                         ('imm', 'cmp', 0, 12),
                         ('branch', 0, 135410284)])}
WORDS = {135407924: 33796112, 135408044: 138517260, 135410260: 33796112, 135410264: 138518270}
MOVE_IDS = (148, 15, 19, 70, 57, 249, 127, 100, 91, 208, 135, 230, 12)
STOCK_DESCRIPTIONS = [138274296,
 138274251,
 138274261,
 138274285,
 138274273,
 138274305,
 138274317,
 138274372,
 138274338,
 138274361,
 138274361,
 138274349]
EXTENDED_DESCRIPTIONS = [138274296,
 138274251,
 138274261,
 138274285,
 138274273,
 138274305,
 138274317,
 138274372,
 138274338,
 138274361,
 138274361,
 138274349,
 152343762,
 152343777,
 152343789]
FIXED_WINDOWS = [{'address': 135407876, 'sha256': '144aeea33c0558d916db72f6eb1fbccb79148bc330f41e7cf40d8457d013ba7d', 'size': 18},
 {'address': 135407924, 'sha256': '401369c6ac2880741f3c7481c9fed2000999a4cee6807273aa6881c52da63346', 'size': 4},
 {'address': 135407988, 'sha256': 'd9e423e0a28fadefe18a1047b8993d3a19ea98831ff6dd2817249def83666b18', 'size': 14},
 {'address': 135408044, 'sha256': 'f25d09061cf1e3fdcd1d02a052902057e3abc2434c341c199aa623f942990b78', 'size': 4},
 {'address': 135410136, 'sha256': '77b664d6af53672a950ed631c0337382da8f3c9daa8bad72c252de0e4a81ba42', 'size': 68},
 {'address': 135410204, 'sha256': 'dfb55595dea0c032faa15c5458f5e4f664985ab6f4d4d0f7e78d64d28cbf7421', 'size': 30},
 {'address': 135410234, 'sha256': '44f444c57a9ccb1f1a99170fe2d1e89dd71ce997aff47730899ef09615d6fd5b', 'size': 24},
 {'address': 135410260, 'sha256': '401369c6ac2880741f3c7481c9fed2000999a4cee6807273aa6881c52da63346', 'size': 4},
 {'address': 135410264, 'sha256': 'ab3a8cacb511655c768f21d7f17772833fde7eea18a054936ddbea5520aa3178', 'size': 4},
 {'address': 135410268, 'sha256': '7f4c267bb2e9d6d4cd99a0666493d562de4fadbcc077711df3cefde9d5ded229', 'size': 16},
 {'address': 135410284, 'sha256': 'f59b147b69c4186e5ed5697033939c5b23ef8bfb268f5c827655df6d877c536d', 'size': 12},
 {'address': 138517260, 'sha256': 'c3cdcd7d88b53fef825c04fd8a498be901d32881a8bcecea8b8859ee2f0f840a', 'size': 48},
 {'address': 138518270, 'sha256': 'd1546aa524f989f9fdb92dcc8728770e282d9a155653ce8ac7bc4725f16e863f', 'size': 26},
 {'address': 152343777, 'sha256': '849ae6efd0f9b4fd8c23e8e8cb82a490bd043fb38a637828e4d345e95729fa84', 'size': 23},
 {'address': 152473700, 'sha256': 'efd9da4b625d3f4b6a1c8c2575dfd45c56eb470043ea61ec201c95642942839e', 'size': 60}]
BLOCKS={name:tuple(party.block(a,specs))for name,(a,specs)in SPECS.items()}
INS={i.address:i for rows in BLOCKS.values()for i in rows}
TEXTS=(
 dict(address=0x091494E1,size=12,text='ふかい きりを はらう',source_label='gText_FieldMoveDesc_Defog'),
 dict(address=0x091494ED,size=11,text='すいちゅうに もぐる',source_label='gText_FieldMoveDesc_Dive'),
)
# 公開日本語textを意味として独立encode。ROMの生byte列を埋め込まない。
HIRAGANA='あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんぁぃぅぇぉゃゅょがぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽっ'
TEXT_ENCODING={c:i+1 for i,c in enumerate(HIRAGANA)}
TEXT_ENCODING[' ']=0
ROOT_FINDINGS=dict(
 stock_producer_entry=0x081231D8,stock_move_literal=0x08123258,stock_move_table=0x08419EFE,
 stock_move_count=12,stock_terminator=12,action_base=18,stock_action_range=[18,29],
 description_consumer_entry=0x08122904,description_literal=0x081229AC,
 actual_description_table=0x08419B0C,extended_description_table=0x09169064,
 defog_index=13,dive_index=14,required_extended_actions=[31,32],
 defog_pointer_cell=0x09169098,dive_pointer_cell=0x0916909C,
 root_gap='actual stock producer cannot append indices13/14; actual description literal still selects stock12 table',
 text_boundary=dict(address=0x091494EA,size=4,parts=[dict(address=0x091494EA,size=3),dict(address=0x091494ED,size=1)]),
)
CLAIMS=dict(
 classification='UNKNOWN_HELD',newly_classified=0,emits_typed_regions=False,root_verified=False,
 bounded_stock_producer_projection_only=True,extended_table_presence_proven=True,
 complete_consumer_byte_reads_proven=False,synthetic_contract_execution=False,
 actual_runtime_execution_observed=False,full_story_reachability_claimed=False,
 all_possible_roots_absent_proven=False,extended_code_globally_unreachable_proven=False,
 universal_allocation_epoch_proven=False,all_opaque_effects_proven=False,
 irq_noninterference_proven=False,indirect_reference_completeness_claimed=False,
 donor_eligible=False,donor_leased=False,
)
LIMITS=dict(
 scope_ja='根不成立の限定反証。新consumerへの到達・文字消費・解放域は証明しない。',
 contract_ja='公開sourceの名前や追加tableの存在を現ROMの登録根とみなさない。既存stock loopが示す候補indexの射影だけを確認。',
 lifetime_ja='正の到達合成を行わないため、新RAM保存契約・heap epoch契約を仮定しない。追加producer接続後に別途必要。',
 input_ja='診断入力と正式候補を分離。正式候補の分類数は増やさない。',
 remaining_ja='追加IDの実producer・追加tableへの実登録根・両textの実byte consumer・生存契約が未結合。別経路不存在や全到達を主張しない。',
)

def exact(a,b):
 return json.dumps(a,sort_keys=True,separators=(',',':'),allow_nan=False)==json.dumps(b,sort_keys=True,separators=(',',':'),allow_nan=False)

def encode_text(text):
 need(type(text)is str and all(c in TEXT_ENCODING for c in text),'公開日本語文字集合')
 return bytes([TEXT_ENCODING[c]for c in text]+[255])

def bind_semantics(raw):
 for i in INS.values():
  need(chunk(raw,i.address,i.size)==menu.encoded(i),'追加field根の実意味命令 '+hex(i.address))
 for a,value in WORDS.items():need(d.u32(raw,a)==value,'実literalはstock根 '+hex(a))
 for j,value in enumerate(MOVE_IDS):
  need(int.from_bytes(chunk(raw,0x08419EFE+2*j,2),'little')==value,'stock field-move ID/終端')
 for base,values in ((0x08419B0C,STOCK_DESCRIPTIONS),(0x09169064,EXTENDED_DESCRIPTIONS)):
  for j,value in enumerate(values):need(d.u32(raw,base+4*j)==value,'説明tableの実pointer')
 for row in TEXTS:
  encoded=encode_text(row['text']);need(len(encoded)==row['size'],'公開text長')
  need(chunk(raw,row['address'],row['size'])==encoded,'日本語textの独立encode')
 d.signed(raw,FIXED_WINDOWS)

def sources_bind(review,sources):
 need(type(sources)is dict and set(sources)==set(SOURCE_IDS),'閉じた固定source集合')
 need(exact(review['source_bindings'],SOURCE_IDS),'固定source identity')
 for key,row in SOURCE_IDS.items():
  value=sources[key]
  need(type(value)is bytes and identity(value)=={k:row[k]for k in('size','sha256')},'公開source全文identity '+key)
  need(hashlib.sha1(b'blob '+str(len(value)).encode()+b'\0'+value).hexdigest()==row['git_blob_sha'],'公開Git blob '+key)
 body=sources['cfru-party_menu.c'].decode()
 for token in ('[FIELD_MOVE_DEFOG] = gText_FieldMoveDesc_Defog,','[FIELD_MOVE_DIVE] = gText_FieldMoveDesc_Dive,',
               'for (j = 0; j < NELEMS(gFieldMoves); ++j)',
               'AppendToList(sPartyMenuInternal->actions, &sPartyMenuInternal->numActions, j + MENU_FIELD_MOVES);'):
  need(token in body,'公開source追加producer/table構造')
 need('SetPartyMonFieldSelectionActions 81231D8 2' in sources['cfru-hooks'].decode(),'公開hook指示')
 for token in ('gFieldMoveDescriptions 081229AC','gFieldMoves 08123258'):
  need(token in sources['cfru-repoints'].decode(),'公開repoint指示')
 text=sources['cfru-strings_party_menu.string'].decode()
 for row in TEXTS:need('#org @'+row['source_label']+'\n'+row['text']+'\n' in text,'公開日本語textの語義')

def producer_projection():
 """bind済みstock loopの等値比較で生成可能なindexだけを射影する。実RAM実行ではない。"""
 need(MOVE_IDS[-1]==12 and len(MOVE_IDS)==13 and len(set(MOVE_IDS))==13,'固定12要素と非重複終端')
 # 半word入力全65536は12個の一致クラスと残余クラスに分割できる。
 classes=[dict(move=value,indices=[j],actions=[j+18])for j,value in enumerate(MOVE_IDS[:-1])]
 classes.append(dict(move='all_other_uint16_values',indices=[],actions=[]))
 possible=sorted({action for row in classes for action in row['actions']})
 need(possible==list(range(18,30)) and set(possible).isdisjoint((31,32)),'追加IDはstock loopから生成しない')
 return dict(kind='bound_stock_equality_loop_projection',classes=classes,domain_size=65536,
             other_class_size=65536-12,independent_move_slots=4,possible_actions=possible,
             required_extended_actions=[31,32],required_actions_generated=False,
             runtime_execution_observed=False,all_external_writers_analyzed=False)

def protected_windows(review):
 need(exact(review['windows'],FIXED_WINDOWS),'不変の最小保護窓')
 return copy.deepcopy(FIXED_WINDOWS)

def make_review(raw,hits):
 selected=[row for row in hits if row['address']in TARGET_HITS]
 need(len(selected)==1,'保留対象は1件')
 if raw is not None:bind_semantics(raw)
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),
             source_bindings=copy.deepcopy(SOURCE_IDS),hits=copy.deepcopy(selected),windows=copy.deepcopy(FIXED_WINDOWS),
             root_findings=copy.deepcopy(ROOT_FINDINGS),texts=copy.deepcopy(TEXTS),claims=copy.deepcopy(CLAIMS),limits=copy.deepcopy(LIMITS))

def held_proof_template(current_candidate_measured=False):
 need(type(current_candidate_measured)is bool,'正式candidate測定状態は明示bool')
 return dict(status='PASS_HELD_UNCONNECTED_FIELD_MOVE_ROOT',count=0,hits=[],held_hits=list(HELD_HITS),
             retained_unknown_hits=list(HELD_HITS),root_findings=copy.deepcopy(ROOT_FINDINGS),
             producer_projection=producer_projection(),protected_windows=len(FIXED_WINDOWS),
             protected_bytes=sum(row['size']for row in FIXED_WINDOWS),source_bindings=copy.deepcopy(SOURCE_IDS),
             limits=copy.deepcopy(LIMITS),all_inherited_fields_unchanged=True,
             current_candidate_measured=current_candidate_measured,**copy.deepcopy(CLAIMS))

def validate_held_proof(proof,current_candidate_measured=False):
 need(type(proof)is dict and exact(proof,held_proof_template(current_candidate_measured)),'固定source moduleに閉じた未知維持proof')
 return True

def _regions(raw,inherited,review,sources):
 """全体identityを親が一度照合した後のbounded監査API。常に型領域0件。"""
 need(type(review)is dict and set(review)=={'schema_version','required_candidate','diagnostic_input','source_bindings','hits','windows','root_findings','texts','claims','limits'},'閉じた保留review')
 need(type(review['schema_version'])is int and review['schema_version']==1,'整数schema')
 need(exact(review['required_candidate'],CANDIDATE) and exact(inherited['candidate'],CANDIDATE),'正式候補identityは不変')
 need(exact(review['diagnostic_input'],DIAGNOSTIC),'診断入力を正式候補へ昇格しない')
 for key,expected in(('root_findings',ROOT_FINDINGS),('texts',TEXTS),('claims',CLAIMS),('limits',LIMITS)):
  need(exact(review[key],expected),'保留scopeは不変 '+key)
 selected=[row for row in inherited['hits']if row['address']in TARGET_HITS]
 need(len(selected)==1 and exact(selected,review['hits']),'既unknown行の完全identity')
 h=selected[0]
 need(type(h['address'])is int and h['address']==TARGET_HITS[0] and type(h['size'])is int and h['size']==4 and h['accepted']is False and h['owner_candidates']==[] and h['kind']=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS' and h['classification']=='UNCLASSIFIED','owner外の未分類4byteを維持')
 d.signed(raw,h);protected_windows(review);sources_bind(review,sources);bind_semantics(raw)
 proof=held_proof_template();validate_held_proof(proof)
 return [],proof

def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'正式候補全体identityを照合。診断は不可。')
 rows,proof=_regions(raw,inherited,review,sources);proof['current_candidate_measured']=True
 validate_held_proof(proof,True);return rows,proof

def witness_geometry(evidence):
 raise ValueError('未接続field-move根はTypedRegionを発行しない')
