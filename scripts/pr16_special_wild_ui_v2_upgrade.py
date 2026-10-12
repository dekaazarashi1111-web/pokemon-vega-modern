#!/usr/bin/env python3
"""One-time hash-checked text transfer; actual source changes join the result commit."""
from pathlib import Path
import hashlib
import json
ROOT=Path(__file__).resolve().parents[1]
ALLOWED={'tools/mgba_pr16_special_wild_gameplay.c','scripts/pr16_special_wild_gameplay_native.py','tests/test_pr16_special_wild_gameplay_native.py'}
plan=json.loads((ROOT/'scripts/pr16_special_wild_ui_v2_source_edits.json').read_bytes())
if set(plan)!=ALLOWED:raise ValueError('source transfer scope')
outputs={}
for name,row in plan.items():
    raw=(ROOT/name).read_bytes()
    if hashlib.sha256(raw).hexdigest()==row['after']:continue
    if hashlib.sha256(raw).hexdigest()!=row['before']:raise ValueError('source preimage: '+name)
    lines=raw.decode().splitlines(True);previous=0
    for start,end,text in row['edits']:
        if not previous<=start<=end<=len(lines) or '\0' in text:raise ValueError('edit boundary')
        previous=end
    for start,end,text in reversed(row['edits']):lines[start:end]=text.splitlines(True)
    result=''.join(lines).encode()
    if hashlib.sha256(result).hexdigest()!=row['after']:raise ValueError('source postimage: '+name)
    outputs[name]=result
for name,raw in outputs.items():(ROOT/name).write_bytes(raw)
print('PASS: scoped source text transfer',len(outputs))
