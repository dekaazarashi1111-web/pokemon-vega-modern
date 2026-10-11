#!/usr/bin/env python3
"""Compare the observed top=0 shop to a top=1-only renderer experiment.

The existing ROM/source/originals remain immutable. Only a branch to a compiled
renderer copy and an allocator-owned copy change in the experimental candidate.
This is causal diagnosis, NOT final integration or visual acceptance.
"""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT))
import pr16_shop_routes as shop
from tools import modernization_mega_shop as production
r=shop.repaired;need=r.need;identity=r.identity
SELF='scripts/pr16_shop_display_probe.py'
OVERLAY='overlays/modernization_mega_shop/modernization_mega_shop.c'
OVERLAY_SHA='116bafdf4b3e736d5baf42870a30ce7069d2aafbbf33548a97bf1640c88b4b2d'
START=0x15DDCD8
OUT=ROOT/'.local/pr16-shop-display-probe'
SCOPE='PR16_SHOP_DISPLAY_CAUSAL_EXPERIMENT_NOT_ACCEPTANCE'


def header():
    catalog=json.loads((ROOT/shop.CATALOG).read_bytes());mapping,tokens=production._charmap(ROOT)
    text=production._encode_text;c=production._c_bytes
    lines=['#ifndef MODERNIZATION_MEGA_SHOP_CATALOG_GENERATED_H','#define MODERNIZATION_MEGA_SHOP_CATALOG_GENERATED_H','','#define MEGA_SHOP_CATALOG_COUNT 45u','']
    entries=[]
    for row in catalog['entries']:
        symbol=f"gMegaShopRow{row['index']:02d}";raw=bytes.fromhex(row['row_text_hex'])
        need(raw==text(row['row_text'],mapping,tokens),'shop glyph catalogue differs')
        lines.append(c(symbol,raw));entries.append('    {'+f"{row['item_id']}u, {row['price_bp']}u, 0x{row['claim_flag']:04X}u, 1u, 0u, {symbol}"+'},')
    lines.extend([c('gMegaShopBalancePrefix',text('BP ',mapping,tokens)),c('gMegaShopDigitGlyphs',text('0123456789',mapping,tokens)[:-1],suffix='[10]'),c('gMegaShopTextNext',text('つぎ',mapping,tokens)),c('gMegaShopTextCancel',text('やめる',mapping,tokens)),
                  'static const MegaShopCatalogEntry gMegaShopCatalog[MEGA_SHOP_CATALOG_COUNT] = {',*entries,'};','','#endif /* MODERNIZATION_MEGA_SHOP_CATALOG_GENERATED_H */',''])
    raw='\n'.join(lines).encode('ascii');need(identity(raw)['sha256']==catalog['header_sha256'],'reconstructed original C header differs')
    return raw


