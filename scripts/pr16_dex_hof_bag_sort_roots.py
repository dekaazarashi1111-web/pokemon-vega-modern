"""Bag並替えの実producerが除く2labelを未知維持するguard。外部I/Oなし。"""
import copy
import hashlib
import json
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_menu_text as engine
import pr16_dex_hof_runtime_party as rt
need, identity, chunk = d.need, d.identity, d.chunk
CANDIDATE, DIAGNOSTIC = party.CANDIDATE, party.DIAGNOSTIC
HITS = HELD_HITS = (0x09149270, 0x09149286)
CLASSIFIED_HITS = ()
KIND = 'held_bag_sort_excluded_action_producer'
TYPE_CATEGORY = 'guard'
POCKET, POINTER, COUNT = 0x0203AC7A, 0x0203AC9C, 0x0203ACA0
PRODUCER = 0x0911195C
TABLE = 0x09167808
TASKS = 0x030050D0
CALLBACKS = {12: 0x0910FCB8, 13: 0x0910FC84, 14: 0x0910FC50, 15: 0x0910FC1C, 16: 0x0910FBE8}
MODES = {12: 0, 13: 1, 14: 3, 15: 2, 16: 4}
SOURCE_IDS = {'cfru-item.c': {'local': 'cfru-item.c',
                 'repository': 'kapibarasan000/CFRU-JP',
                 'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                 'path': 'src/item.c',
                 'size': 55431,
                 'sha256': '885c2ae9fa78d145eec1eca4333104b6fdd90a1d5afbbe191e0bc3398e740922',
                 'git_blob_sha': 'ea5302c0dc2bb9fc92e665aab6015a27ff4275d7'}}
SPECS = [(152115548, 'literal', (3, 152115588)),
 (152115550, 'mem', (True, 'half', 3, 3, 6)),
 (152115552, 'addi', (2, 3, 1)),
 (152115554, 'imm', ('cmp', 3, 1)),
 (152115556, 'branch', (0, 152115582)),
 (152115558, 'imm', ('cmp', 2, 3)),
 (152115560, 'branch', (1, 152115576)),
 (152115562, 'imm', ('mov', 2, 3)),
 (152115564, 'literal', (1, 152115592)),
 (152115566, 'literal', (3, 152115596)),
 (152115568, 'mem', (False, 'word', 1, 3, 0)),
 (152115570, 'literal', (3, 152115600)),
 (152115572, 'mem', (False, 'byte', 2, 3, 0)),
 (152115574, 'bx', (14,)),
 (152115576, 'imm', ('mov', 2, 4)),
 (152115578, 'literal', (1, 152115604)),
 (152115580, 'jump', (152115566,)),
 (152115582, 'imm', ('mov', 2, 2)),
 (152115584, 'literal', (1, 152115608)),
 (152115586, 'jump', (152115566,)),
 (152108008, 'shift', ('lsl', 2, 0, 2)),
 (152108010, 'literal', (3, 152108044)),
 (152108012, 'add', (2, 2, 0)),
 (152108014, 'shift', ('lsl', 2, 2, 3)),
 (152108016, 'add', (3, 3, 2)),
 (152108018, 'imm', ('mov', 2, 4)),
 (152108020, 'push', (16, True)),
 (152108022, 'shift', ('lsl', 4, 0, 0)),
 (152108024, 'mem', (False, 'half', 2, 3, 12)),
 (152108060, 'shift', ('lsl', 2, 0, 2)),
 (152108062, 'literal', (3, 152108096)),
 (152108064, 'add', (2, 2, 0)),
 (152108066, 'shift', ('lsl', 2, 2, 3)),
 (152108068, 'add', (3, 3, 2)),
 (152108070, 'imm', ('mov', 2, 2)),
 (152108072, 'push', (16, True)),
 (152108074, 'shift', ('lsl', 4, 0, 0)),
 (152108076, 'mem', (False, 'half', 2, 3, 12)),
 (152108112, 'shift', ('lsl', 2, 0, 2)),
 (152108114, 'literal', (3, 152108148)),
 (152108116, 'add', (2, 2, 0)),
 (152108118, 'shift', ('lsl', 2, 2, 3)),
 (152108120, 'add', (3, 3, 2)),
 (152108122, 'imm', ('mov', 2, 3)),
 (152108124, 'push', (16, True)),
 (152108126, 'shift', ('lsl', 4, 0, 0)),
 (152108128, 'mem', (False, 'half', 2, 3, 12)),
 (152108164, 'shift', ('lsl', 2, 0, 2)),
 (152108166, 'literal', (3, 152108200)),
 (152108168, 'add', (2, 2, 0)),
 (152108170, 'shift', ('lsl', 2, 2, 3)),
 (152108172, 'add', (3, 3, 2)),
 (152108174, 'imm', ('mov', 2, 1)),
 (152108176, 'push', (16, True)),
 (152108178, 'shift', ('lsl', 4, 0, 0)),
 (152108180, 'mem', (False, 'half', 2, 3, 12)),
 (152108216, 'shift', ('lsl', 2, 0, 2)),
 (152108218, 'literal', (3, 152108252)),
 (152108220, 'add', (2, 2, 0)),
 (152108222, 'shift', ('lsl', 2, 2, 3)),
 (152108224, 'add', (3, 3, 2)),
 (152108226, 'imm', ('mov', 2, 0)),
 (152108228, 'push', (16, True)),
 (152108230, 'shift', ('lsl', 4, 0, 0)),
 (152108232, 'mem', (False, 'half', 2, 3, 12))]
