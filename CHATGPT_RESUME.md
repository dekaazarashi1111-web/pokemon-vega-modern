# ChatGPTの固定再開入口

このファイル名を次のセッションでもそのまま指定する。対象はPR #16 / branch `codex/modernization-followup-20260908`。GitHubでbranchの現在HEADとPR状態を取得し、そのrefで読む。default branchや過去SHAへ切り替えない。

## 現行の再開順 — OWNER-20261010-WIKI-FIRST

1. [AGENTS.md](AGENTS.md) — 安全・検証・Gitの規約。
2. [現在の実行方針と完了条件](docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md) — Wiki先行、全クリ除外、所有者検討中の基盤継続、承認管理。
3. [現在の状態JSON](content/modernization/pr16_wiki_first_execution_plan.json) — `owner_execution_plan`、`next_action`、保留した技術停止点、記録状況。このJSONが現在の作業選択の唯一の正本。

従来どおり「最新HEADのCHATGPT_RESUME.mdから指示された正本を読み、未完作業を実装・検証・記録して同branchへ反映」という指示だけで続ける。毎回方針の再確認を求めず、この固定MD/JSONを更新する。別日付のresumeや二重の進捗JSONを作らない。

**最初に調整基準Wiki R0を整える。** 解析08397492の1件や90未知の全解消、全保存修復、無関係なCI障害の解消を、Wiki第一版の前提にしない。直前の解析成果は保存済みとして保全し、未完を完了へ読み替えない。

**R0提示後は、所有者がWikiを見て調整案を考える間にも、作業セッションで保存・容量修復、CI整合性、メガ/キョダイマックス/専用Zの技術確認を進める。** 所有者の案待ちだけで停止しない。未承認の対象種、性能、技、特性、解禁条件、追加フォーム仕様は勝手に決めない。承認済みの小単位は依存条件を満たせば全案の完成を待たず実装できる。

**ストーリー全クリ走破は完成条件から除外。** ゲーム内ストーリーを削除する意味ではない。Save101以前の原本を保持し、全story PASSと主張しない。保存破損の修復、必要な短い戦闘・習得・進化・Save/fresh Continue等の確認は残す。長期育成soakは別判断の延期項目。シオウや全国図鑑のためだけの長距離プレイへ自動的に戻らない。

## 旧資料を現在の次作業と取り違えない

- [保留した技術作業の旧メモ](docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md) と [旧技術状態JSON](content/modernization/pr16_native_supply_resume_20260913.json) は、証拠・受入・解析停止点の参照先として保持する。これらの旧nextは新しい作業選択を上書きしない。
- [変更前の入口全文](CHATGPT_RESUME_BEFORE_WIKI_FIRST.md) は同一blobの固定履歴。旧Story加速計画・予約時の次作業を再開しない。原本の扱い、Side Change不採用、Vega ROM優先の所有者決定は引き続き維持する。
- 正式受入は各checkpoint、配布ゲートは [P08台帳](content/modernization/p08_remaining_work.json) を正とする。Wiki第一版だけでIssue18/19やrelease_readyを完了にしない。
- 旧MDの生成器 `scripts/pr16_resume.py` は旧技術JSON用。新方針を旧作業順へ戻す目的でrender/install-routingしない。旧証拠のhash不一致を安易に再束縛しない。

新しい閲覧版は固定して所有者へ提示するが、開発branchは前進してよい。意味変更が生じたら影響するページと調整案を示す別revision/diffを作り、閲覧中のR0を黙って更新しない。既存Stage61/旧P08/Issue19のWikiを上書きしない。

## 毎回の終了と許可境界

新状態JSONへ、今回の実完了・検証・実在するWiki入口と版・所有者の承認・技術レーンの残件・最新Actions・次の具体的作業を残す。`design/run_log.md` / `design/version_log.md` は追記だけ。初回の事務追記未実施分は新JSONの `recording` に明示してあるので、同決定IDの重複を確認して未実施分だけ追記してからWikiへ進む。

受入済みを変更影響なしに再実行しない。長い作業は小さな区切りで記録し、ユーザーが許可した同branchへ通常commit/non-force pushする。push前後のlive HEADと対象blobを確認し、他者の変更を破棄しない。merge・draft解除・公開release・active baseline切替は別の明示許可なしに行わない。

## 次回そのまま渡す指示

```text
@GitHub dekaazarashi1111-web/pokemon-vega-modern の
branch codex/modernization-followup-20260908 の最新HEADで
CHATGPT_RESUME.md を読み、指示された正本と最新Actionsを照合して、
次の未完作業を実装・検証・記録まで進め、同じbranchへ非force反映してください。
受入済みは変更影響なしに再実行せず、固定の引継ぎMD/JSONと両ログを更新してください。
merge・release・baseline切替は別途明示指示なしに行わないでください。
```
