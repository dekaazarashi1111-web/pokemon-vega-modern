"""Credits4件のgap横断を検証し、未結合serializerを未知に保持する。I/Oなし。"""
from __future__ import annotations
import copy
import hashlib
import json
import re
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as party
need, identity, chunk = d.need, d.identity, d.chunk
CANDIDATE, DIAGNOSTIC = party.CANDIDATE, party.DIAGNOSTIC
TYPE_CATEGORY = 'boundary'
KIND = 'held_credits_alignment_gap_observation'
# GUARDSへの登録専用。HITSを受入hitへ昇格させてはならない。
CLASSIFIED_HITS = ()
HELD_HITS = (0x083E239B, 0x083E24C3, 0x083E2563, 0x083E258F)
HITS = HELD_HITS
SOURCE_IDS = {'pret-credits.c': {'local': 'pret-credits.c',
                    'repository': 'pret/pokefirered',
                    'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                    'path': 'src/credits.c',
                    'size': 50032,
                    'sha256': '96690b500af63cc588b2ca8060f4af5b1a69a99797870099831d77a32027af25',
                    'git_blob_sha': '8f89652a0f864ae4fcacd67cccff3a4d3441f350'},
 'pret-strings.c': {'local': 'pret-strings.c',
                    'repository': 'pret/pokefirered',
                    'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                    'path': 'src/strings.c',
                    'size': 96631,
                    'sha256': '08e3799f20dd90ae937808be25721d28c3465b4f2ebaba2e71321e52f72465c1',
                    'git_blob_sha': 'c09955503495e79c237d7f6d5164c666c7502600'},
 'pret-defines.h': {'local': 'pret-defines.h',
                    'repository': 'pret/pokefirered',
                    'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                    'path': 'include/gba/defines.h',
                    'size': 2518,
                    'sha256': '4356e895d7108dedd2c788bbbe98e0948778712a4ea6374193bdc1a851efe69b',
                    'git_blob_sha': '5521e942c00cc2c263b842ae7608dfb7ac881a76'},
 'pret-charmap.txt': {'local': 'pret-charmap.txt',
                      'repository': 'pret/pokefirered',
                      'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                      'path': 'charmap.txt',
                      'size': 21853,
                      'sha256': '4da662317b3b5109a52064f9012d85b644d1dbf0f3f24243374aeef4cf25f061',
                      'git_blob_sha': 'b9d0ed9de00d05fc303bb987a5aa634b19009b47'}}
LAYOUT_ROWS = [{'hit': 138290075,
  'table_index': 1,
  'pointer_pair': {'address': 138264084,
                   'size': 8,
                   'sha256': '123e6b8ea5ab0f8c45d3a298ee8088de7aa80e261357bb9d3e38bd50db77d288'},
  'title': {'address': 138290048,
            'size': 27,
            'sha256': '055e7dadc1face2ad56cd48b49c314dccd6317284edba9ae25c939ea352a181e'},
  'gap': {'address': 138290075,
          'size': 1,
          'sha256': '6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d'},
  'names': {'address': 138290076,
            'size': 22,
            'sha256': '01c87c4f075b3bb23e5920a09f4cb64789a05dd70f7cc41aa70c4c4be2fa9a7c'},
  'source_title_symbol': 'gCreditsString_Art_Director_Battle_Director',
  'source_names_symbol': 'gCreditsString_Ken_Sugimori_Shigeki_Morimoto'},
 {'hit': 138290371,
  'table_index': 6,
  'pointer_pair': {'address': 138264144,
                   'size': 8,
                   'sha256': '06d672c19c3bc2fc6d1bacca738582c84e528eb0c41f6391c15aac5c124e1b87'},
  'title': {'address': 138290352,
            'size': 18,
            'sha256': '504a12620bc2f5aca3012ae08b036665a979e27dea3a0da8c792c5c8ad0cd17e'},
  'gap': {'address': 138290370,
          'size': 2,
          'sha256': '96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630a09cfc7'},
  'names': {'address': 138290372,
            'size': 22,
            'sha256': 'b447f575f87ec5ae774b9dc998785b13fc6e0bae7b34dfc2617da833715cc85f'},
  'source_title_symbol': 'gCreditsString_Graphic_Designers_2',
  'source_names_symbol': 'gCreditsString_Ken_Sugimori_Hironobu_Yoshida'},
 {'hit': 138290531,
  'table_index': 10,
  'pointer_pair': {'address': 138264192,
                   'size': 8,
                   'sha256': '9429753dd20150f953fa23ffba5b19309289b1d5a4a962e7b25c036c67e1f6c9'},
  'title': {'address': 138290516,
            'size': 15,
            'sha256': '4215fb5d381fd0ab6497403f623e48d40983beb18353233e50e19f2e4f944ab9'},
  'gap': {'address': 138290531,
          'size': 1,
          'sha256': '6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d'},
  'names': {'address': 138290532,
            'size': 30,
            'sha256': 'e83f9ab4016cf132320f8cf0ec272432110a364c71d247a65671b2b933734532'},
  'source_title_symbol': 'gCreditsString_Game_Designers_2',
  'source_names_symbol': 'gCreditsString_Hitomi_Sato_Shigeru_Ohmori_Tadashi_Takahashi'},
 {'hit': 138290575,
  'table_index': 11,
  'pointer_pair': {'address': 138264204,
                   'size': 8,
                   'sha256': '29a24a97681b1a688372810561bd20432661f76b6885039d611f457a7d85618e'},
  'title': {'address': 138290564,
            'size': 11,
            'sha256': '83e8b97f9f834dba9662710c8086e654fe8316436f3e420b5b845fb263a4430a'},
  'gap': {'address': 138290575,
          'size': 1,
          'sha256': '6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d'},
  'names': {'address': 138290576,
            'size': 21,
            'sha256': '7ecf4b7e6b174f837a094590cbddeaaff9281133f9ad53d13ee764bf7d897851'},
  'source_title_symbol': 'gCreditsString_Game_Scenario',
  'source_names_symbol': 'gCreditsString_Hitomi_Sato_Satoshi_Tajiri'}]