LITERALS = {152115588: 33795188,
 152115592: 152467456,
 152115596: 33795228,
 152115600: 33795232,
 152115604: 152467460,
 152115608: 152467452,
 152108044: 50352336,
 152108096: 50352336,
 152108148: 50352336,
 152108200: 50352336,
 152108252: 50352336}
ARRAYS = [(152467452, 2, (12, 4)), (152467456, 3, (12, 16, 4)), (152467460, 4, (12, 13, 16, 4))]
ACTION_TABLE = {4: (138270721, 135310809),
 12: (152343147, 152108217),
 13: (152343142, 152108165),
 14: (152343151, 152108113),
 15: (152343155, 152108061),
 16: (152343160, 152108009)}
CALLBACK_TEXT_LITERALS = {152108048: 152343182, 152108100: 152343177, 152108152: 152343173, 152108204: 152343168, 152108256: 152343164}
TEXTS = [{'address': 152343151,
  'size': 4,
  'sha256': 'a0fbe2dadae3b34a621a2093a55de6a3931684a7b37f889e96b28a345088b69d'},
 {'address': 152343155,
  'size': 5,
  'sha256': '7454d24ea6f1fb11b3c91833f255766c1a5356eb37be07f200899de5277fe0d2'},
 {'address': 152343173,
  'size': 4,
  'sha256': 'a0fbe2dadae3b34a621a2093a55de6a3931684a7b37f889e96b28a345088b69d'},
 {'address': 152343177,
  'size': 5,
  'sha256': '7454d24ea6f1fb11b3c91833f255766c1a5356eb37be07f200899de5277fe0d2'}]
