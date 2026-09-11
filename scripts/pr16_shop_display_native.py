#!/usr/bin/env python3
"""Physical shop repair, every catalogue page, and read-only VRAM regression.

Three fresh original-ROM controls must reproduce damaged world tilemaps.
Eleven repaired cases must preserve those tilemaps through purchase, cancel,
denial, save, cold Continue and revisiting the actual NPC. No graphics writes
or function calls are injected after the physical-observation boundary.
"""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_shop_display_repair as repair
probe=repair.probe;shop=probe.shop;r=probe.r;need=r.need;identity=r.identity
SELF='scripts/pr16_shop_display_native.py'
TEST='tests/test_pr16_shop_display_repair.py'
WORKFLOW='.github/workflows/pr16-shop-display-repair.yml'
OUT=ROOT/'.local/pr16-shop-display-native'
SOURCE_SHA='16eda36fade0e8ef0ec3dc0b45b22c9776969f557aedc6ac25f1b65ffc09848c'
SCOPE='PR16_REPAIRED_SHOP_PHYSICAL_GRAPHICS_SAVE'
CONTROL_SCOPE='PR16_ORIGINAL_SHOP_GRAPHICS_REPRODUCTION'
CASES=dict(shop.CASES);CASES['cancel-last']=(1043,2)
CONTROLS=('eelektross','cancel-first','cancel-page')
GRAPHICS_C=r'''
static uint8_t d_world_reference[6144];
static unsigned d_world_captures,d_world_checks,d_world_differences,d_layouts,d_bad_layouts;
static void d_capture_world(struct mCore *c){
 a_require(read16(c,0x04000008U)==0x1F08U && read16(c,0x0400000AU)==0x1D41U && read16(c,0x0400000CU)==0x1C42U && read16(c,0x0400000EU)==0x1E43U,"field BG controls differ from audited banks");
 b_copy(c,0x0600E000U,d_world_reference,sizeof(d_world_reference));++d_world_captures;
}
static void d_check_world(struct mCore *c){
 uint8_t now[6144];b_copy(c,0x0600E000U,now,sizeof(now));unsigned differences=0;
 for(unsigned i=0;i<sizeof(now);++i)differences+=now[i]!=d_world_reference[i];
 ++d_world_checks;d_world_differences+=differences;
 fprintf(stderr,"WORLD_TILEMAP capture=%u observation=%u changed_bytes=%u\n",d_world_captures,d_world_checks,differences);
}
static void d_check_layout(struct mCore *c){
 unsigned id=read8(c,G_STATE+96U),bad=0U;++d_layouts;
 if(id>=32U){++d_bad_layouts;return;}
 unsigned p=0x02020430U+12U*id;
 unsigned base=read16(c,p+6U),size=read8(c,p+3U)*read8(c,p+4U);
 bad|=read8(c,p)!=0U || read8(c,p+1U)!=8U || read8(c,p+2U)!=1U || read8(c,p+3U)!=21U || read8(c,p+4U)!=16U || read8(c,p+5U)!=15U || base!=1U;
 bad|=base+size>408U || base+size>532U || 0x8000U+32U*(base+size)>0xE000U;
 for(unsigned i=0;i<32U;++i){
  unsigned q=0x02020430U+12U*i,other=read16(c,q+6U),end=other+read8(c,q+3U)*read8(c,q+4U);
  if(i!=id && !read8(c,q) && other<base+size && base<end)bad=1U;
 }
 d_bad_layouts+=bad;fprintf(stderr,"SHOP_LAYOUT observation=%u page=%u base=%u tiles=%u invalid=%u\n",d_layouts,read8(c,G_STATE+95U),base,size,bad);
 char label[80];int n=snprintf(label,sizeof(label),"page-%u-observation-%u",read8(c,G_STATE+95U),d_layouts);
 a_require(n>0 && n<(int)sizeof(label),"shop layout screenshot path overflow");g_shot(label);
}
'''


def replace(text,before,after):
    need(text.count(before)==1,'display observer insertion is ambiguous');return text.replace(before,after,1)


