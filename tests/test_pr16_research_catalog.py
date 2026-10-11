"""全catalogの新規oracle。ROM/セーブ/旧nativeは必要としない。"""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest import mock
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_research_catalog as m

class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = m.load((ROOT / m.MODEL).read_bytes())
        cls.items = (ROOT / m.ITEMS).read_text()
        rom = bytearray(m.CANDIDATE['size']); offset = 0x13C1000
        for row in cls.model['shop']:
            data = m.encoded(row['row_text_hex']); item = row['item_key']
            values = (row['item_id'], row['point_cost'], row['quantity'],
                      m.UNLOCKS.index(row['unlock_key']), int(item in m.DAILY),
                      m.DAILY.get(item, 255), row['daily_limit'], 255, 0, offset + 0x08000000)
            struct.pack_into('<HHHBBBBBBI', rom, m.TABLE-0x08000000+row['index']*16, *values)
            rom[offset:offset+len(data)] = data; offset += len(data)
        for row in cls.model['dialogue']:
            b = m.encoded(row['encoded_hex']); at = row['runtime_address']-0x08000000
            rom[at:at+len(b)] = b
        cls.rom = bytes(rom)
        cls.native = [dict(binding='map98/3-background0',events=0x09413C50,
                           backgrounds=0x09413C14,script=0x093C0328,catalog=0,item=4,price=10,quantity=5),
                      dict(shop_open='catalog',eligible_count=23,window=1,callback=154924453,native_tasks=1)]
        cls.native += [dict(page=p,catalog_indices=list(range(p*5,min(23,p*5+5))),
                            frame=1000+200*p,screen_sha256=f'{p+1:064x}') for p in range(5)]
        cls.native += [dict(status='PASS',case=m.CASE,candidate_sha256=m.CANDIDATE['sha256'],
                           catalog_count=23,pages=5,fresh_cores=1,guarded_host_writes=0,
                           manual_saves=0,transaction_saves=0,natural_progress_accepted=False,
                           purchase_reruns=0,cancel_reruns=0,warnings_errors=0)]

    def test_all_rows(self):
        out=m.audit_tables(self.rom,self.model,self.items)
        self.assertEqual((out['shop_count'],out['dialogue_count']),(23,35))
        self.assertEqual([r['index'] for r in out['shop_rows']],list(range(23)))
        self.assertFalse(out['natural_progress_accepted'])
        self.assertFalse(out['all_dialogue_native_display_accepted'])

    def test_current_candidate_required(self):
        with self.assertRaises(ValueError):m.audit(self.rom)

    def test_manifest_name_binding(self):
        with self.assertRaises(ValueError):m.audit_tables(self.rom,self.model,self.items.replace('モンスターボール','別名'))

    def test_bad_pointer(self):
        rom=bytearray(self.rom);struct.pack_into('<I',rom,m.TABLE-0x08000000+12,0x09FFFFFE)
        with self.assertRaises(ValueError):m.audit_tables(bytes(rom),self.model,self.items)

    def test_native(self):
        self.assertEqual(m.validate_native(self.raw(self.native))['pages'],5)

    @staticmethod
    def raw(rows):return b'\n'.join(json.dumps(r).encode() for r in rows)

    def test_generation_isolated(self):
        import pr16_research_purchase as p
        raw=(ROOT/'tools/mgba_pr16_research_save_impact.c').read_text()
        raw += (ROOT/p.C).read_text()
        raw=raw.replace('int main(int argc,char**argv){','int old_main(int argc,char**argv){',1)
        with mock.patch.object(p,'generate',return_value=raw.encode()):text=m.generate(b'').decode()
        self.assertEqual(text.count('int main(int argc,char**argv){'),1)
        start=text.index('static struct mCore*ct_setup(');end=text.index('/* 5ページ',start)
        setup=text[start:end]
        self.assertEqual(setup.count('QOL_FLAG_SET,QOL_FLAG_DH_CLEAR'),1)
        self.assertLess(setup.index('QOL_FLAG_SET'),setup.index('si_guard(c)'))
        self.assertIn('c->setVideoBuffer(c,si_video,240);c->reset(c);si_flash(c);',text)
        main=text.rsplit('int main(int argc,char**argv){',1)[1]
        for forbidden in ('si_normal_save','up_select','up_finish','uc_closed','QOL_KEY_B','call_preserving','qol_write'):
            self.assertNotIn(forbidden,main)
        self.assertIn('nonblank rendered screen',text)