FIXED_WINDOWS = [{'address': 152108008,
  'size': 18,
  'sha256': '25d7adc94e27be1ac605b2d64b7bc99a34e8a00b60adf8688ebdbfa224097e2d'},
 {'address': 152108044,
  'size': 8,
  'sha256': 'f0e96df29f3285ce4ff902e44ba410f4b2beca2e455121b3935f92c910a068ba'},
 {'address': 152108060,
  'size': 18,
  'sha256': '9a1ffa4b0dddb6062f35ea0ac2c159dfcb954e3f45edc8c4cd5444d89b89398d'},
 {'address': 152108096,
  'size': 8,
  'sha256': '48cf7bfa93e819d4b12b868942b8826a397e1c42a9165c17cd481f2c88758013'},
 {'address': 152108112,
  'size': 18,
  'sha256': '70ee92c4c33d1a3a7750ecd74fe20c7c4421f4e7e7e3870038f069787b2f138b'},
 {'address': 152108148,
  'size': 8,
  'sha256': '9e7a036e92b042365cc74e431fa759c5eddaf9826a4931c4a368bda9d13eb006'},
 {'address': 152108164,
  'size': 18,
  'sha256': '981f22d394185667476bb8ac29b837e1082dbe6d70268629620e4e85f3c1a40a'},
 {'address': 152108200,
  'size': 8,
  'sha256': '6629572f9990dd385b4769bc0b0322d8ba26db67ba149afbde519ec081e0828c'},
 {'address': 152108216,
  'size': 18,
  'sha256': 'e0465ae6239573c25f5dabfdff3e5d7a3b418623e3e03cef928063147ff9dc41'},
 {'address': 152108252,
  'size': 8,
  'sha256': '0e3dcb63bb9e88d69ec4827e2e58d467f45668c06d45771be74a0fbe8cc4cd01'},
 {'address': 152115548,
  'size': 64,
  'sha256': 'ff9120ea04f0c6cad903ceb056ddf97be1549ed31b1f3edb7891f4370a5131c8'},
 {'address': 152343151,
  'size': 9,
  'sha256': '679fb1412134d0b0b77cd1af126be4fef220d05b293f6698e8098f03b2e9612a'},
 {'address': 152343173,
  'size': 9,
  'sha256': '679fb1412134d0b0b77cd1af126be4fef220d05b293f6698e8098f03b2e9612a'},
 {'address': 152467452,
  'size': 2,
  'sha256': '05565904fe65aa6c49626e54ca2b786e0a4d5403047decefe2b91444e7063992'},
 {'address': 152467456,
  'size': 3,
  'sha256': '4341ffb17ea9401ff2302662f5fce184d312c56a5c590a0c2e2a3ecc0c0a8bab'},
 {'address': 152467460,
  'size': 4,
  'sha256': '047b53c27ecca407499a9d2d58dbc3fefae2fd32f31e77230b0bd377931ada66'},
 {'address': 152467496,
  'size': 8,
  'sha256': '90d04165cac74fc515914f593768c8739b10bf955ecbee60f2c55bcba454ea4c'},
 {'address': 152467560,
  'size': 40,
  'sha256': '7c3b49e6e30fbad428a8e22390e9213a22d7c57be6eac4e041a250e064724c99'}]
INS = {a: party.Ins(a, kind, tuple(args)) for a, kind, args in SPECS}
BLOCKS = {'bag_sort_excluded_action_producer': tuple(INS.values())}
WINDOWS = {f'bag_sort_window_{j}': (row['address'], row['size']) for j, row in enumerate(FIXED_WINDOWS)}
encoded, exact = engine.encoded, engine.exact
CLAIMS = dict(
    proof_scope='conditional_local_sort_producer_unknown_retention',
    root_verified=False, full_story_reachability_claimed=False,
    actual_runtime_execution_observed=False, global_unreachability_proven=False,
    all_other_writers_excluded=False, indirect_reference_completeness_claimed=False,
    retired_or_reusable_proven=False, donor_eligible=False, donor_leased=False,
    opaque_callee_effects_proven=False, universal_heap_or_irq_lifetime_proven=False,
    padding_classified=False, all_hit_bytes_consumed=False)
ROOT = dict(kind='unrooted_local_producer_guard', entry=PRODUCER,
            candidate_input_hook=0x091118EC, hook_caller_bound=False,
            context_pointer_writer=0x09111970, context_count_writer=0x09111974,
            parent_accepted_context_table=0x08413D60, candidate_extended_table=TABLE,
            extended_table_dispatch_bound=False, excluded_actions=[14, 15],
            excluded_confirmation_modes=[2, 3])
CONTRACT = dict(
    entry='未結合のLoadBagSorterMenuOptionsを局所条件付きで評価する。StartMenu自然到達や登録根を持つとは扱わない。',
    producer='実命令がpocket半wordから配列pointerとcountをstoreする。各選択肢のmembershipは生成した最小配列の構造読取。text consumer実行ではない。',
    inputs='pocketの全u16域を等値分岐で3classに分ける。正規pocket0/1/2を代表実行し、その他の値を自然play有効入力とは主張しない。',
    callbacks='callback14/15と文字列が残っていても生成actionにない。各callback prefixのmode storeは未登録の局所診断であり自然選択ではない。',
    resources='producerはopaque call0、heap0、window0、task0。read-before-write RAMはpocket2byteのみ。callback prefixはtaskId0..15と通常ABI stackだけを条件とする。',
    boundary='4textの各EOSを固定するが根付きconsumerへ結合しないので2hitはいずれも未知。存在するtableやsource名から退役・再利用安全を推論しない。')