def controller(sha,control=False):
    r.layer.source.checked(ROOT/shop.SOURCE,SOURCE_SHA)
    text=probe.controller(sha);text=replace(text,probe.SCOPE,CONTROL_SCOPE if control else SCOPE)
    text=replace(text,' {"insufficient-bp",1012,3},{"missing-ring",1012,4}\n};',' {"insufficient-bp",1012,3},{"missing-ring",1012,4},\n {"cancel-last",1043,2}\n};')
    needle='static bool g_menu(struct mCore *c)';text=replace(text,needle,GRAPHICS_C+'\n'+needle)
    needle='static void g_menu_check(struct mCore *c,unsigned omitted){';text=replace(text,needle,needle+'\n d_check_world(c);d_check_layout(c);')
    text=replace(text,'if(++stable==60U){c->setKeys(c,0);return;}','if(++stable==60U){d_check_world(c);c->setKeys(c,0);return;}')
    needle=' /* The only actions after this boundary are physical input and reads. */';text=replace(text,needle,' d_capture_world(c);\n'+needle)
    needle='reloaded=b_frames;b_position(c,96,5,24,20);';text=replace(text,needle,needle+'d_capture_world(c);d_check_world(c);')
    needle=r' printf("\"manual_saves'
    inserted=r''' printf("\"graphics\":{\"world_captures\":%u,\"world_checks\":%u,\"world_difference_bytes\":%u,\"layout_checks\":%u,\"invalid_layouts\":%u},",d_world_captures,d_world_checks,d_world_differences,d_layouts,d_bad_layouts);
'''
    return replace(text,needle,inserted+needle)


def expected(name,sha,control):
    need(name in CASES and (not control or name in CONTROLS),'unknown repaired/control shop case')
    row=shop.expected('cancel-page' if name=='cancel-last' else name)
    if name=='cancel-last':row.update(case=name,item=1043,catalog_index=44,pages=8)
    row.update(rom_sha256=sha,scope=CONTROL_SCOPE if control else SCOPE);return row


def validate(raw,name,code,sha,control=False):
    need(type(code) is int and code==0,'repaired/control shop did not exit integer zero')
    value=shop.common.strict_json(raw);want=expected(name,sha,control)
    need(type(value) is dict and set(value)==set(want)|{'total_frames','witness','graphics'},'shop graphics schema differs')
    for key,target in want.items():need(shop.common.same_typed(value[key],target),'shop graphics data differs: '+key)
    normalized={k:v for k,v in value.items() if k!='graphics'}
    if name=='cancel-last':normalized.update(case='cancel-page',item=1035,catalog_index=36,pages=7)
    normalized.update(rom_sha256=r.ROM_SHA,scope=shop.SCOPE)
    shop.validate(json.dumps(normalized).encode(),'cancel-page' if name=='cancel-last' else name,code)
    g=value['graphics'];need(type(g) is dict and set(g)=={'world_captures','world_checks','world_difference_bytes','layout_checks','invalid_layouts'},'shop graphics witness keys differ')
    need(all(type(v) is int and 0<=v<=1000000 for v in g.values()),'shop graphics witness is not bounded integer')
    need(g['world_captures']==2,'shop graphics did not observe both fresh cores')
    need(g['world_checks']==(2 if name=='missing-ring' else want['pages']+5),'world checks missing from physical sequence')
    need(g['layout_checks']==(0 if name=='missing-ring' else want['pages']+2),'shop pages/revisit geometry checks missing')
    if control:need(g['world_difference_bytes']>0 and g['invalid_layouts']>0,'original shop did not reproduce expected corrupting allocation')
    else:need(g['world_difference_bytes']==0 and g['invalid_layouts']==0,'repaired shop damaged world tilemaps or used overlapping layout')
    return value


