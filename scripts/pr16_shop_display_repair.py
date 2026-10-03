#!/usr/bin/env python3
"""Deterministic, bounded field-shop renderer repair above exact 635fd890.

BG0 uses character base 0x8000; the world tilemaps start at 0xE000. The old
532..867 content allocation overwrites those tilemaps AND frame tiles 532..540.
Reserve content tiles 1..336, below message window 408..511, and keep the border
inside the visible tilemap. Economy, catalogue, save schema and callers remain.
"""
import json
from pathlib import Path
import shutil
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_shop_display_probe as probe
r=probe.r;need=r.need;identity=r.identity
SELF='scripts/pr16_shop_display_repair.py'
OUTPUT=ROOT/'.local/pr16-shop-display-repair'
CHANGES=(('    template.tilemap_top = 0u;','    template.tilemap_top = 1u;'),
         ('    template.base_block = FN_GET_STD_WINDOW_BASE_TILE();','    template.base_block = 1u;'))
GEOMETRY=dict(bg_character_base=0x8000,content_base_tile=1,width=21,height=16,left=8,top=1,
              message_tiles=[408,512],frame_tiles=[532,541],world_tilemaps=[0xE000,0xF800],ui_tilemap=[0xF800,0x10000])


def validate_geometry(g):
    need(type(g) is dict and set(g)==set(GEOMETRY),'fixed field graphics keys differ')
    for key,want in GEOMETRY.items():
        actual=g[key]
        if type(want) is list:
            need(type(actual) is list and len(actual)==len(want) and all(type(a) is int and a==b for a,b in zip(actual,want)), 'fixed field graphics range differs: '+key)
        else:
            need(type(actual) is int and actual==want,'fixed field graphics integer differs: '+key)
    begin=g['bg_character_base']+32*g['content_base_tile'];end=begin+32*g['width']*g['height']
    need(0x8000<begin<end<=g['bg_character_base']+32*g['message_tiles'][0],'shop overlaps message tiles')
    need(end<=g['world_tilemaps'][0] and end<=g['bg_character_base']+32*g['frame_tiles'][0],'shop overlaps world/frame tiles')
    need(1<=g['left'] and g['left']+g['width']<=29 and 1<=g['top'] and g['top']+g['height']<=19,'shop frame outside screen')
    return dict(content_bytes=[begin,end],content_tiles=[g['content_base_tile'],g['content_base_tile']+g['width']*g['height']],world_and_frame_overlap=False)


