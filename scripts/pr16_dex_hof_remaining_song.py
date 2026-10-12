"""既受入132曲・49sampleを保存する案。既存sourceファイルは変更しない。"""
from __future__ import annotations
import json
from unittest.mock import patch
import pr16_dex_hof_reference_gaps_song as prior

SOURCES=prior.SOURCES
REVIEW=prior.REVIEW
REVIEW_ID=prior.REVIEW_ID
need,identity=prior.need,prior.identity


def retained_sample_witnesses(inherited):
    out=list(inherited['song_extension']['asset_witnesses'])
    out+=inherited['song_extended_extension']['asset_witnesses']
    need(len(out)==43,'all43 original song sample witness records')
    for key,count in (('reference_delta',4),('reference_chain',2)):
        added=[dict(kind=r['kind'],asset=r['evidence']['asset'])
               for r in inherited[key]['witnesses'] if r['kind']in('pcm8','dpcm4')]
        need(len(added)==count,'exact immediate source sample count '+key)
        out += added
    need(len(out)==49,'all47 prior plus2 immediate-parent sample witness records')
    unique={(w['asset']['address'],w['asset']['size'],w['asset']['sha256'],w.get('kind',w.get('codec')))for w in out}
    need(len(unique)==49,'all49 exact distinct sample identities')
    return out


def preserve_assets(regions,witnesses):
    for w in witnesses:
        need(any(r.kind==w.get('kind',w.get('codec'))and r.evidence['asset']==w['asset']for r in regions),
             'every prior49 complete exact sample identity preserved')


def exact_song_set(songs,expected):
    need(len(expected)==132 and len(songs)==132 and {s['id']for s in songs}==set(expected),
         'exact old132 unique IDs without zero-hit discovery expansion')


def protect_root_roles(raw,regions,windows):
    prior.base.prior.signed(raw,list(windows))
    for w in windows:
        need(prior.base.BASE<=w['address']<w['address']+w['size']<=prior.base.BASE+len(raw),
             'positive finite in-ROM added root role')
        need(not any(w['address']<r.end and r.start<w['address']+w['size']for r in regions),
             'all132 modeled sound payloads disjoint from every added finite typed root role')


def no_new_audio(selected):
    need(not selected,'unchanged132 finite roots yield no newly classified audio')


def measured_regions(raw,inherited,engine,sources,typed_regions=(),additional_protected_windows=()):
    """意味review再束縛。正式入口song_regions以外からは診断だけで用いる。"""
    reviewed=(prior.ROOT/REVIEW).read_bytes()
    need(identity(reviewed)==REVIEW_ID,'reuse exact already accepted finite132 root review')
    captured=[]
    original=prior.extended.song_regions
    def capture(*args,**kwargs):
        result=original(*args,**kwargs)
        captured.append(result)
        return result
    with patch.object(prior.extended,'song_regions',side_effect=capture):
        selected,proof=prior.all_song_regions(raw,inherited,engine,sources,json.loads(reviewed),typed_regions)
    need(len(captured)==1,'one complete132-song model pass only')
    regions,songs,diagnostics=captured[0]
    expected=prior.extended.selected_song_ids(raw,sources,engine)
    previous_review=json.loads((prior.ROOT/prior.previous.REVIEW).read_bytes())
    expected.update(prior.previous.bind_roots(raw,previous_review,sources))
    expected.update(prior.bind_roots(raw,json.loads(reviewed),sources))
    exact_song_set(songs,expected)
    no_new_audio(selected)
    witnesses=retained_sample_witnesses(inherited);preserve_assets(regions,witnesses)
    protect_root_roles(raw,regions,additional_protected_windows)
    proof=dict(proof,inherited_song_count=132,additional_song_ids=[],combined_song_count=132,
               old_sample_witnesses_preserved=49,old_sample_unique_identities_preserved=49,
               immediate_parent_new_sample_witnesses_preserved=2,
               no_new_song_root_claimed=True,
               all_modeled_sound_payloads_checked_against_new_root_roles=True,
               extra_finite_root_role_count=len(additional_protected_windows),
               extra_finite_root_roles_identity=identity(prior.delta.canonical(list(additional_protected_windows))))
    proof['new_songs']=[]
    return selected,proof


def song_regions(raw,inherited,engine,sources,typed_regions=(),additional_protected_windows=()):
    need(identity(raw)==inherited['candidate']==prior.base.CANDIDATE,'strict whole current0641 candidate')
    need((inherited['classified'],inherited['unclassified'])==(661,213),'exact immediate accepted frontier')
    return measured_regions(raw,inherited,engine,sources,typed_regions,additional_protected_windows)