OBLIGATIONS = [
    '現ROMの登録根からTrySetupSortBag、context producer、extended action table消費への実経路を束縛する。',
    '対象ID14/15を生成する別の正当なwriterを実証するか、全参照/間接参照と退役を別に証明する。',
    '09149270と09149286の両側textをEOS込みで実consumerへ結合してから最小型を判断する。',
    '有限guardを全caller到達不能、自然play、owner移管、donor容量へ昇格させない。']


def bind_semantics(raw):
    for ins in INS.values():
        need(chunk(raw, ins.address, ins.size) == encoded(ins), 'Bag並替え意味命令不一致 ' + hex(ins.address))
    for address, value in LITERALS.items():
        need(d.u32(raw, address) == value, 'Bag並替えliteral不一致')
    d.signed(raw, FIXED_WINDOWS)
    for address, size, actions in ARRAYS:
        need(chunk(raw, address, size) == bytes(actions), '最小action配列不一致')
    for action, values in ACTION_TABLE.items():
        need(tuple(d.u32(raw, TABLE + action * 8 + j * 4) for j in range(2)) == values,
             '対象action登録cell不一致')
    for address, value in CALLBACK_TEXT_LITERALS.items():
        need(d.u32(raw, address) == value, 'callback text source literal不一致')
    for row in TEXTS:
        value = chunk(raw, row['address'], row['size'])
        need(value[-1] == 255 and all(x < 248 for x in value[:-1]), '完全literal/EOS境界のみ')


