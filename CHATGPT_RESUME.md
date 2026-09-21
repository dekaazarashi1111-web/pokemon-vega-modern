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

候補Wiki生成のGitHub Issue [#18](https://github.com/dekaazarashi1111-web/pokemon-vega-modern/issues/18) は、`docs/wiki/p08-candidate-46487d98/**` を調整前・現状保存スナップショットとして生成済みである。同Wikiを上書きせず履歴として保持する。

clean-ROM独立2生成・配布用BPS固定・`release_ready=true` 判定・PR merge・active baseline切替へ入る前に、GitHub Issue [#19](https://github.com/dekaazarashi1111-web/pokemon-vega-modern/issues/19) `USER-20260921-LEARNSET-BASELINE-RESET` を実行する。

Issue #19は、技習得を次のフラットな基準へ復元するタスクである。

- 原作ポケモン: 所有者提供ZIP `Pokemon_Vega_Stage61_技習得品質改善版_v1.3.0_20260905(5).zip`（82,683,251 bytes / SHA-256 `80b678320c08203e7b39236e5c123f5c2f2f0c729e7f4e5101bed88c84158adb`）の公式Species/Form採用データを基準にする。
- ベガオリジナル: 原作Vegaの機械可読表または固定ROMからの直接抽出を優先し、`https://w.atwiki.jp/altair1/pages/19.html` のポケモン図鑑Vと各個別ページにあるレベル技・技マシン・教え技・タマゴ技を正本化または独立照合に使う。
- より再現性が高い別方法を使ってよいが、原作Vega由来をhash/versionで固定し、atwikiとの差分と理由を全件記録する。
- `CURRENT_PRESERVED`、`V3_ADDED`、V4/Modern後付け、旧ベガ由来499行等は、基準に存在しない限り現役習得から分離する。Move ID・技効果・過去の由来履歴は削除しない。
- `official_baseline`、`vega_original_baseline`、将来の `owner_approved_overlay` を分離し、本タスク完了時の追加overlayは原則空とする。
- 変更前Wiki・候補・受入証拠を保持し、新候補ROMと新候補Wikiを別identityで生成する。変更影響台帳に基づき影響範囲だけ再受入する。

### 所有者決定: サイドチェンジ

- 原本の技ID1063 / Side Change / サイドチェンジ相当は、本プロジェクトでは実装・採用しない。battle effect、AI、animation、TM/TR/Tutor、タマゴ・共有タマゴ等を新設しない。
- 原本159経路・103種は履歴から消さず、非採用理由付きで保持する。active learnsetでは原則として当該経路を除外する。
- level-up行を単純除外すると表構造・順序・consumerが不必要に複雑になる場合に限り、実装済みの目立つ伝説専用技を一時placeholderとして置いてよい。第一候補は「ときのほうこう」。現行manifestから実key/IDを解決し、仮行を `TEMP_OWNER_PLACEHOLDER_FOR_ALLYSWITCH` 相当で全件台帳化する。
- 仮技は最終バランスでも所有者承認済み配布でもない。後でWikiを見て、ベガ技または別技へ置換、もしくは削除する。level-up以外へ自動展開せず、後継Wikiで仮置きとして明示する。
- 詳細な実装・validator条件は `docs/PR16_LEARNSET_BASELINE_RESET_JA.md` を正とする。Side Change自体のnative受入は不要。

所有者提供ZIPは `userfile/imports/**` 等のGit管理外・読み取り専用入力として扱い、ZIP本体をcommitしない。入力が未提供またはhash不一致なら、似た名前の別資料や現行ROMを暗黙代用せずfail-closedにする。

Issue #19の完了後、所有者が新Wikiを確認してから、技追加、種族値・特性・夢特性調整、追加メガ、追加専用Zの仕様を別途決める。本タスク中に新しい最終配布を創作しない。上記Side Change用の明示placeholderだけは最終配布ではない仮置きとして例外的に許可する。

## 次回そのまま渡す指示

```text
@GitHub dekaazarashi1111-web/pokemon-vega-modern の
branch codex/modernization-followup-20260908 の最新HEADで
CHATGPT_RESUME.md を読み、指示された正本と最新Actionsを照合して、
次の未完作業から続けてください。受入済みは変更影響なしに再実行せず、
終了時は同じ引継ぎMD/JSON・両ログを更新してください。
merge・release・baseline切替は別途明示指示なしに行わないでください。
```


## Issue19の実装・検証正本

実装手順は `docs/PR16_LEARNSET_BASELINE_RESET_JA.md`、工程の受入範囲と未完項目は `content/modernization/pr16_learnset_baseline_checkpoint.json`。最新の次工程は固定再開MD/JSONを優先し、予約時点の説明と混同しない。


## Vega181種の原本採取・隔離監査checkpoint

`docs/PR16_VEGA_ORIGINAL_AUDIT_JA.md` と `content/modernization/pr16_vega_original_checkpoint.json` を参照。原本9923行/全182ページ/43試験は完了。次工程は3群5行の原本衝突と92種の非直接egg裁定。baseline採用/Issue19全体は未完。保存原本から再開し、公式隔離やWiki全件採取を繰り返さない。