FIXED_WINDOWS = tuple(copy.deepcopy(row[key]) for row in LAYOUT_ROWS
                      for key in ('pointer_pair', 'title', 'gap', 'names'))
CLAIMS = dict(
    proof_scope='bounded_layout_observation_and_unknown_retention_only',
    padding_classified=False,
    all_hit_bytes_consumed=False,
    actual_runtime_execution_observed=False,
    actual_registered_root_recomposed=False,
    japanese_serializer_bound=False,
    linker_layout_bound=False,
    gap_unreferenced_proven=False,
    indirect_reference_completeness_claimed=False,
    natural_play_reachability_proven=False,
    universal_heap_or_irq_lifetime_proven=False,
    donor_eligible=False,
    donor_leased=False,
)
REQUIRED_OBLIGATIONS = (
    '日本語object全体を生成する固定source・文字変換・serializerの一致',
    '同一objectの境界・alignment・linker配置を現candidateへ独立束縛',
    'gapを文字列や他のデータと誤認しない領域分離と未参照境界の根',
    '対象namesを実登録rootから実consumerへ合成する有限条件',
    '全4byteの型が閉じること。3byteの文字消費から先行1byteへ拡張しない',
)
SOURCE_LIMITATIONS = dict(
    public_alignment_declaration_verified=True,
    public_alignment_macro_verified=True,
    selected_public_text_count=8,
    exact_rom_text_matches=0,
    japanese_object_build_available=False,
    exact_linker_map_available=False,
    complete_reference_domain_available=False,
)


def exact(actual, expected):
    """bool/intの取り違えも許さない閉じたJSON比較。"""
    return json.dumps(actual, sort_keys=True, separators=(',', ':'), allow_nan=False) == json.dumps(
        expected, sort_keys=True, separators=(',', ':'), allow_nan=False)


def source_bindings(review, sources):
    need(type(sources) is dict and set(sources) == set(SOURCE_IDS), 'exact public source set')
    need(exact(review['source_bindings'], SOURCE_IDS), 'immutable public source identities')
    for key, spec in SOURCE_IDS.items():
        raw = sources[key]
        need(type(raw) is bytes and identity(raw) == {k: spec[k] for k in ('size', 'sha256')},
             'whole pinned public source: ' + key)
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        need(blob == spec['git_blob_sha'], 'independent Git blob binding: ' + key)
    need(b'#define ALIGNED(n) __attribute__((aligned(n)))' in sources['pret-defines.h'],
         'exact public alignment declaration semantics')


def protected_windows(review):
    need(exact(review['windows'], list(FIXED_WINDOWS)), 'immutable bounded observation windows')
    return copy.deepcopy(list(FIXED_WINDOWS))


def public_text_prefix(symbol, sources):
    """選択した単純literalのglyph列のみ。ROM serializer全体の証明にはしない。"""
    expression = (r'^ALIGNED\(4\) const u8 ' + re.escape(symbol)
                  + r'\[\] = _\(("(?:[^"\\]|\\.)*")\);$')
    declarations = re.findall(expression, sources['pret-strings.c'].decode(), re.M)
    need(len(declarations) == 1, 'one exact aligned public declaration')
    literal = json.loads(declarations[0])
    need(literal and all(c == '\n' or c == ' ' or c.isascii() and c.isalpha() for c in literal),
         'selected public glyph sequence excludes placeholders and controls')
    charmap = sources['pret-charmap.txt'].decode()
    encoded = []
    for char in literal:
        token = '\\n' if char == '\n' else char
        pattern = r"^'" + re.escape(token) + r"'[ \t]*=[ \t]*([0-9A-F]{2})(?:[ \t]*@[^\n]*)?[ \t]*$"
        values = re.findall(pattern, charmap, re.M)
        need(len(values) == 1, 'one-byte glyph mapping from pinned public source')
        encoded.append(int(values[0], 16))
    return bytes(encoded)


