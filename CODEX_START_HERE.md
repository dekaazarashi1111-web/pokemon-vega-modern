# Codex開始手順

このワークスペースは既にGitリポジトリとプレイブックを統合済みです。新しく `git init` したり、受領ZIPの `AGENTS.md` で既存運用を上書きしたりしません。

## 毎セッションの開始

```bash
git status --short --branch
sed -n '1,240p' AGENTS.md
sed -n '1,220p' design/current_state.md
sed -n '1,260p' design/agent_context_map.md
python3 scripts/taskctl.py next
python3 scripts/taskctl.py plan
```

次に、選択した `tasks/T*.md` とcontext mapが指す資料だけを読みます。再開時は `prompts/RESUME.md` も使えます。

二地方関連では、V2をactive review資料とし、V1は来歴確認にだけ使います。

```text
design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/
design/import_review.md
design/kanto_feasibility.md
docs/KANTO_PORT_POLICY.md
```

## 私有入力

物理的な原本は `userfile/imports/` に読み取り専用で保存されています。ツールは次のGit管理外安定名を使います。

```text
inputs/
├─ private/
│  ├─ FireRed_JPN_Rev0_clean.gba
│  ├─ Vega_20180223.ips
│  └─ factory_test_20260524.ups
└─ reference/
   ├─ vega_cfru_integration_audit.zip
   ├─ vega_reference_provided.gba
   └─ factory_reference_provided.gba
```

hashと用途は `design/import_inventory.md` を正とします。ROM、patch、元ZIPは追跡・ステージ・コミットしません。

## 初期化 / Gate A

`make quickstart` は次の書込みを行います。

- Git管理外 `config/project.toml` の作成。
- 私有入力のhash検証と読み取り専用化。
- `vendor/upstream/` への上流clone/固定commit checkout（source archiveが無い場合はネットワーク使用）。
- `state/source-lock.json` とpreflight reportの生成。
- cleanからVega/Factory参照ROMを別々に生成し、厳密競合監査を実行。
- validator、private guard、READYタスク表示。

入力原本は変更せず、Factory UPSをVegaへ適用しません。生成物は同一hash/source pinなら再利用します。

```bash
make quickstart
make validate guard test
```

## 並列化

正本のIN_PROGRESSタスクは1件に保ち、その配下で独立作業を並列化します。大規模レーンをworktreeへ分ける場合は `WORKSTREAMS.md` の所有権と統合順に従います。

- Engine: `prompts/ENGINE_LANE.md`
- Map: `prompts/MAP_LANE.md`
- Content: `prompts/CONTENT_LANE.md`
- QA: `prompts/QA_LANE.md`

カントーはVega内の元FireRed領域を上書き復元せず、clean BPRJ Rev.0のraw資産を新規 `KANTO_*` 群へ複製して全参照を再接続します。まずT11の1map importer、次にT13のクチバ往復縦切りを通します。

T13のrelease解禁は殿堂入り後ではありません。シオウの3個目バッジとアーシア島D・Hビル初回攻略をT02で確定した実flagへ結び、早期・殿堂入り前のセーブで往復を必ず検証します。

## 人が確認する場所

```text
design/current_state.md
design/tasks_next.md
design/decisions.md
design/blockers.md
design/run_log.md
reports/generated/
```

安全に戻せる細部は自律的に進めます。不可欠な私有入力不足か、後戻りしにくい仕様分岐だけを確認します。
