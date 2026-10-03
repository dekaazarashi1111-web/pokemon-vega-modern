#!/usr/bin/env python3
"""研究wild専用の生成・ABI束縛。過去nativeのmainは呼ばない。"""
from pathlib import Path
import pr16_research_bug as prior
ROOT = Path(__file__).resolve().parents[1]
C = 'tools/mgba_pr16_research_wild.c'
CANDIDATE = prior.CANDIDATE
METHODS = ('fishing', 'ecology')
ABI = {
    'tools/mgba_pr16_learnset_battle.c': '#define QOL_KEY_LEFT 0x0020U',
    'tools/mgba_modernization_p02_stage71_acceptance_smoke.c': '    P02S_CB2_BAG = 0x081089E5U,',
}
need, identity = prior.need, prior.identity


def generate(seed: bytes) -> bytes:
    for path, declaration in ABI.items():
        need((ROOT / path).read_text().splitlines().count(declaration) == 1,
             'unique source-proven input/UI ABI: ' + path)
    import pr16_research_lifecycle_v2 as base
    base.OUT.mkdir(parents=True, exist_ok=True)
    source = prior.generate(seed).decode()
    token = 'int main(int argc,char**argv){'
    need(source.count(token) == 1, 'one old main; never execute accepted cases')
    source = source.replace(token, 'int accepted_bug_main(int argc,char**argv){')
    # This probe embeds the QOL host base, not the larger P02 driver. Import
    # only its two needed constants, with their original declarations bound.
    aliases = '\n#define QOL_KEY_LEFT 0x0020U\n#define P02S_CB2_BAG 0x081089E5U\n'
    return (source + aliases + (ROOT / C).read_text()).encode()