def build(parent,work):
    need(identity(parent)==dict(size=33554432,sha256=r.ROM_SHA),'exact shop display parent required')
    source=r.layer.source.checked(ROOT/probe.OVERLAY,probe.OVERLAY_SHA).decode();changed=source
    for before,after in CHANGES:
        need(changed.count(before)==1 and after not in changed,'display source preimage differs');changed=changed.replace(before,after,1)
    payload=json.loads((ROOT/probe.shop.CHECKPOINT).read_bytes())['payload'];header=probe.header()
    original,symbols,toolchain=probe.production._compile_runtime(ROOT,payload['code_address'],header)
    need(identity(original)==dict(size=payload['code_size'],sha256=payload['code_sha256']),'original shop compiler reproduction differs')
    at=payload['code_offset'];need(parent[at:at+len(original)]==original,'shop original code changed')
    target=work/'renderer-root';shutil.copytree(ROOT/'overlays',target/'overlays');(target/probe.OVERLAY).write_text(changed)
    code,relinked,compiler=probe.production._compile_runtime(target,0x08000000+probe.START,header)
    need('render_menu' in symbols and 'render_menu' in relinked,'shop renderer was inlined unexpectedly')
    where=symbols['render_menu']-0x08000000
    veneer=(b'\xc0\x46' if where&2 else b'')+r.layer.veneer(8,relinked['render_menu'])
    layout=json.loads((ROOT/r.ROM).with_suffix('.json').read_bytes())['allocation'];requests=[];owners=0
    for i,row in enumerate(layout['allocations']):
        need(row['sequence']==i and row['end_exclusive']==row['start']+row['size'],'display allocation sequence differs')
        need(identity(parent[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'display parent allocation bytes changed')
        request={k:row[k] for k in ('name','region','size','alignment','start','owner','purpose','content_sha256')}
        if row['start']<=where and where+len(veneer)<=row['end_exclusive']:
            owners+=1;patched=bytearray(parent[row['start']:row['end_exclusive']]);offset=where-row['start'];patched[offset:offset+len(veneer)]=veneer;request['content_sha256']=identity(patched)['sha256']
        requests.append(request)
    need(owners==1,'shop renderer entry ownership differs')
    requests.append(dict(name='pr16-shop-display-safe-content',region='integration_modules',size=len(code),alignment=4,owner='P05',purpose='safe field-shop renderer: bounded tiles 1..336 and top border 1',content_sha256=identity(code)['sha256']))
    r.layer.source.checked(ROOT/'config/rom_regions.csv',r.layer.REGIONS_SHA)
    plan=r.layer.build_allocation_report_from_csv(ROOT/'config/rom_regions.csv',requests)
    need(plan['summaries']['overlap_count']==0 and plan['allocations'][-1]['start']==probe.START,'shop safe renderer allocation differs')
    need(parent[probe.START:probe.START+len(code)]==b'\xff'*len(code),'shop safe renderer allocation occupied')
    need(0<=where-at<=len(original)-len(veneer),'renderer entry outside original implementation')
    candidate=bytearray(parent);candidate[where:where+len(veneer)]=veneer;candidate[probe.START:probe.START+len(code)]=code
    cursor=0
    for offset,size in sorted(((where,len(veneer)),(probe.START,len(code)))):
        need(candidate[cursor:offset]==parent[cursor:offset],'undeclared shop display change');cursor=offset+size
    need(candidate[cursor:]==parent[cursor:],'undeclared shop display trailing change')
    for row in plan['allocations']:need(identity(candidate[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'candidate allocation content differs')
    report=dict(schema_version=1,status='BUILT_NOT_NATIVE_ACCEPTED',parent=identity(parent),candidate=identity(candidate),allocation=plan,
                source_preimage_sha256=probe.OVERLAY_SHA,source_changes=[dict(before=a,after=b) for a,b in CHANGES],
                geometry=GEOMETRY,graphics_contract=validate_geometry(GEOMETRY),original_code=identity(original),new_code=identity(code),
                source_renderer=symbols['render_menu'],new_renderer=relinked['render_menu'],entry=dict(offset=where,before=parent[where:where+len(veneer)].hex(),after=veneer.hex()),
                original_toolchain=toolchain,repair_toolchain=compiler,renderer_source=identity(changed.encode()),header=identity(header),
                save_layout_changes=0,table_changes=0,economy_changes=0,active_baseline_changed=False,native_accepted=False,release_ready=False)
    return bytes(candidate),report,changed


def run():
    need(not any(p.is_symlink() for p in (OUTPUT,*OUTPUT.parents)),'unsafe shop repair output');OUTPUT.mkdir(parents=True,exist_ok=True)
    parent=r.layer.source.checked(ROOT/r.ROM,r.ROM_SHA);results=[]
    for iteration in range(2):
        with tempfile.TemporaryDirectory(prefix='shop-repair-',dir=ROOT/'.local') as td:results.append(build(parent,Path(td)))
    candidate,report,source=results[0]
    need(candidate==results[1][0] and report==results[1][1] and source==results[1][2],'independent shop repair builds differ')
    (OUTPUT/'candidate.gba').write_bytes(candidate);(OUTPUT/'renderer.c').write_text(source)
    patches={}
    for name,left,right in (('parent-to-shop-display-repaired.bps',parent,candidate),('shop-display-repaired-to-parent.bps',candidate,parent)):
        patch=r.layer.create_bps(left,right);need(r.layer.apply_bps(left,patch)==right,'shop repair patch round trip failed');(OUTPUT/name).write_bytes(patch);patches[name]=identity(patch)
    report.update(independent_repair_builds=2,full_clean_rebuild_claimed=False,patches=patches,
                  source_bindings={p:identity((ROOT/p).read_bytes()) for p in (SELF,probe.SELF,probe.OVERLAY,'tools/modernization_mega_shop.py','tools/rom_allocator.py','config/rom_regions.csv')})
    (OUTPUT/'candidate.json').write_bytes(r.stable(report));r.layer.source.checked(ROOT/r.ROM,r.ROM_SHA)
    return report

if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False))
