#!/usr/bin/env python3
"""予約owner内の現在の実sectionを正本化し、過去の空き表示を再使用しない。"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCHEDULER='content/modernization/pr16_dex_scheduler_checkpoint.json'
CODEC_BASE=0x09FC0998;CODEC_SIZE=5022;CODEC_END=0x09FC22EC
def need(x,m):
 if not x:raise ValueError(m)
def occupied():
 d=json.loads((ROOT/SCHEDULER).read_bytes());rows=[dict(name='accepted_codec',address=CODEC_BASE,size=CODEC_SIZE)]
 rows.extend({k:s[k]for k in('name','address','size')}for s in d['link']['sections']if CODEC_BASE<=s['address']<CODEC_END)
 need(len(rows)==4 and all(s['address']+s['size']<=CODEC_END for s in rows),'exact current codec and three scheduler sections')
 return sorted(rows,key=lambda r:r['address'])
def available():
 cursor=CODEC_BASE;out=[]
 for row in occupied():
  need(row['address']>=cursor,'nonoverlapping current subowners')
  if cursor<row['address']:out.append(dict(address=cursor,size=row['address']-cursor))
  cursor=row['address']+row['size']
 if cursor<CODEC_END:out.append(dict(address=cursor,size=CODEC_END-cursor))
 return out
def require_codec_lease(address,size):
 need(size>0 and CODEC_BASE<=address<address+size<=CODEC_END,'bounded codec reservation request')
 collisions=[r['name']for r in occupied()if address<r['address']+r['size']and r['address']<address+size]
 need(not collisions,'current scheduler/codec subowner collision: '+', '.join(collisions))
 need(any(w['address']<=address and address+size<=w['address']+w['size']for w in available()),'one actual free subspan')
