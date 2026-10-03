#!/usr/bin/env python3
"""通常捕獲で実証した研究保存delegateの誤結合を固定recipeで修正する。"""
from __future__ import annotations
import hashlib
import json
import struct
from pathlib import Path

PARENT = {'size':33554432,'sha256':'0205af9bd2d92b1b3303195ab0cc84e5ea0f3de390ade15d9f8ce42a6dcdd1a0'}
CANDIDATE = {'size':33554432,'sha256':'23d584095f7bc0691e1582da447d6cd9a389d8698e061ea2de9f6eac03b63f48'}
CONFIG = 'config/research_economy_v1.json'
CONFIG_BLOB = '91b89a8312f231adf7dcdc59b6cf808f70ad7dc4'
OFFSET = 0x13BF67C
BEFORE = bytes.fromhex('95763709')
AFTER = bytes.fromhex('61763709')
CONTEXT_SHA = 'd4e3f4d9b2045d1faee4fe9e4d31098e2d165ab7a43e7a54c8f2db8af4f6a014'
# Bound exact target code, not a name-only or numeric-nearness guess.
TARGETS = [(0x1377660,52,'bf430c8e1e3986e52e62134a46aa4dbdf1df288ed6d40b4a3dc17f0889212ac6'),
           (0x1377694,104,'c360571f6777afee59f3fa17b192a5740a8c52369b494f0b033b276f574f87b3')]


def need(ok, message):
    if not ok: raise ValueError(message)


def identity(raw):
    return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def correct_config(raw):
    """One authoritative config edit, preserving formatting and all other keys."""
    header = ('blob '+str(len(raw))+'\0').encode()
    need(hashlib.sha1(header+raw).hexdigest()==CONFIG_BLOB,'canonical config preimage')
    old=b'"qol_save": "0x09377695"';new=b'"qol_save": "0x09377661"'
    need(raw.count(old)==1,'unique canonical delegate')
    result=raw.replace(old,new)
    before=json.loads(raw);after=json.loads(result)
    need(before['delegates']['qol_save']=='0x09377695','wrong old delegate')
    before['delegates']['qol_save']='0x09377661'
    need(before==after,'outside canonical field changes')
    return result


def apply(raw):
    need(identity(raw)==PARENT,'research save parent identity')
    need(raw[OFFSET:OFFSET+4]==BEFORE,'research save literal preimage')
    need(hashlib.sha256(raw[OFFSET-16:OFFSET+20]).hexdigest()==CONTEXT_SHA,'research persist context')
    for offset,size,digest in TARGETS:
        need(hashlib.sha256(raw[offset:offset+size]).hexdigest()==digest,'bound QOL delegate body')
    result=bytearray(raw);result[OFFSET:OFFSET+4]=AFTER;result=bytes(result)
    need(identity(result)==CANDIDATE,'research save candidate identity')
    need(result[:OFFSET]==raw[:OFFSET] and result[OFFSET+4:]==raw[OFFSET+4:],'outside literal changes')
    rollback=bytearray(result);rollback[OFFSET:OFFSET+4]=BEFORE
    need(bytes(rollback)==raw,'full rollback')
    return result, {'schema_version':1,'parent':PARENT,'candidate':CANDIDATE,
        'offset':OFFSET,'before':BEFORE.hex(),'after':AFTER.hex(),'context_sha256':CONTEXT_SHA,
        'changed_bytes':sum(a!=b for a,b in zip(BEFORE,AFTER)), 'rollback_verified':True,
        'canonical_config':CONFIG,'old_delegate':'VegaQolProduction_SaveLoadAdapter',
        'new_delegate':'VegaQolProduction_TrySavingDataAdapter','arm_compiles':0,
        'outside_declared_changes':0,'active_baseline_changed':False,
        'scope':'ResearchEconomy.persist_phase shared earn/spend/rank/recovery save delegate; not only wild',
        'unaffected_code':['wild generation','special move setter','manual save handler','save load handler bodies'],
        'affected_acceptance_not_inherited':['research persistence transactions on the new candidate']}