def finite_literal_extent(raw, window):
    """root到達や描画を主張せず、既知開始点からEOSまでの必要条件だけ検査。"""
    d.signed(raw, window)
    value = chunk(raw, window['address'], window['size'])
    need(value[-1] == 255 and 255 not in value[:-1], 'exact first-EOS extent')
    need(all(c < 248 or c in (254, 255) for c in value), 'literal/newline/EOS only')
    return value


def split_hit(hit, size, text_windows):
    """文字列に属する部分と証明のない部分を分離。所属は型の受入ではない。"""
    need(type(hit) is int and type(size) is int and size > 0, 'positive integer hit window')
    need(type(text_windows) is list, 'explicit text windows')
    intervals = []
    for window in text_windows:
        need(type(window) is dict and set(window) == {'address', 'size'}, 'closed extent geometry')
        a, n = window['address'], window['size']
        need(type(a) is int and type(n) is int and n > 0, 'positive integer text extent')
        intervals.append((a, a + n))
    intervals.sort()
    need(all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:])), 'nonoverlapping text extents')
    covered = [a for a in range(hit, hit + size) if any(lo <= a < hi for lo, hi in intervals)]
    uncovered = [a for a in range(hit, hit + size) if a not in covered]
    return dict(text_extent_bytes=covered, unproven_bytes=uncovered,
                all_hit_bytes_in_text_extents=not uncovered)


def boundary_observations(raw, sources):
    """観測差分を返すだけで、TypedRegionを生成しない。"""
    d.signed(raw, list(FIXED_WINDOWS))
    credits = sources['pret-credits.c'].decode()
    block = credits.split('static const struct CreditsTextHeader sCreditsTexts[] = {', 1)
    need(len(block) == 2, 'unique credits header table')
    entries = re.findall(r'\{\s*(gCreditsString_\w+),\s*(gCreditsString_\w+),\s*(?:FALSE|TRUE)\s*\}',
                         block[1].split('};', 1)[0])
    result = []
    for row in LAYOUT_ROWS:
        table = row['pointer_pair']['address']
        title, names = row['title'], row['names']
        need(table == 0x083DBE08 + row['table_index'] * 12, 'fixed title/names pair cell')
        need(d.u32(raw, table) == title['address'] and d.u32(raw, table + 4) == names['address'],
             'actual bounded title and names pointers')
        need(entries[row['table_index']] == (row['source_title_symbol'], row['source_names_symbol']),
             'public table index-to-symbol correspondence only')
        texts = [finite_literal_extent(raw, w) for w in (title, names)]
        end = title['address'] + title['size']
        need(end == row['gap']['address'] and end + row['gap']['size'] == names['address'],
             'exact EOS-gap-next-start partition')
        need(names['address'] == row['hit'] + 1 and names['address'] % 4 == 0,
             'observed names alignment; not serializer provenance')
        need((end + 3) & ~3 == names['address'], 'observed nearest-aligned gap, not an ownership proof')
        split = split_hit(row['hit'], 4, [dict(address=w['address'], size=w['size']) for w in (title, names)])
        need(split == dict(text_extent_bytes=list(range(row['hit'] + 1, row['hit'] + 4)),
                           unproven_bytes=[row['hit']], all_hit_bytes_in_text_extents=False),
             'exactly one gap byte and three names bytes')
        public_rows = []
        for role, value, window in zip(('title', 'names'), texts, (title, names)):
            prefix = public_text_prefix(row['source_' + role + '_symbol'], sources)
            need(prefix != value[:-1], 'public English text must not be promoted to Japanese serializer')
            public_rows.append(dict(role=role, source_symbol=row['source_' + role + '_symbol'],
                                    public_literal_glyph_count=len(prefix),
                                    observed_rom_literal_byte_count=len(value) - 1,
                                    exact_glyph_sequence_matches=False))
        result.append(dict(hit=row['hit'], table_index=row['table_index'],
                           title=copy.deepcopy(title), names=copy.deepcopy(names), gap=copy.deepcopy(row['gap']),
                           split=split, public_source_comparison=public_rows,
                           observed_names_alignment=4, required_hit_size=4,
                           real_consumer_recomposed=False, classified=False))
    return result