def build(parent,work):
    need(identity(parent)==dict(size=33554432,sha256=r.ROM_SHA),'display parent differs')
    source=r.layer.source.checked(ROOT/OVERLAY,OVERLAY_SHA).decode()
    payload=json.loads((ROOT/shop.CHECKPOINT).read_bytes())['payload'];generated=header()
    original,symbols,toolchain=production._compile_runtime(ROOT,payload['code_address'],generated)
    need(identity(original)==dict(size=payload['code_size'],sha256=payload['code_sha256']),'original shop compiler reproduction differs')
    at=payload['code_offset'];need(parent[at:at+len(original)]==original,'candidate shop implementation differs')
    target=work/'variant-root';shutil.copytree(ROOT/'overlays',target/'overlays')
    old='    template.tilemap_top = 0u;';new='    template.tilemap_top = 1u;'
    need(source.count(old)==1 and new not in source,'shop coordinate source preimage differs')
    changed=source.replace(old,new,1);(target/OVERLAY).write_text(changed)
    code,relinked,compiler=production._compile_runtime(target,0x08000000+START,generated)
    need('render_menu' in symbols and 'render_menu' in relinked,'renderer was not independently emitted')
    where=symbols['render_menu']-0x08000000
    veneer=(b'\xc0\x46' if where&2 else b'')+r.layer.veneer(8,relinked['render_menu'])
    layout=json.loads((ROOT/r.ROM).with_suffix('.json').read_bytes())['allocation'];requests=[]
    for i,row in enumerate(layout['allocations']):
        need(row['sequence']==i and row['end_exclusive']==row['start']+row['size'],'allocation sequence differs')
        need(identity(parent[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'parent allocation bytes differ')
        request={k:row[k] for k in ('name','region','size','alignment','start','owner','purpose','content_sha256')}
        if row['start']<=where<row['end_exclusive']:
            before=bytearray(parent[row['start']:row['end_exclusive']]);offset=where-row['start'];before[offset:offset+len(veneer)]=veneer
            request['content_sha256']=identity(before)['sha256']
        requests.append(request)
    requests.append(dict(name='pr16-shop-display-top1-experiment',region='integration_modules',size=len(code),alignment=4,owner='P05',purpose='causal top-coordinate renderer experiment; not release',content_sha256=identity(code)['sha256']))
    r.layer.source.checked(ROOT/'config/rom_regions.csv',r.layer.REGIONS_SHA)
    plan=r.layer.build_allocation_report_from_csv(ROOT/'config/rom_regions.csv',requests)
    need(plan['summaries']['overlap_count']==0 and plan['allocations'][-1]['start']==START,'shop diagnostic allocation differs')
    need(parent[START:START+len(code)]==b'\xff'*len(code),'shop diagnostic allocation occupied')
    need(0<=where-at<=len(original)-len(veneer),'renderer entry outside original code')
    candidate=bytearray(parent);candidate[where:where+len(veneer)]=veneer;candidate[START:START+len(code)]=code
    cursor=0
    for offset,size in sorted(((where,len(veneer)),(START,len(code)))):
        need(candidate[cursor:offset]==parent[cursor:offset],'undeclared shop probe mutation');cursor=offset+size
    need(candidate[cursor:]==parent[cursor:],'undeclared shop probe tail mutation')
    report=dict(status='EXPERIMENTAL_NOT_ADOPTED',parent=identity(parent),candidate=identity(candidate),allocation=plan,
                source_sha256=OVERLAY_SHA,source_change=dict(before=old,after=new),original_code=identity(original),new_code=identity(code),
                source_symbols=symbols,new_symbols=relinked,entry=dict(offset=where,before=parent[where:where+len(veneer)].hex(),after=veneer.hex()),
                toolchain=toolchain,experimental_toolchain=compiler,renderer_source=identity(changed.encode()),header=identity(generated),
                save_layout_changes=0,table_changes=0,economy_changes=0,native_accepted=False,release_ready=False)
    return bytes(candidate),report,changed


def controller(sha):
    text=(ROOT/shop.SOURCE).read_text()
    for old,new in [(r.ROM_SHA,sha),(shop.SCOPE,SCOPE)]:
        need(text.count(old)==1,'shop controller projection preimage differs');text=text.replace(old,new,1)
    needle='static void g_state(struct mCore *c,const char *label){'
    extra='''\n unsigned id=read8(c,G_STATE+96U);\n fprintf(stderr,"DISPLAY bgcnt=%04x,%04x,%04x,%04x win=%u\\n",read16(c,0x04000008U),read16(c,0x0400000AU),read16(c,0x0400000CU),read16(c,0x0400000EU),id);\n if(id<32U){unsigned p=0x02020430U+12U*id;fprintf(stderr,"WINDOW bg=%u left=%u top=%u width=%u height=%u palette=%u base=%u\\n",read8(c,p),read8(c,p+1U),read8(c,p+2U),read8(c,p+3U),read8(c,p+4U),read8(c,p+5U),read16(c,p+6U));}\n'''
    need(text.count(needle)==1,'shop diagnostic insertion differs');return text.replace(needle,needle+extra,1)


def validate(raw,name,code,sha):
    need(type(code) is int and code==0,'shop probe did not exit zero')
    actual=shop.common.strict_json(raw);need(actual['rom_sha256']==sha and actual['scope']==SCOPE,'shop experimental identity differs')
    # Delegate structural/data checks on a COPY; raw output is never relabelled.
    normalized=dict(actual,rom_sha256=r.ROM_SHA,scope=shop.SCOPE)
    shop.validate(json.dumps(normalized).encode(),name,code);return actual


def run():
    OUT.mkdir(parents=True,exist_ok=True);m=shop.base.load();seed=ROOT/m.SEED
    parent=r.layer.source.checked(ROOT/r.ROM,r.ROM_SHA);r.layer.source.checked(seed,m.SEED_SHA)
    (OUT/'result.json').unlink(missing_ok=True)
    source_paths=(SELF,shop.SOURCE,shop.SELF,shop.base.PARENT_C,OVERLAY,'overlays/modernization_mega_shop/modernization_mega_shop.h','overlays/bp_shop_runtime/bp_shop_libc.c','overlays/save_migration/save_migration.c','overlays/save_migration/save_migration.h',shop.CATALOG,shop.CHECKPOINT,'tools/modernization_mega_shop.py','config/rom_regions.csv','vendor/upstream/CFRU-JP/charmap.tbl')
    bindings={p:identity((ROOT/p).read_bytes()) for p in source_paths};results=[];guards=[]
    with tempfile.TemporaryDirectory(prefix='shop-display-',dir=ROOT/'.local') as td:
        work=Path(td);candidate,recipe,overlay=build(parent,work)
        (OUT/'recipe.json').write_bytes(r.stable(recipe));(OUT/'renderer-top1.c').write_text(overlay)
        variants={'control':(parent,r.ROM_SHA),'top1':(candidate,identity(candidate)['sha256'])}
        for i,(src,target) in enumerate(m.EMBEDDED):(work/target).write_text(m.embed((ROOT/src).read_text(),'probe_embedded_'+str(i)))
        (work/'pr16_shop_breeding_helpers.c').write_text(m.embed((ROOT/shop.base.PARENT_C).read_text(),'probe_helpers'))
        tasks=[]
        for variant,(raw,sha) in variants.items():
            rom=work/(variant+'.gba');rom.write_bytes(raw);source=OUT/(variant+'-controller.c');source.write_text(controller(sha));binary=work/(variant+'-runner')
            _,_,process=shop.common.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),str(source),'-lmgba','-o',str(binary)],OUT/(variant+'-compile'),120)
            need(shop.common.require_exited(process)==0,'display controller compile failed')
            for guard in m.GUARDS:
                stdout,stderr,process=shop.common.capture([str(binary),'--guard-check',guard],OUT/(variant+'-guard-'+guard),10);m.validate_guard(stdout,stderr,process);guards.append(variant+':'+guard)
            for name in ('eelektross','cancel-first','cancel-page'):
                private=work/(variant+'-'+name+'.srm');shutil.copyfile(seed,private);tasks.append((variant,name,sha,rom,binary,private))
        def one(task):
            variant,name,sha,rom,binary,private=task;prefix=OUT/(variant+'-'+name)
            stdout,stderr,process=shop.common.capture([str(binary),str(rom),str(private),sha,m.SEED_SHA,name,str(prefix)],prefix,240)
            try:
                result=validate(stdout,name,shop.common.require_exited(process),sha);need(b'mGBA[' not in stderr,'display emulator warning');return dict(variant=variant,case=name,result=result,process=process)
            except (ValueError,RuntimeError,KeyError,TypeError) as error:return dict(variant=variant,case=name,error=str(error),process=process)
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(one,tasks))
        for variant,(raw,sha) in variants.items():need(identity((work/(variant+'.gba')).read_bytes())==identity(raw),'display runtime modified ROM')
    need(bindings=={p:identity((ROOT/p).read_bytes()) for p in bindings},'display source changed');r.layer.source.checked(ROOT/r.ROM,r.ROM_SHA);r.layer.source.checked(seed,m.SEED_SHA)
    failures=[row for row in results if 'error' in row]
    report=dict(status='DATA_PASS_VISUAL_REVIEW_REQUIRED' if not failures else 'FAIL',scope=SCOPE,recipe=recipe,results=results,guard_checks=guards,sources=bindings,
                new_native_processes=len(tasks),new_native_cores=sum(row['result']['fresh_cores'] for row in results if 'result' in row),visual_accepted=False,final_candidate_changed=False,release_ready=False)
    (OUT/'result.json').write_bytes(r.stable(report));need(not failures,'display experiment data failure');print(json.dumps(dict(status=report['status'],candidate=recipe['candidate'],new_native_processes=report['new_native_processes'],new_native_cores=report['new_native_cores'],visual_accepted=False)))

if __name__=='__main__':run()
