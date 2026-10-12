"""受付契約欠落の実原本から、再linkなしで再開する回帰検査。"""
from copy import deepcopy
from pathlib import Path
import inspect
import json
import sys
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_circus_rental_resume as t

class RentalResumeTests(unittest.TestCase):
    def setUp(self):
        self.original = json.loads((ROOT / t.PREVIOUS).read_bytes())
        self.saved = self.original['build']

    def test_actual_failure_is_preprocess_not_native_or_link(self):
        n = self.original['native']
        self.assertEqual(n['actual_new_processes'], 0)
        self.assertEqual(n['failures'], [dict(stage='setup-or-execution', error="'reception'")])
        self.assertEqual(self.saved['independent_arm_links'], 2)
        self.assertEqual(n['candidate']['sha256'], t.SHA)

    def test_real_contract_restores_reception_and_three_launches(self):
        fixed = t.restore_contract(self.saved)
        self.assertEqual(fixed['reception'], self.saved['old']['reception'])
        self.assertEqual(fixed['launch_sites'], self.saved['old']['launch_sites'])
        self.assertEqual(len(fixed['launch_sites']), 3)
        # 生成controllerが直後に読む両方のキーを実際に参照する。
        addresses = dict(CF_BRIDGE=fixed['reception']['bridge'], CF_SCRIPT=fixed['reception']['circus'],
                         CF_LAUNCH=fixed['launch_sites'][0]['new'])
        self.assertTrue(all(type(v) is int and 0x08000000 <= v < 0x0A000000 for v in addresses.values()))

    def test_saved_build_and_nested_parent_not_mutated(self):
        before = t.stable(self.saved)
        fixed = t.restore_contract(self.saved)
        for key in self.saved:
            self.assertEqual(fixed[key], self.saved[key], key)
        fixed['reception']['bridge'] = 0
        fixed['patches'][0]['name'] = 'changed only in test copy'
        self.assertEqual(t.stable(self.saved), before)

    def test_wrong_candidate_or_parent_rejected(self):
        for key in ('candidate', 'parent'):
            bad = deepcopy(self.saved)
            bad[key]['sha256'] = '0' * 64
            with self.subTest(key=key), self.assertRaises(ValueError):
                t.restore_contract(bad)

    def test_unproven_build_rejected(self):
        for key, value in [('independent_arm_links', 1), ('whole_rom_rollback_matches_parent', False)]:
            bad = deepcopy(self.saved); bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                t.restore_contract(bad)

    def test_partial_or_invalid_native_addresses_rejected(self):
        for kind in ('missing', 'zero', 'bool', 'launch', 'sites'):
            bad = deepcopy(self.saved)
            if kind == 'missing': del bad['old']['reception']['circus']
            elif kind == 'zero': bad['old']['reception']['bridge'] = 0
            elif kind == 'bool': bad['old']['reception']['bridge'] = True
            elif kind == 'launch': bad['old']['launch_sites'][0]['new'] = 0x02000000
            else: bad['old']['launch_sites'].pop()
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                t.restore_contract(bad)

    def test_prior_text_evidence_still_exact(self):
        for path, bound in self.original['text_evidence'].items():
            self.assertEqual(t.identity((ROOT / path).read_bytes()), bound, path)

    def test_restore_does_not_compile_or_run_old_native(self):
        source = inspect.getsource(t.reconstruct)
        self.assertIn("checked_patch(raw, saved['old'])", source)
        self.assertIn('checked_patch(parent, saved)', source)
        for call in ('compile_bridge(', 'compile_runtime(', 'inherited.reconstruct(', 'inherited.prepare('):
            self.assertNotIn(call, source)

    def test_native_keeps_original_prefix_and_target_gate(self):
        self.assertIn("need(result['genuine_30_wins_verified']", inspect.getsource(t.native))
        self.assertIn('events[:100]', inspect.getsource(t.inherited.native))
        self.assertIn('same_without_frame', inspect.getsource(t.inherited.native))

    def test_reconstruction_checks_identity_allocation_and_rollback(self):
        raw = b'01234567'; new = b'01AB4567'
        recipe = dict(parent=t.identity(raw), candidate=t.identity(new),
                      patches=[dict(name='test', offset=2, before=b'23'.hex(), after=b'AB'.hex())],
                      allocation=dict(allocations=[dict(name='test', start=2, end_exclusive=4,
                                                       content_sha256=t.identity(b'AB')['sha256'])]))
        self.assertEqual(t.checked_patch(raw, recipe), new)
        bad = deepcopy(recipe); bad['allocation']['allocations'][0]['content_sha256'] = '0' * 64
        with self.assertRaises(ValueError): t.checked_patch(raw, bad)
        with self.assertRaises(ValueError): t.checked_patch(b'badbytes', recipe)

    def test_prepare_preserves_previous_failure_and_refuses_duplicate(self):
        source = inspect.getsource(t.prepare)
        self.assertIn('previous_native_processes=0', source)
        self.assertIn("last.get('recording_run') == COMPILE_RUN", source)
        self.assertNotIn('inherited.prepare()', source)

    def test_configure_reentrant_and_isolated(self):
        for _ in range(2):
            d, b = t.configure()
            self.assertEqual(d.SELF, t.SELF)
            self.assertEqual(b.SELF, t.SELF)
            self.assertEqual(len(d.FILES), len(set(d.FILES)))
            self.assertTrue(set(t.FILES) <= set(d.FILES))