# 各ABI field/商品/文言/閉じたnative schemaの独立変異。件数水増しsubtestではない。
def abi_test(field):
    def test(self):
        for index in range(23):
            rom=bytearray(self.rom);rom[m.TABLE-0x08000000+16*index+field]^=1
            with self.assertRaises(ValueError):m.audit_tables(bytes(rom),self.model,self.items)
    return test
for field in range(16):setattr(CatalogTests,f'test_abi_byte_{field:02}',abi_test(field))

def model_test(section,index,key,value):
    def test(self):
        model=copy.deepcopy(self.model)
        if section is None:model[key]=value
        else:model[section][index][key]=value
        with self.assertRaises((ValueError,KeyError)):m.audit_tables(self.rom,model,self.items)
    return test
for name,args in {
    'boolean_price':('shop',0,'point_cost',True),'zero_quantity':('shop',0,'quantity',0),
    'wrong_index':('shop',2,'index',1),'wrong_item':('shop',1,'item_id',4),
    'wrong_display':('shop',0,'row_text','モンスターボール 11RP'),
    'unknown_unlock':('shop',0,'unlock_key','UNKNOWN'),'stock':('shop',14,'stock_policy','UNLIMITED_AFTER_UNLOCK'),
    'limit':('shop',0,'daily_limit',1),'repeated':('shop',1,'shop_entry_key','SHOP_ENTRY_KEY_POKE_BALL_BUNDLE'),
    'terminator':('shop',0,'row_text_hex','ff00ff'),'dialogue_end':('dialogue',0,'encoded_hex','0000'),
    'dialogue_duplicate':('dialogue',1,'dialogue_key','DIALOGUE_KEY_COUNTER_INTRO'),
    'short_shop':(None,0,'shop',[]),'short_dialogue':(None,0,'dialogue',[]),
    'boolean_schema':(None,0,'schema_version',True),
}.items():setattr(CatalogTests,'test_model_'+name,model_test(*args))

def dialogue_test(index):
    def test(self):
        rom=bytearray(self.rom);rom[self.model['dialogue'][index]['runtime_address']-0x08000000]^=1
        with self.assertRaises(ValueError):m.audit_tables(bytes(rom),self.model,self.items)
    return test
for i in range(35):setattr(CatalogTests,f'test_dialogue_{i:02}',dialogue_test(i))

def native_test(index,key,value):
    def test(self):
        rows=copy.deepcopy(self.native);rows[index][key]=value
        with self.assertRaises(ValueError):m.validate_native(self.raw(rows))
    return test
for name,args in {
    'count':(1,'eligible_count',19),'fake_tasks':(1,'native_tasks',True),
    'missing_item':(2,'catalog_indices',[1,2,3,4]),'reordered':(3,'page',2),
    'duplicate_image':(3,'screen_sha256',f'{1:064x}'),'backward_frame':(3,'frame',999),
    'boolean_root':(0,'catalog',False),'boolean_counter':(-1,'manual_saves',False),
    'extra':(-1,'extra',1),'promoted':(-1,'natural_progress_accepted',True),
}.items():setattr(CatalogTests,'test_native_'+name,native_test(*args))

class ClosedInputTests(unittest.TestCase):
    def test_duplicate_json(self):
        with self.assertRaises(ValueError):m.load(b'{"a":1,"a":2}')
    def test_nan(self):
        with self.assertRaises(ValueError):m.load(b'{"a":NaN}')
    def test_empty_native(self):
        with self.assertRaises(ValueError):m.validate_native(b'')
    def test_extra_native_row(self):
        with self.assertRaises(ValueError):m.validate_native(CatalogTests.raw(CatalogTests.native+[{}]))

if __name__=='__main__':unittest.main()
