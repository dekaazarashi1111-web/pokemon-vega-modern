"""Apply only the eight reviewed, byte-pinned representative-integration files."""
from pathlib import Path
import hashlib
import shutil

r = Path.cwd()
staging = r / '.github/repairs/p08-representative-evidence'
new_files = {
    'tools/modernization_p08_representative_evidence.py': '162c00482d14765075d612394a8af0d7b6301291',
    'scripts/integrate_modernization_p08_representative_evidence.py': 'e28f114f7708002ddbd1364fef2e58afb20f9891',
    'tests/test_modernization_p08_representative_evidence.py': '9398a41325d8cbc42f19863c972d6f781c78c7d4',
    'docs/P08_REPRESENTATIVE_E2E.md': '64fcccc9a3d5a16db743786aff6637073714ace8',
}
modified = {
    'scripts/check_modernization_p08_current_acceptance.py': ('a022cfdc682d93b77e511ff03d62199a3a22ca549294482da7145de2990d2c3e', 'd1a8f16206fe473ca974e57264f8e7c4745c1bcb6757f21f82b2718d9ac43d83'),
    'scripts/build_modernization_p08.py': ('16f391536d0225fd1782d6eed24d303c83f3a153fa4ae1a3a04bbcd3849a33ac', '658dd7538de48a3f88f34730922576f6d4fb0da91ac18937aa0a344bd717a9d7'),
    'tests/test_modernization_p08_current_acceptance.py': ('8444ab543c55033a53362c52a7762e7f14868c374dba439e0664248519fe2719', 'a1fb06c590b957ded39b9f4ddc3247ebc8701ccaec179b6e929505297c6b2af6'),
    'docs/P08_CURRENT_ACCEPTANCE.md': ('6fc3f52bb9905ca3b88b209d0a81e2d6910c6dbb51cd748e3a6ee97627a0c2ac', '9ddb7af3a49327e11d94a51a1ef4d4ad133cf1a678697348f9d64e79ecc67d82'),
}
for path, (before, after) in modified.items():
    assert hashlib.sha256((r / path).read_bytes()).hexdigest() == before, 'preimage changed: ' + path
for path, expected in new_files.items():
    raw = (staging / path).read_bytes()
    assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == expected, 'staged bytes changed: ' + path
    assert not (r / path).exists(), 'target already exists: ' + path
    shutil.copyfile(staging / path, r / path)
p = r / 'scripts/check_modernization_p08_current_acceptance.py'; s = p.read_text()
s = s.replace('from tools import modernization_p08_stage79_evidence as evidence  # noqa: E402', 'from tools import modernization_p08_stage79_evidence as evidence  # noqa: E402\nfrom tools import modernization_p08_representative_evidence as representative  # noqa: E402')
s = s.replace("'cumulative_evidence_binding'}", "'cumulative_evidence_binding'} | representative.KEYS")
s = s.replace("    sources: dict[str, dict[str, Any]] = {}", "    representative_e2e = representative.build_extension(root)\n    sources: dict[str, dict[str, Any]] = dict(representative_e2e['source_bindings'])")
s = s.replace('        document = load(path)', '        document = load(path)\n        representative.validate_document(document, representative_e2e)')
s = s.replace('実際の育成操作・画面遷移を通した検証が未完了', '通常習得・進化キャンセルの代表2ケースはPASS。満杯時の技入替・拒否、他の習得画面や育成経路の通し検証は未完了')
s = s.replace('習得後の保存・新規core再読込を通した検証が未完了', '通常習得後の保存・新規core Continueは代表2ケースでPASS。他の習得経路での保存・再読込は未完了')
s = s.replace('実際の戦闘ターン進行を通した検証が未完了', '6特性24条件とDragonize操作観測4条件はPASS。その他の技・特性経路、自然な特性取得・Battle Circus入場を含む全体検証は未完了')
s = s.replace("        'declared_runtime_limits': limits,", "        'declared_runtime_limits': limits,\n        'declared_runtime_limits_scope': 'UNCHANGED_ORIGINAL_STAGE79_FLAGS_NOT_REPRESENTATIVE_PROGRESS',\n        'representative_e2e': representative_e2e,")
p.write_text(s)
p = r / 'scripts/build_modernization_p08.py'; s = p.read_text().replace('OUTPUTS = {', 'from tools.modernization_p08_representative_evidence import attach_outputs as attach_representative  # noqa: E402\n\nOUTPUTS = {').replace('return attach_outputs(historical, ROOT)', 'return attach_representative(attach_outputs(historical, ROOT), ROOT)'); p.write_text(s)
p = r / 'tests/test_modernization_p08_current_acceptance.py'; s = p.read_text().replace('        self.validator.start()', "        self.representative_validator = patch.object(audit.representative, 'build_extension',\n            return_value=deepcopy(self.actual['representative_e2e']))\n        self.representative_validator.start()\n        self.addCleanup(self.representative_validator.stop)\n        self.validator.start()"); p.write_text(s)
p = r / 'docs/P08_CURRENT_ACCEPTANCE.md'
p.write_text(p.read_text() + '''
## 2026-09-09：後続の代表的な実操作試験

`representative_e2e` にP03 learning（2ケース）、P05 scheduler（24条件）、
P05 controller witness（4条件）の原本照合を追加した。
`declared_runtime_limits` は変更していないStage79原本のフラグであり、後続の
代表成功を取り消すものではない。現在の残件理由は、代表試験で確認済みの範囲と
未検証の経路を区別する。詳細と検証手順は `docs/P08_REPRESENTATIVE_E2E.md` を参照。
原本に含まれる新規プロセス30件と、今回の証跡再検証における新規実行0件を混同しない。
''')
for path, (before, after) in modified.items():
    assert hashlib.sha256((r / path).read_bytes()).hexdigest() == after, 'postimage mismatch: ' + path
print('P08 reviewed implementation byte verification: PASS')