def make_review(raw, hits):
    """rawは他consumerとのAPI互換だけ。I/OもROM識別の推測もしない。"""
    selected = [h for h in hits if h.get('address') in HELD_HITS]
    need(len(selected) == 4 and [h['address'] for h in selected] == list(HELD_HITS),
         'exact ordered held hits')
    return dict(schema_version=1, required_candidate=copy.deepcopy(CANDIDATE),
                diagnostic_input=copy.deepcopy(DIAGNOSTIC), source_bindings=copy.deepcopy(SOURCE_IDS),
                hits=copy.deepcopy(selected), layout_rows=copy.deepcopy(LAYOUT_ROWS),
                windows=copy.deepcopy(list(FIXED_WINDOWS)), claims=copy.deepcopy(CLAIMS),
                source_limitations=copy.deepcopy(SOURCE_LIMITATIONS),
                required_obligations=list(REQUIRED_OBLIGATIONS), classified_hits=[])


def witness_geometry(evidence):
    """このguardはあらゆる型証拠の発行を拒否する。"""
    raise ValueError('alignment observation does not issue a typed witness; four hits remain unknown')


def held_proof_template(current_candidate_measured=False):
    """guard出力の閉じた契約。観測metadataを型証拠として解釈しない。"""
    need(type(current_candidate_measured) is bool, 'explicit measurement-state boolean')
    observations = []
    for row, glyph_counts in zip(LAYOUT_ROWS, ((33, 34), (23, 34), (20, 48), (19, 31))):
        comparisons = []
        for role, glyph_count in zip(('title', 'names'), glyph_counts):
            comparisons.append(dict(role=role, source_symbol=row['source_' + role + '_symbol'],
                                    public_literal_glyph_count=glyph_count,
                                    observed_rom_literal_byte_count=row[role]['size'] - 1,
                                    exact_glyph_sequence_matches=False))
        observations.append(dict(hit=row['hit'], table_index=row['table_index'],
                                 title=copy.deepcopy(row['title']), names=copy.deepcopy(row['names']),
                                 gap=copy.deepcopy(row['gap']),
                                 split=dict(text_extent_bytes=list(range(row['hit'] + 1, row['hit'] + 4)),
                                            unproven_bytes=[row['hit']], all_hit_bytes_in_text_extents=False),
                                 public_source_comparison=comparisons, observed_names_alignment=4,
                                 required_hit_size=4, real_consumer_recomposed=False, classified=False))
    return dict(status='PASS_FOUR_CREDITS_HITS_REMAIN_UNKNOWN', count=0, hits=[],
                held_hits=list(HELD_HITS), new_classified_bytes=0,
                source_bindings=copy.deepcopy(SOURCE_IDS),
                source_limitations=copy.deepcopy(SOURCE_LIMITATIONS),
                observations=observations, required_obligations=list(REQUIRED_OBLIGATIONS),
                protected_windows=len(FIXED_WINDOWS),
                protected_bytes=sum(w['size'] for w in FIXED_WINDOWS),
                all_inherited_fields_unchanged=True,
                current_candidate_measured=current_candidate_measured, **copy.deepcopy(CLAIMS))


def validate_held_proof(proof, current_candidate_measured=False):
    """欠落・余計なclaim・bool偽装・padding分類を全てfail-closedで拒否。"""
    need(type(proof) is dict and exact(proof, held_proof_template(current_candidate_measured)),
         'exact closed four-hit unknown-retention guard proof')
    return True


def _regions(raw, inherited, review, sources):
    selected = [h for h in inherited['hits'] if h.get('address') in HELD_HITS]
    expected = make_review(None, selected)
    need(exact(review, expected), 'closed held-padding review: no promoted claim or re-sealed metadata')
    need(exact(inherited['candidate'], CANDIDATE), 'inherited current identity remains separate from diagnostic')
    for hit in selected:
        need(type(hit['address']) is int and hit['accepted'] is False and hit['owner_candidates'] == []
             and type(hit['size']) is int and hit['size'] == 4 and hit['classification'] == 'UNCLASSIFIED'
             and hit['kind'] == 'ALL_BYTE_START_U32_ALL_ROM_MIRRORS', 'same owner-external unknown4byte hit')
        d.signed(raw, hit)
    protected_windows(review)
    source_bindings(review, sources)
    observations = boundary_observations(raw, sources)
    proof = held_proof_template()
    proof['observations'] = observations
    validate_held_proof(proof)
    return [], proof


def regions(raw, inherited, review, sources, root=None):
    need(identity(raw) == inherited['candidate'] == CANDIDATE,
         'whole current candidate required; old diagnostic cannot verify current')
    empty, proof = _regions(raw, inherited, review, sources)
    proof['current_candidate_measured'] = True
    validate_held_proof(proof, current_candidate_measured=True)
    return empty, proof