def run():
    OUT.mkdir(parents=True,exist_ok=True);m=shop.base.load();seed=ROOT/m.SEED
    parent=r.layer.source.checked(ROOT/r.ROM,r.ROM_SHA);r.layer.source.checked(seed,m.SEED_SHA)
    recipe=repair.run();candidate=(repair.OUTPUT/'candidate.gba').read_bytes();need(identity(candidate)==recipe['candidate'],'shop candidate differs from twice-built recipe')
    (OUT/'recipe.json').write_bytes(r.stable(recipe));(OUT/'renderer.c').write_bytes((repair.OUTPUT/'renderer.c').read_bytes())
    paths={SELF,TEST,WORKFLOW,repair.SELF,probe.SELF,shop.SELF,shop.SOURCE,shop.base.SELF,shop.base.PARENT,shop.base.PARENT_C,
           probe.OVERLAY,'overlays/modernization_mega_shop/modernization_mega_shop.h','overlays/bp_shop_runtime/bp_shop_libc.c','overlays/save_migration/save_migration.c','overlays/save_migration/save_migration.h',
           shop.CATALOG,shop.CHECKPOINT,'tools/modernization_mega_shop.py','tools/rom_allocator.py','config/rom_regions.csv','vendor/upstream/CFRU-JP/charmap.tbl',
           'scripts/pr16_repaired_acceptance.py','scripts/pr16_p07_preserved_layer.py','scripts/pr16_evolution_learning_repair.py','scripts/pr16_integration_continuation.py','scripts/run_modernization_p03_fullslots_e2e.py',
           'config/active_play_baseline.json','design/active_play_baseline.md',*(p for p,_ in m.EMBEDDED)}
    cfg=json.loads((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_bytes());p02=next(d for d in cfg['domains'] if d['id']=='p02')
    for binding in (p02['runner'],*p02['dependencies']):
        need(shop.common.identity(ROOT/binding['path'])=={k:binding[k] for k in ('size','sha256')},'shop observer embedded dependency differs');paths.add(binding['path'])
    bindings={p:identity((ROOT/p).read_bytes()) for p in sorted(paths)};guards=[];results=[];tasks=[]
    with tempfile.TemporaryDirectory(prefix='shop-graphics-native-',dir=ROOT/'.local') as td:
        work=Path(td)
        for i,(src,target) in enumerate(m.EMBEDDED):(work/target).write_text(m.embed((ROOT/src).read_text(),'display_embedded_'+str(i)))
        (work/'pr16_shop_breeding_helpers.c').write_text(m.embed((ROOT/shop.base.PARENT_C).read_text(),'display_helpers'))
        variants={'control':parent,'repaired':candidate}
        for variant,raw in variants.items():
            sha=identity(raw)['sha256'];rom=work/(variant+'.gba');rom.write_bytes(raw)
            source=OUT/(variant+'-controller.c');source.write_text(controller(sha,variant=='control'));binary=work/(variant+'-runner')
            _,_,process=shop.common.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),str(source),'-lmgba','-o',str(binary)],OUT/(variant+'-compile'),120)
            need(shop.common.require_exited(process)==0,'shop graphics C compile failed')
            for guard in m.GUARDS:
                stdout,stderr,process=shop.common.capture([str(binary),'--guard-check',guard],OUT/(variant+'-guard-'+guard),10);m.validate_guard(stdout,stderr,process);guards.append(variant+':'+guard)
            for name in (CONTROLS if variant=='control' else CASES):
                private=work/(variant+'-'+name+'.srm');shutil.copyfile(seed,private);tasks.append((variant,name,sha,rom,binary,private))
        def one(task):
            variant,name,sha,rom,binary,private=task;prefix=OUT/(variant+'-'+name)
            stdout,stderr,process=shop.common.capture([str(binary),str(rom),str(private),sha,m.SEED_SHA,name,str(prefix)],prefix,240)
            try:
                result=validate(stdout,name,shop.common.require_exited(process),sha,variant=='control');need(b'mGBA[' not in stderr,'shop graphics emulator warning');return dict(variant=variant,case=name,result=result,process=process)
            except (ValueError,RuntimeError,KeyError,TypeError) as error:return dict(variant=variant,case=name,error=str(error),process=process)
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(one,tasks))
        for variant,raw in variants.items():need((work/(variant+'.gba')).read_bytes()==raw,'shop native ROM changed')
    need(bindings=={p:identity((ROOT/p).read_bytes()) for p in bindings},'shop graphics sources/baseline changed');r.layer.source.checked(ROOT/r.ROM,r.ROM_SHA);r.layer.source.checked(seed,m.SEED_SHA)
    failures=[row for row in results if 'error' in row]
    report=dict(schema_version=1,status='FAIL' if failures else 'DATA_AND_VRAM_PASS_VISUAL_REVIEW_REQUIRED',scope=SCOPE,candidate=recipe['candidate'],parent=identity(parent),recipe=recipe,results=results,failures=failures,guard_checks=guards,sources=bindings,
                actual_new_processes=len(tasks),repaired_processes=sum(row['variant']=='repaired' and 'result' in row for row in results),repaired_cores=sum(row['result']['fresh_cores'] for row in results if row['variant']=='repaired' and 'result' in row),
                control_processes=len(CONTROLS),control_cores=2*len(CONTROLS),old_runs_relabelled=0,all_nine_catalogue_pages_observed=not failures,visual_review_complete=False,
                natural_capture_accepted=False,battle_connection_accepted=False,full_p05_acceptance=False,release_ready=False)
    (OUT/'result.json').write_bytes(r.stable(report));need(not failures,'shop graphics native failure; inspect original traces')
    return report

if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False))
