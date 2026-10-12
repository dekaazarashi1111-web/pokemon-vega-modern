"""専用Wiki入口の差分試験。native/ROM生成には触れない。"""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import build_pr16_candidate_wiki as cli
from pr16_candidate_wiki_inputs import Inputs


class WikiCliTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.fixture={'README.md':b'[data](data/a.json)\n','data/a.json':b'{}\n'}
        self.candidate={'sha256':'a'*64,'crc32':'12345678','size':32}
        self.output=self.root/'docs/wiki/p08-candidate-aaaaaaaa'
        self.index={'counts':{'species':1},'record_counts':{'species':1}}

    def execute(self,command):
        with patch.object(cli,'selected_candidate',return_value=self.candidate), patch.object(cli,'generate',return_value=(self.fixture,self.index)):
            return cli.execute(command,Inputs(self.root))

    def test_build_check_equal_and_check_no_write(self):
        build=self.execute('build')
        before={p:(p.read_bytes(),p.stat().st_mtime_ns) for p in self.output.rglob('*') if p.is_file()}
        with patch.object(Path,'write_bytes',side_effect=AssertionError('write')),patch.object(Path,'write_text',side_effect=AssertionError('write')),patch.object(Path,'mkdir',side_effect=AssertionError('mkdir')):
            check=self.execute('check')
        self.assertEqual(build['tree_sha256'],check['tree_sha256'])
        self.assertEqual(before,{p:(p.read_bytes(),p.stat().st_mtime_ns) for p in self.output.rglob('*') if p.is_file()})

    def test_idempotent_build_does_not_rewrite_files(self):
        self.execute('build')
        with patch.object(Path,'write_bytes',side_effect=AssertionError('rewrite')):
            self.execute('build')

    def test_missing_root_check_creates_nothing(self):
        with self.assertRaises(ValueError):self.execute('check')
        self.assertEqual(list(self.root.iterdir()),[])

    def test_missing_stale_changed_rejected(self):
        for mode in ('missing','stale','changed'):
            with self.subTest(mode=mode):
                self.execute('build')
                path=self.output/'README.md'
                if mode=='missing':path.unlink()
                elif mode=='changed':path.write_bytes(b'wrong')
                else:(self.output/'stale.md').write_bytes(b'stale')
                before=cli.read_tree(self.output)
                with self.assertRaises(ValueError):self.execute('check')
                self.assertEqual(before,cli.read_tree(self.output))
                if mode=='stale':(self.output/'stale.md').unlink()

    def test_build_rejects_stale_without_deleting(self):
        self.execute('build');(self.output/'old.md').write_text('old')
        before=cli.read_tree(self.output)
        with self.assertRaises(ValueError):self.execute('build')
        self.assertEqual(before,cli.read_tree(self.output))

    def test_output_and_child_symlinks_rejected(self):
        self.execute('build')
        (self.output/'external.md').symlink_to(self.root/'outside')
        for command in ('build','check'):
            with self.assertRaises(ValueError):self.execute(command)
        (self.output/'external.md').unlink()
        self.output.rename(self.output.with_name('real'))
        self.output.symlink_to(self.output.with_name('real'),target_is_directory=True)
        with self.assertRaises(ValueError):self.execute('check')

    def test_special_file_rejected(self):
        self.execute('build');os.mkfifo(self.output/'fifo')
        with self.assertRaises(ValueError):self.execute('check')
        (self.output/'fifo').unlink()

    def test_read_events_are_allowed(self):
        cli.reject_writes('open',('x','r',os.O_RDONLY))
        cli.reject_writes('os.listdir',('.',))

    def test_write_modes_flags_mutations_and_processes_rejected(self):
        for mode in ('w','wb','a','x','r+'):
            with self.subTest(mode=mode),self.assertRaises(ValueError):cli.reject_writes('open',('x',mode,os.O_RDONLY))
        for flags in (os.O_WRONLY,os.O_RDWR,os.O_CREAT,os.O_TRUNC,os.O_APPEND):
            with self.assertRaises(ValueError):cli.reject_writes('open',('x',None,flags))
        for event in ('os.mkdir','os.remove','os.rename','os.utime','subprocess.Popen','os.system','os.posix_spawn'):
            with self.assertRaises(ValueError):cli.reject_writes(event,())

    def test_audit_hook_blocks_real_write_in_isolated_process(self):
        target=self.root/'must-not-exist'
        source='import sys;sys.path.insert(0,sys.argv[1]);from build_pr16_candidate_wiki import reject_writes;sys.addaudithook(reject_writes);open(sys.argv[2],"w")'
        run=subprocess.run([sys.executable,'-B','-c',source,str(ROOT/'scripts'),str(target)],capture_output=True,text=True)
        self.assertNotEqual(run.returncode,0);self.assertIn('check書込',run.stderr);self.assertFalse(target.exists())

    def test_unknown_command_fail_closed(self):
        with self.assertRaises(ValueError):self.execute('delete')

if __name__=='__main__':unittest.main()