class Machine(rt.Machine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ram_reads = []
    def read(self, address, size):
        if not 0x08000000 <= address < 0x0A000000:
            self.ram_reads.append((address, size))
        return super().read(address, size)


def pocket_class(pocket):
    need(type(pocket) is int and 0 <= pocket <= 0xFFFF, 'u16 pocketのみ')
    return 1 if pocket == 1 else 2 if pocket == 2 else 0


def _compose_selected(raw, pocket, initial_fields=None):
    """局所producerのみ。旧Bag/Use/Toss proofは再実行しない。"""
    pocket_class(pocket)
    expected = [(POCKET, 2, pocket)]
    need(initial_fields is None or exact(initial_fields, expected), 'pocket以外の出力fixture注入を拒否')
    mem = {}
    rt.setmem(mem, POCKET, 2, pocket)
    machine = Machine(raw, PRODUCER, memory=mem, instructions=INS).run()
    pointer, count = rt.getmem(machine.mem, POINTER, 4), rt.getmem(machine.mem, COUNT, 1)
    need(machine.calls == [] and machine.ram_reads == [(POCKET, 2)], 'opaqueなしの最小入口field')
    need(machine.writes == [(0x09111970, POINTER, 4), (0x09111974, COUNT, 1)], '実writer2件のみ')
    selected = {0: (0x09167804, 4, [12, 13, 16, 4]),
                1: (0x091677FC, 2, [12, 4]), 2: (0x09167800, 3, [12, 16, 4])}[pocket_class(pocket)]
    actions = list(chunk(raw, pointer, count))
    need((pointer, count, actions) == selected, '実producerの選択集合')
    need(not {14, 15}.intersection(actions), '対象2actionを生成しない')
    return dict(pocket=pocket, pocket_class=pocket_class(pocket), pointer=pointer,
                count=count, actions=actions, semantic_steps=machine.steps,
                actual_writes=[dict(instruction=pc, address=a, size=n) for pc, a, n in machine.writes],
                required_initial_fields=[dict(address=POCKET, size=2)], opaque_boundaries=0,
                registered_root_bound=False, text_consumer_executed=False)


def compose_selected(raw, pocket, initial_fields=None):
    bind_semantics(raw)
    return _compose_selected(raw, pocket, initial_fields)


def callback_mode_prefix(raw, action, task_id=0):
    """実mode writerまでの局所診断。callback自身を登録根とみなさない。"""
    bind_semantics(raw)
    need(type(action) is int and action in CALLBACKS, '閉じた5callback集合')
    need(type(task_id) is int and 0 <= task_id < 16, '有効task indexのみ')
    entry = CALLBACKS[action]
    machine = Machine(raw, entry, {0: task_id}, instructions=INS)
    while machine.pc != entry + 18:
        machine.step()
    address = TASKS + 40 * task_id + 12
    value = rt.getmem(machine.mem, address, 2)
    need(value == MODES[action], '実callback mode writer')
    need(machine.calls == [] and machine.ram_reads == [], 'prefixに外部効果なし')
    need(machine.external_writes() == [(address, 2)], 'task mode以外の外部writeなし')
    return dict(action=action, entry=entry, task_id=task_id, mode=value,
                mode_writer=entry + 16, source='unrooted_actual_callback_prefix',
                registered_root_bound=False, text_consumer_executed=False,
                semantic_steps=machine.steps)


def sources_bind(review, sources):
    need(set(sources) == set(SOURCE_IDS) and exact(review['source_bindings'], SOURCE_IDS), '固定source集合')
    for key, row in SOURCE_IDS.items():
        value = sources[key]
        need(identity(value) == {k: row[k] for k in ('size', 'sha256')}, '固定source全文identity')
        need(hashlib.sha1(b'blob ' + str(len(value)).encode() + b'\0' + value).hexdigest() == row['git_blob_sha'],
             '固定source Git blob')
    need(b'//BAG_MENU_OPTION_BY_MOST,' in sources['cfru-item.c'] and
         b'//BAG_MENU_OPTION_BY_LEAST,' in sources['cfru-item.c'] and
         b'void LoadBagSorterMenuOptions(void)' in sources['cfru-item.c'], '固定source producer対照')


def protected_windows(review):
    need(exact(review['windows'], FIXED_WINDOWS), '最小保護窓固定')
    return copy.deepcopy(FIXED_WINDOWS)


def witness_geometry(evidence):
    raise ValueError('未知維持guardは型witnessを発行しない')


def evidence_template(hit):
    raise ValueError('未知維持guardはhitを分類しない')


def make_review(raw, hits):
    selected = [h for h in hits if h.get('address') in HITS]
    need([h['address'] for h in selected] == list(HITS), '候補2hitの順序/重複/欠落')
    return dict(schema_version=1, required_candidate=copy.deepcopy(CANDIDATE),
                diagnostic_input=copy.deepcopy(DIAGNOSTIC), source_bindings=copy.deepcopy(SOURCE_IDS),
                hits=copy.deepcopy(selected), windows=copy.deepcopy(FIXED_WINDOWS),
                root=copy.deepcopy(ROOT), claims=copy.deepcopy(CLAIMS), input_contract=copy.deepcopy(CONTRACT),
                texts=copy.deepcopy(TEXTS), required_obligations=list(OBLIGATIONS), classified_hits=[])


def validate_held_proof(proof, current_candidate_measured=False):
    need(type(current_candidate_measured) is bool, '明示current gate boolean')
    need(exact(proof, held_proof_template(current_candidate_measured)), '閉じた未知維持proof')
    return True


def held_proof_template(current_candidate_measured=False):
    need(type(current_candidate_measured) is bool, '明示current gate boolean')
    return dict(status='PASS_BAG_SORT_TWO_HITS_REMAIN_UNKNOWN', count=0, hits=[], held_hits=list(HITS),
                source_bindings=copy.deepcopy(SOURCE_IDS), root=copy.deepcopy(ROOT),
                producer_cases=copy.deepcopy(CASE_PROOFS), callback_mode_prefixes=copy.deepcopy(CALLBACK_PROOFS),
                partition=dict(domain='u16 pocket read', classes=['==1', '==2', 'otherwise'],
                               exhaustive_for_local_equalities=True, natural_input_validity_claimed=False),
                selected_confirmation_modes=[0, 1, 4], excluded_confirmation_modes=[2, 3],
                required_obligations=list(OBLIGATIONS), protected_windows=len(FIXED_WINDOWS),
                protected_bytes=sum(w['size'] for w in FIXED_WINDOWS),
                current_candidate_measured=current_candidate_measured,
                all_inherited_fields_unchanged=True, **copy.deepcopy(CLAIMS))


def _regions(raw, inherited, review, sources):
    selected = [h for h in inherited['hits'] if h.get('address') in HITS]
    need(exact(review, make_review(None, selected)), '不変review JSONのみ')
    need(exact(inherited['candidate'], CANDIDATE), 'currentとdiagnosticを分離')
    for hit in selected:
        need(type(hit['address']) is int and hit['accepted'] is False and hit['owner_candidates'] == [] and
             type(hit['size']) is int and hit['size'] == 4 and hit['classification'] == 'UNCLASSIFIED' and
             hit['kind'] == 'ALL_BYTE_START_U32_ALL_ROM_MIRRORS', '既存のowner-external未知hitのみ')
        d.signed(raw, hit)
    protected_windows(review)
    sources_bind(review, sources)
    bind_semantics(raw)
    proof = held_proof_template()
    proof['producer_cases'] = [compose_selected(raw, pocket) for pocket in (0, 1, 2)]
    proof['callback_mode_prefixes'] = [callback_mode_prefix(raw, action) for action in CALLBACKS]
    validate_held_proof(proof)
    return [], proof


def regions(raw, inherited, review, sources, root=None):
    need(identity(raw) == inherited['candidate'] == CANDIDATE, 'whole current必須、旧診断で昇格しない')
    rows, proof = _regions(raw, inherited, review, sources)
    proof['current_candidate_measured'] = True
    validate_held_proof(proof, True)
    return rows, proof

# 固定metadataのみ。実ROM断片、実行traceを保存しない。
CASE_PROOFS = [{'pocket': 0,
  'pocket_class': 0,
  'pointer': 152467460,
  'count': 4,
  'actions': [12, 13, 16, 4],
  'semantic_steps': 15,
  'actual_writes': [{'instruction': 152115568, 'address': 33795228, 'size': 4},
                    {'instruction': 152115572, 'address': 33795232, 'size': 1}],
  'required_initial_fields': [{'address': 33795194, 'size': 2}],
  'opaque_boundaries': 0,
  'registered_root_bound': False,
  'text_consumer_executed': False},
 {'pocket': 1,
  'pocket_class': 1,
  'pointer': 152467452,
  'count': 2,
  'actions': [12, 4],
  'semantic_steps': 13,
  'actual_writes': [{'instruction': 152115568, 'address': 33795228, 'size': 4},
                    {'instruction': 152115572, 'address': 33795232, 'size': 1}],
  'required_initial_fields': [{'address': 33795194, 'size': 2}],
  'opaque_boundaries': 0,
  'registered_root_bound': False,
  'text_consumer_executed': False},
 {'pocket': 2,
  'pocket_class': 2,
  'pointer': 152467456,
  'count': 3,
  'actions': [12, 16, 4],
  'semantic_steps': 14,
  'actual_writes': [{'instruction': 152115568, 'address': 33795228, 'size': 4},
                    {'instruction': 152115572, 'address': 33795232, 'size': 1}],
  'required_initial_fields': [{'address': 33795194, 'size': 2}],
  'opaque_boundaries': 0,
  'registered_root_bound': False,
  'text_consumer_executed': False}]
CALLBACK_PROOFS = [{'action': 12,
  'entry': 152108216,
  'task_id': 0,
  'mode': 0,
  'mode_writer': 152108232,
  'source': 'unrooted_actual_callback_prefix',
  'registered_root_bound': False,
  'text_consumer_executed': False,
  'semantic_steps': 9},
 {'action': 13,
  'entry': 152108164,
  'task_id': 0,
  'mode': 1,
  'mode_writer': 152108180,
  'source': 'unrooted_actual_callback_prefix',
  'registered_root_bound': False,
  'text_consumer_executed': False,
  'semantic_steps': 9},
 {'action': 14,
  'entry': 152108112,
  'task_id': 0,
  'mode': 3,
  'mode_writer': 152108128,
  'source': 'unrooted_actual_callback_prefix',
  'registered_root_bound': False,
  'text_consumer_executed': False,
  'semantic_steps': 9},
 {'action': 15,
  'entry': 152108060,
  'task_id': 0,
  'mode': 2,
  'mode_writer': 152108076,
  'source': 'unrooted_actual_callback_prefix',
  'registered_root_bound': False,
  'text_consumer_executed': False,
  'semantic_steps': 9},
 {'action': 16,
  'entry': 152108008,
  'task_id': 0,
  'mode': 4,
  'mode_writer': 152108024,
  'source': 'unrooted_actual_callback_prefix',
  'registered_root_bound': False,
  'text_consumer_executed': False,
  'semantic_steps': 9}]
