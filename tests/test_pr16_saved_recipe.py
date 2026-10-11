"""再構成核の拒否契約。実ROM/native/旧builderは一度も使わない。"""
import copy
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_saved_recipe as s


class SavedRecipeTests(unittest.TestCase):
    def setUp(self):
        self.raw=b'0123456789abcdef'
        self.out=b'01AB456789abcdef'
        self.recipe={'parent':s.identity(self.raw),'candidate':s.identity(self.out),
                     'patches':[dict(offset=2,before=b'23'.hex(),after=b'AB'.hex())]}

    def test_exact_forward_and_whole_reverse(self):
        out, report=s.apply_recipe(self.raw,self.recipe)
        self.assertEqual(out,self.out)
        self.assertTrue(report['whole_rom_rollback_matches_parent'])

    def test_parent_digest_rejected(self):
        with self.assertRaises(s.RecipeError):s.apply_recipe(b'X'+self.raw[1:],self.recipe)

    def test_candidate_digest_rejected(self):
        r=copy.deepcopy(self.recipe);r['candidate']=s.identity(self.raw)
        with self.assertRaises(s.RecipeError):s.apply_recipe(self.raw,r)

    def test_preimage_rejected(self):
        r=copy.deepcopy(self.recipe);r['patches'][0]['before']='ffff'
        with self.assertRaises(s.RecipeError):s.apply_recipe(self.raw,r)

    def test_bounds_overlap_boolean_and_resize_rejected(self):
        for rows in ([dict(offset=-1,before='3233',after='4142')],
                     [dict(offset=15,before='3233',after='4142')],
                     [dict(offset=True,before='3233',after='4142')],
                     self.recipe['patches']*2,
                     [dict(offset=2,before='3233',after='41')]):
            with self.subTest(rows=rows),self.assertRaises(s.RecipeError):s.patch(self.raw,rows)

    def test_empty_uppercase_whitespace_and_noop_rejected(self):
        for before,after in [('', ''),('3233','ABCD'),('32 33','4142'),('3233','3233')]:
            with self.subTest(before=before,after=after),self.assertRaises(s.RecipeError):
                s.patch(self.raw,[dict(offset=2,before=before,after=after)])

    def test_typed_identity_and_duplicate_json(self):
        for b in [dict(size=True,sha256='0'*64),dict(size=0,sha256='0'*64),dict(size=1,sha256='z'*64)]:
            with self.assertRaises(s.RecipeError):s.binding(b)
        for raw in [b'{"a":1,"a":2}',b'{"a":NaN}']:
            with self.assertRaises(s.RecipeError):s.strict(raw)

    def test_chain_terminal_and_order(self):
        last=b'01AB456XYZabcdef';r2=dict(parent=s.identity(self.out),candidate=s.identity(last),
            patches=[dict(offset=7,before=b'789'.hex(),after=b'XYZ'.hex())])
        out,report=s.chain(self.raw,[self.recipe,r2],s.identity(last))
        self.assertEqual(out,last);self.assertTrue(report['whole_chain_rollback_matches_parent'])
        self.assertEqual(report['arm_compiles'],0)
        for recipes,target in [([r2,self.recipe],s.identity(last)),([self.recipe],s.identity(last))]:
            with self.assertRaises(s.RecipeError):s.chain(self.raw,recipes,target)

    def test_cycle_rejected(self):
        reverse=dict(parent=self.recipe['candidate'],candidate=self.recipe['parent'],
                     patches=[dict(offset=2,before='4142',after='3233')])
        with self.assertRaises(s.RecipeError):s.chain(self.raw,[self.recipe,reverse],s.identity(self.raw))

    def test_allocation_hash_sequence_overlap(self):
        row=dict(start=2,end_exclusive=4,size=2,sequence=0,name='owner',content_sha256=s.identity(b'AB')['sha256'])
        plan=dict(summaries=dict(overlap_count=0),allocations=[row])
        self.assertEqual(s.allocations(self.out,plan),1)
        for key,value in [('end_exclusive',99),('size',True),('sequence',1),('content_sha256','0'*64)]:
            p=copy.deepcopy(plan);p['allocations'][0][key]=value
            with self.assertRaises(s.RecipeError):s.allocations(self.out,p)
        duplicate=copy.deepcopy(row);duplicate.update(name='other',sequence=1)
        with self.assertRaises(s.RecipeError):s.allocations(self.out,dict(summaries=dict(overlap_count=0),allocations=[row,duplicate]))

    def test_path_traversal_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            for path in ['../x','/x','a/../x','a//b','a\\b']:
                with self.assertRaises(s.RecipeError):s.safe(d,path)
            (Path(d)/'link').symlink_to('/tmp')
            with self.assertRaises(s.RecipeError):s.safe(d,'link/x')
            self.assertEqual(s.safe(d,'nested/file'),Path(d)/'nested/file')

    def test_disassembly_exact_halfwords_and_literals(self):
        text=' 9ff0000:\tb510      \tpush {r4, lr}\n 9ff0002:\t1234      \tmov\n 9ff0004:\t08000001 \t.word\n'
        raw=bytes.fromhex('10b5341201000008')
        self.assertEqual(s.disassembly_bytes(text,0x9ff0000,s.identity(raw)),raw)
        for bad in [text+text,text.replace('9ff0002','9ff0010'),text.replace('1234','1235'),text.splitlines()[0]]:
            with self.assertRaises(s.RecipeError):s.disassembly_bytes(bad,0x9ff0000,s.identity(raw))

    def test_core_does_not_import_or_spawn_builders(self):
        import ast
        tree=ast.parse(Path(s.__file__).read_text())
        imports={alias.name for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom)) for alias in n.names}
        self.assertFalse(imports&{'subprocess','os','ctypes','importlib','pr16_circus_rental_resume'})
        calls={n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertFalse(calls&{'eval','exec','__import__'})

if __name__=='__main__':unittest.main()
