#!/usr/bin/env python3
"""旧mainを実行しない2段階の稼得入力/新shop支出生成。成功saveは再利用する。"""
from pathlib import Path
import pr16_research_photo as old
import pr16_research_shop_ui as patch
ROOT=Path(__file__).resolve().parents[1]
C='tools/mgba_pr16_research_natural_spending.c'

def generate(seed):
    import pr16_research_lifecycle_v2 as gen
    gen.OUT.mkdir(parents=True,exist_ok=True)
    source=old.generate(seed).decode();token='int main(int argc,char**argv){'
    patch.need(source.count(token)==1 and source.count(old.CANDIDATE['sha256'])==1,'unique inherited main and parent')
    source=source.replace(token,'int accepted_photo_main(int argc,char**argv){').replace(old.CANDIDATE['sha256'],patch.CANDIDATE['sha256'])
    mining=(ROOT/'tools/mgba_pr16_research_mining.c').read_text()
    patch.need(mining.count(token)==1,'unique retained mining main')
    source+='\n'+mining.replace(token,'int accepted_mining_main(int argc,char**argv){')
    return (source+'\n'+(ROOT/C).read_text()).encode()

def fixture(seed):return old.fixture(seed)

def generate_ui(seed):
    source=generate(seed).decode();token='int main(int argc,char**argv){'
    patch.need(source.count(token)==1,'unique monetary main retained but not called')
    return (source.replace(token,'int measured_monetary_main(int argc,char**argv){')+'\n'+(ROOT/'tools/mgba_pr16_research_shop_ui_only.c').read_text()).encode()
