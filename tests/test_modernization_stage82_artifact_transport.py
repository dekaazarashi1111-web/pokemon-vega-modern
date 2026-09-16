"""Original evidence transport: no bearer forwarding, no ZIP substitution."""
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import urllib.request
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import record_modernization_stage82_archive as subject

API='https://api.github.com/repos/'+subject.REPO+'/actions/artifacts/123/zip'
BLOB='https://productionresultssa0.blob.core.windows.net/actions-results/test.zip?sig=signed'

class Transport(unittest.TestCase):
    def request(self):
        response=mock.MagicMock()
        response.__enter__.return_value.read.return_value=b'original zip bytes'
        with mock.patch.dict(os.environ,{'GH_TOKEN':'regression-test-token'}), mock.patch.object(subject.urllib.request,'urlopen',return_value=response) as opened:
            self.assertEqual(subject.get(API,True),b'original zip bytes')
        return opened.call_args.args[0]

    def test_initial_api_is_authenticated(self):
        self.assertEqual(self.request().get_header('Authorization'),'Bearer regression-test-token')

    def test_token_is_not_a_redirectable_header(self):
        self.assertNotIn('Authorization',self.request().headers)

    def test_blob_redirect_does_not_receive_github_token(self):
        req=self.request()
        redirected=urllib.request.HTTPRedirectHandler().redirect_request(req,None,302,'Found',{},BLOB)
        self.assertNotIn('Authorization',dict(redirected.header_items()))
        self.assertEqual(redirected.full_url,BLOB)

    def test_second_redirect_does_not_regain_token(self):
        handler=urllib.request.HTTPRedirectHandler()
        req=handler.redirect_request(self.request(),None,302,'Found',{},BLOB)
        req=handler.redirect_request(req,None,307,'Moved',{},BLOB+'&second=1')
        self.assertIsNone(req.get_header('Authorization'))

    def test_foreign_repository_is_rejected_before_network(self):
        with mock.patch.object(subject.urllib.request,'urlopen') as opened:
            with self.assertRaisesRegex(ValueError,'non-repository Actions URL'):
                subject.get('https://api.github.com/repos/other/repo/actions/artifacts/123/zip',True)
            opened.assert_not_called()

    def test_direct_blob_request_is_rejected_before_network(self):
        with mock.patch.object(subject.urllib.request,'urlopen') as opened:
            with self.assertRaises(ValueError):subject.get(BLOB,True)
            opened.assert_not_called()

class OriginalMembers(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.directory=Path(self.temp.name)
        (self.directory/'result.json').write_bytes(b'{"status":"PASS"}')

    def zip_bytes(self,name='result.json',data=b'{"status":"PASS"}'):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as z:z.writestr(name,data)
        return stream.getvalue()

    def test_exact_original_passes(self):
        subject.verify_zip_members(self.zip_bytes(),self.directory)

    def test_different_result_rejected(self):
        with self.assertRaisesRegex(ValueError,'ZIP/extraction mismatch'):
            subject.verify_zip_members(self.zip_bytes(data=b'{"status":"FAIL"}'),self.directory)

    def test_extra_extracted_file_rejected(self):
        (self.directory/'old-pass.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'extra or missing'):
            subject.verify_zip_members(self.zip_bytes(),self.directory)

    def test_missing_member_rejected(self):
        (self.directory/'result.json').unlink()
        with self.assertRaises(FileNotFoundError):subject.verify_zip_members(self.zip_bytes(),self.directory)

    def test_path_traversal_rejected(self):
        with self.assertRaisesRegex(ValueError,'unsafe ZIP member'):
            subject.verify_zip_members(self.zip_bytes('../result.json'),self.directory)

    def test_absolute_member_rejected(self):
        with self.assertRaisesRegex(ValueError,'unsafe ZIP member'):
            subject.verify_zip_members(self.zip_bytes('/result.json'),self.directory)

    def test_symlink_member_rejected(self):
        (self.directory/'result.json').rename(self.directory/'target')
        (self.directory/'result.json').symlink_to(self.directory/'target')
        with self.assertRaisesRegex(ValueError,'symlink'):
            subject.verify_zip_members(self.zip_bytes(),self.directory)

if __name__=='__main__':unittest.main()
