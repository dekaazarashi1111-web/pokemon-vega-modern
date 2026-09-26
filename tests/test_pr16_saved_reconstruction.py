"""保存原本の正規化だけを試験。旧host/native/ARM検証は起動しない。"""
import ast
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import urllib.request
import warnings
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_saved_reconstruction as r
s = r.s


class ReconstructionTests(unittest.TestCase):
    def archive(self, root, names=('member.txt',), content=b'original', member=b'original'):
        buffer=io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with zipfile.ZipFile(buffer,'w') as z:
                for name in names:z.writestr(name,content)
        raw=buffer.getvalue();folder=Path(root)/'originals';folder.mkdir()
        (folder/'1.zip').write_bytes(raw)
        seed=dict(archives={'fixed':dict(artifact_id=1,run_id=2,head_sha='1'*40,
            identity=s.identity(raw),members={'member.txt':s.identity(member)})})
        return r.Originals(seed,Path(root))

    def test_sparse_difference_with_chunk_crossing_and_unchanged_ranges(self):
        a=b'0'*8193;b=a[:4090]+b'1'*15+a[4105:]
        rows=r.sparse_difference(a,b)
        self.assertEqual(s.patch(a,rows),b)
        self.assertEqual(s.patch(b,[dict(offset=x['offset'],before=x['after'],after=x['before']) for x in rows]),a)
        self.assertEqual(len(rows),2)
        with self.assertRaises(s.RecipeError):r.sparse_difference(a,b[:-1])

    def test_original_member_bound_and_no_unlisted_member(self):
        with tempfile.TemporaryDirectory() as root:
            o=self.archive(root)
            self.assertEqual(o.read('fixed','member.txt'),b'original')
            self.assertEqual(o.used['fixed/member.txt'],s.identity(b'original'))
            with self.assertRaises(s.RecipeError):o.read('fixed','unlisted')

    def test_changed_member_and_archive_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            o=self.archive(root,content=b'bad')
            with self.assertRaises(s.RecipeError):o.read('fixed','member.txt')
        with tempfile.TemporaryDirectory() as root:
            o=self.archive(root);(Path(root)/'originals/1.zip').write_bytes(b'bad')
            with self.assertRaises(s.RecipeError):o.read('fixed','member.txt')

    def test_duplicate_absolute_and_traversal_zip_rejected(self):
        for names in [('member.txt','member.txt'),('../member.txt',),('/member.txt',),('a\\member.txt',)]:
            with self.subTest(names=names),tempfile.TemporaryDirectory() as root:
                o=self.archive(root,names=names)
                with self.assertRaises(s.RecipeError):o.read('fixed','member.txt')

    def test_process_audit_rejects_all_launch_routes(self):
        for event in ['subprocess.Popen','os.system','os.posix_spawn','os.fork','os.forkpty','os.exec','os.execve']:
            with self.subTest(event=event),self.assertRaises(s.RecipeError):r.deny_process(event,())
        r.deny_process('open',())

    def test_cross_host_redirect_drops_authorization(self):
        req=urllib.request.Request('https://api.github.com/original',headers={'Authorization':'Bearer dummy'})
        out=r.SafeRedirect().redirect_request(req,None,302,'',{},'https://storage.example/target')
        self.assertFalse(out.has_header('Authorization'))
        with self.assertRaises(s.RecipeError):r.SafeRedirect().redirect_request(req,None,302,'',{},'http://storage.example/target')

    def test_literal_reader_never_executes_module(self):
        values=r.constants('tools/modernization_p03_archive_ui_repair.py')
        self.assertEqual(len(values['SITES']),6)
        self.assertNotIn('verify_assembly',values)

    def test_runtime_reconstruction_has_no_legacy_or_network_path(self):
        tree=ast.parse(Path(r.__file__).read_text())
        fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='reconstruct')
        imports=[x for x in ast.walk(fn) if isinstance(x,(ast.Import,ast.ImportFrom))]
        self.assertEqual(imports,[])
        names={x.func.id for x in ast.walk(fn) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name)}
        self.assertFalse(names&{'normalize','Originals','constants','make_entry'})
        attrs={x.func.attr for x in ast.walk(tree) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute)}
        self.assertFalse(attrs&{'run','build','compile_runtime','compile_adapter','verify_assembly','system','Popen'})

    def test_seed_is_fixed_to_recorded_sources(self):
        seed=s.strict((r.ROOT/r.SEED).read_bytes())
        self.assertEqual(len(seed['archives']),9)
        for name,expected in seed['source_bindings'].items():self.assertEqual(s.identity((r.ROOT/name).read_bytes()),expected)
        for archive in seed['archives'].values():
            s.binding(archive['identity'])
            for member in archive['members'].values():s.binding(member)
        self.assertEqual(seed['charmap']['commit'],'e24a16fe39e27ae162faf5b78596d1f3df18489d')

if __name__=='__main__':unittest.main()