# production include順序をそのまま使う。game/ROM検証ではなくhost側C可視性の回帰。
C_PRELUDE = r"""
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
struct mCore { int unused; };
static unsigned b_frames;
#define QOL_PLAYER_PARTY_COUNT 1U
#define BP_F(name) 2U
#define BATTLE_CORE_MAIN_CALLBACK2 3U
#define SP_SCRIPT_PTR 4U
#define ADDR_NEW_BATTLE_STRUCT_POINTER 5U
#define BATTLE_CORE_BATTLE_OUTCOME 6U
static unsigned read8(struct mCore *c, uint32_t address) {(void)c; (void)address; return 0;}
static unsigned read16(struct mCore *c, uint32_t address) {return read8(c,address);}
static unsigned read32(struct mCore *c, uint32_t address) {return read8(c,address);}
static void b_frame(struct mCore *c,uint32_t keys) {(void)c; (void)keys; ++b_frames;}
static void g_shot(const char *name) {(void)name;}
static void bp_require(struct mCore *c,bool value,const char *text) {(void)c; (void)value; (void)text;}
"""
C_AFTER_POLICY = r"""
/* tools/mgba_pr16_circus_continuous.cではpolicyの後に定義する。 */
static unsigned sc_events,sc_wins;
int main(void) {
    struct mCore core={0}; sc_events=101U; sc_wins=21U;
    b_frame(&core,0U);
    return !(sc_events==101U && sc_wins==21U && rd_done==1U);
}
"""

class CounterDeclarationTests(unittest.TestCase):
    def compile(self, fixed):
        watch = (ROOT/'tools/mgba_pr16_circus_rental_drought.h').read_text()
        text = C_PRELUDE + (t.policy_with_counter(watch) if fixed else watch) + C_AFTER_POLICY
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'counter.c'; exe=Path(folder)/'counter'; source.write_text(text)
            result=subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror',str(source),'-o',str(exe)],capture_output=True,text=True)
            if result.returncode: return result, None
            return result, subprocess.run([str(exe)],capture_output=True,text=True)

    def test_original_include_order_reproduces_undeclared_counter(self):
        result, run=self.compile(False)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('sc_events',result.stderr)
        self.assertIn('undeclared',result.stderr)
        self.assertIsNone(run)

    def test_forward_definition_compiles_and_shares_counter(self):
        result, run=self.compile(True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(run.returncode,0,run.stderr)
        line=next(x for x in run.stderr.splitlines() if x.startswith('CIRCUS_RENTAL_DROUGHT '))
        value=json.loads(line.split(' ',1)[1])
        self.assertEqual(value['label'],'event-crossed-direct')
        self.assertEqual(value['events'],101)
        self.assertEqual(value['elapsed'],1)

    def test_duplicate_declaration_rejected(self):
        with self.assertRaises(ValueError): t.policy_with_counter(t.policy_with_counter('body'))

    def test_declaration_precedes_policy_and_preserves_all_old_text(self):
        old=(ROOT/'tools/mgba_pr16_circus_rental_drought.h').read_text()
        self.assertEqual(t.policy_with_counter(old),'static unsigned sc_events;\n'+old)

    def test_native_wraps_policy_before_original_runner(self):
        text=inspect.getsource(t.native)
        self.assertLess(text.index('n.policy ='),text.index('inherited.native()'))
        self.assertIn('policy_with_counter(previous_policy(wx, br))',text)

    def test_binding_refresh_requires_exact_base_and_keeps_strict_validate(self):
        text=inspect.getsource(t.refresh_changed_bindings)
        self.assertIn("['git', 'show', BASE + ':' + path]",text)
        self.assertIn('identity(previous) == bound',text)
        self.assertIn('path in FILES',text)
        self.assertLess(text.index('resume.render(state)'),text.index('resume.validate(ROOT)'))

if __name__ == '__main__': unittest.main()
