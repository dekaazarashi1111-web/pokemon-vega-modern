#!/usr/bin/env python3
"""採掘専用の実入力検証。写真/虫取りの受入済み main は呼ばない。"""
from pathlib import Path
import pr16_research_bug as prior
ROOT = Path(__file__).resolve().parents[1]
C = 'tools/mgba_pr16_research_mining.c'
CANDIDATE = prior.CANDIDATE
CASES = ('mining-missing-badge', 'mining-missing-move', 'mining-earn-cold-cap')

def generate(seed: bytes) -> bytes:
    source = prior.generate(seed).decode()
    token = 'int main(int argc,char**argv){'
    prior.need(source.count(token) == 1, 'unique inherited main')
    return (source.replace(token, 'int accepted_bug_main(int argc,char**argv){') + '\n' + (ROOT/C).read_text()).encode()
