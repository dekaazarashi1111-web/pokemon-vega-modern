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

## 次回そのまま渡す指示

```text
@GitHub dekaazarashi1111-web/pokemon-vega-modern の
branch codex/modernization-followup-20260908 の最新HEADで
CHATGPT_RESUME.md を読み、指示された正本と最新Actionsを照合して、
次の未完作業から続けてください。受入済みは変更影響なしに再実行せず、
終了時は同じ引継ぎMD/JSON・両ログを更新してください。
merge・release・baseline切替は別途明示指示なしに行わないでください。
```
