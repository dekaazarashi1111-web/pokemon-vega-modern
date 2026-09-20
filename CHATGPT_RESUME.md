# ChatGPTの固定再開入口

このファイル名を次のセッションでもそのまま指定する。ここには変化する進捗やHEADを複製しない。

対象はPR #16 / branch `codex/modernization-followup-20260908`。
GitHubでbranchの**現在HEAD**とPR状態を取得し、そのrefで読む。default branchや過去の会話に残るSHAへ勝手に切り替えない。

1. [AGENTS.md](AGENTS.md) — 安全・検証・Gitの規約。
2. [現在の再開メモ](docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md) — 停止点・次の1手・最小読書順。
3. [対応する状態JSON](content/modernization/pr16_native_supply_resume_20260913.json) — 証拠・候補・残件・更新契約。

上のMD/JSONのファイル名にある日付は固定識別子であり、日付ごとの複製は作らない。
正式受入はcheckpoint、完了条件はP08台帳が引き続き正本。詳細を読むタイミングは再開メモに従う。
PR本文・古いresume・一般タスクキューを、このPRの最新停止点の代わりにしない。

## 所有者予約済みの次タスク

現在の再開メモと状態JSONが指すP08作業を先に区切りよく閉じた後、clean-ROM独立2生成・配布用BPS固定・release判定へ入る前に、GitHub Issue [#18](https://github.com/dekaazarashi1111-web/pokemon-vega-modern/issues/18) `USER-20260921-P08-CANDIDATE-WIKI` を実行する。

Issue #18は、既存 `docs/wiki/stage61/**` を固定履歴として変更せず、実行時点の最新P08候補から、ベガ性能、全Species/Form、種族値、タイプ、通常特性・夢特性、全習得経路、技性能、全メガ、専用Zワザ、Stage61との差分を、決定的generator・Markdown・JSON/JSONL・検査レポートとして詳細生成するタスクである。

この予約は現在のP08受入を完了扱いにせず、Wiki生成中の性能変更・追加メガ・追加専用Z・merge・release・active baseline切替も許可しない。Wikiを調整前スナップショットとして生成・検証・記録した後、所有者が内容を見て別途調整仕様を決める。

## 次回そのまま渡す指示

```text
@GitHub dekaazarashi1111-web/pokemon-vega-modern の
branch codex/modernization-followup-20260908 の最新HEADで
CHATGPT_RESUME.md を読み、指示された正本と最新Actionsを照合して、
次の未完作業から続けてください。受入済みは変更影響なしに再実行せず、
終了時は同じ引継ぎMD/JSON・両ログを更新してください。
merge・release・baseline切替は別途明示指示なしに行わないでください。
```
