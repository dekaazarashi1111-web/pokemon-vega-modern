# ChatGPTの固定再開入口

対象は PR #16 / `codex/modernization-followup-20260908`。毎回GitHubの現在HEADとPR状態を確認してそのrefを読む。過去SHAやdefault branchへ切り替えない。

## 現在の最優先 — OWNER-20261011-WIKI-READABILITY-FIRST

所有者指示: 2026-10-11 10:23:24 JST（01:23:24Z）。**まず閲覧用Wikiの小修正を実装・検証・記録・提示まで完成させる。その前に保存容量の解析を続けない。** 今回の依頼はこの作業順への変更であり、方針変更だけをWiki修正完了と数えない。

1. [AGENTS.md](AGENTS.md) — 安全・検証・Git規約。
2. [Wiki閲覧改善の優先指示と完成条件](docs/PR16_WIKI_READABILITY_PRIORITY_JA.md) — 今回の範囲・禁止事項・終了条件。競合する旧作業順より優先。
3. [固定状態JSON](content/modernization/pr16_wiki_first_execution_plan.json) — `next_action` / `owner_execution_plan.wiki_readability` を現在の作業選択の正本とする。
4. [継続する長期方針](docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md) — 全クリ除外・所有者検討中の技術作業・承認管理。R0完成後に即解析へ戻る旧条件は今回の閲覧改善が完了するまで保留。

従来の「最新HEADのCHATGPT_RESUME.mdから指示された正本を読み、次の未完作業を実装・検証・記録して同branchへ反映」の指示だけで続ける。新しい方針確認を繰り返さず、同じ状態JSONを更新する。

## いま行うこと

現在の `next_action.id` は `WIKI_READABILITY_FIX`。既存R0の比較表・個別ページ・生成処理を読み、誤解を招く役割別要約、主要MD一覧の技術情報過多、閲覧とローカル保存の入口を限定修正する。計画の再説明だけで止めず、修正版を作って限定検証し、実在する入口と保存方法を提示する。

**既存の `wiki.review_ready=true` は固定R0の生成・公開済み記録であり、今回の閲覧改善完了ではない。** R0は不変の入力・履歴として保持する。改善版R0.1（閲覧版）の実在path、入力identity、変更範囲、検証、公開commit、パッケージと提示結果は `wiki_readability` へ別記する。未生成pathや予定ZIPを完了として記録しない。

修正は「誤解を防ぎ読みやすくする」範囲。ゲーム本体、種族値、特性割当、技性能、全習得経路、機構対応、原本ROM/Save101は変更しない。バランス案・新メガ・新キョダイマックス・新専用Zの対象や性能を勝手に決めない。全技効果解析・全体Wiki刷新・ストーリー走破・無影響native再実行へ広げない。

## 保留中の技術作業と復帰先

最新の技術停止点は `owner_execution_plan.technical_lanes.save_capacity` と `wiki_readability.paused_technical_next_action`。Berryの現owner/reader確認、正式788分類/86未知、選定残7、安全容量0の時点を保持する。これは転用・保存統合完了ではない。古い784/90や08397492へ戻って再測定しない。WIPコード・成功/失敗原本を破棄せず、未回収Actionsは状態を照会して保存するだけとし、同じ測定を再起動しない。

閲覧改善の全条件を満たして固定版とDL方法を提示した後に限り、保存した最新frontierとActionsを再照合して、保存容量→CI整合→追加機構の技術確認へ戻る。所有者が修正版を見て案を考える間も、実作業セッションでは独立技術を継続する。無人バックグラウンド実行の約束ではない。

## 毎回の終了

同じ固定状態JSONへ今回の実完了・限定検証・実在する閲覧版/保存先・未完・次の具体的作業・最新Actionsを記録する。完了済み受入は変更影響なしに再実行しない。両ログは追記のみ。今回の記録上の未実施は `recording.wiki_readability_priority_update` に明記し、未追記分だけ重複なく補う。

小さな区切りで通常commitし、明示許可された同branchへ非force反映する。push前後のlive HEADと対象blobを照合し、競合する変更を破棄しない。全クリは対象外（PASSではない）、保存安全性は必須のまま。merge・draft解除・公開release・active baseline切替は別途明示許可なしに行わない。

## 次回そのまま渡す指示

```text
@GitHub dekaazarashi1111-web/pokemon-vega-modern の
branch codex/modernization-followup-20260908 の最新HEADで
CHATGPT_RESUME.md を読み、指示された正本と最新Actionsを照合して、
次の未完作業を実装・検証・記録まで進め、同じbranchへ非force反映してください。
受入済みは変更影響なしに再実行せず、固定の引継ぎMD/JSONと両ログを更新してください。
merge・release・baseline切替は別途明示指示なしに行わないでください。
```
