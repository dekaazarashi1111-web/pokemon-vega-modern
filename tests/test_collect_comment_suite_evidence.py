import gzip
import json
import unittest
from scripts import collect_comment_suite_evidence as evidence


class CommentEvidenceTests(unittest.TestCase):
    def comment(self):
        return {'user': {'login': 'github-actions[bot]', 'id': 41898282}, 'body':
                'ChatGPT comment command: **SUCCESS**\n\n- command: `private suite stage62-check`\n'
                f'- ref: `{evidence.BRANCH}`\n- SHA: `{"a"*40}`\n'
                f'- run: https://github.com/{evidence.REPO}/actions/runs/123'}

    def test_exact_author_branch_head_command(self):
        self.assertEqual(evidence.result_comment(self.comment(), 'a'*40), ('stage62-check', 123))

    def test_wrong_author_and_head_are_rejected(self):
        self.assertIsNone(evidence.result_comment(self.comment(), 'b'*40))
        comment = self.comment()
        comment['user']['id'] = 1
        self.assertIsNone(evidence.result_comment(comment, 'a'*40))

    def test_other_repository_and_extra_text_are_rejected(self):
        for suffix in ('\nprivate text', ''):
            comment = self.comment()
            comment['body'] = comment['body'].replace(evidence.REPO, 'another/repo') + suffix
            self.assertIsNone(evidence.result_comment(comment, 'a'*40))

    def test_cli_observed_count_and_version(self):
        result = evidence.summarize_log('battle-cli-offline', b'Ran 37 tests in 0.123s\nOK\nvega-codex-battle 2.5.1\n')
        self.assertEqual(result['tests'], 37)
        self.assertEqual(result['version'], '2.5.1')
        self.assertTrue(result['counts_match_contract'])

    def test_cli_wrong_count_is_not_hidden(self):
        result = evidence.summarize_log('battle-cli-offline', b'Ran 36 tests in 0.123s\nOK\nvega-codex-battle 2.5.1\n')
        self.assertEqual(result['tests'], 36)
        self.assertFalse(result['counts_match_contract'])

    def test_cli_skips_and_missing_summary_are_rejected(self):
        for raw in (b'Ran 37 tests in 0.123s\nOK (skipped=1)\nvega-codex-battle 2.5.1\n', b'OK\n'):
            with self.assertRaises(ValueError):
                evidence.summarize_log('battle-cli-offline', raw)

    def test_mgba_counts_and_gzip(self):
        value = {'stage':62,'status':'PASS','rom_sha256':evidence.ROM_SHA,'fixture_count':6,'process_runs_per_fixture':2,
                 'private_field':'synthetic private message'}
        raw = json.dumps(value).encode()
        result = evidence.summarize_log('stage62-mgba', gzip.compress(raw))
        self.assertTrue(result['counts_match_contract'])
        self.assertNotIn('private', json.dumps(result))

    def test_wrong_rom_and_ambiguous_result_are_rejected(self):
        raw = json.dumps({'stage':62,'status':'PASS','command':'check','rom_sha256':evidence.ROM_SHA}).encode()
        for value in (raw.replace(evidence.ROM_SHA.encode(), b'0'*64), raw+b'\n'+raw):
            with self.assertRaises(ValueError):
                evidence.summarize_log('stage62-check', value)
