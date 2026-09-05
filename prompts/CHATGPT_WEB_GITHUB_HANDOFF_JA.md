# ChatGPT Webへの引継ぎprompt

`dekaazarashi1111-web/pokemon-vega-modern`を対象に、日本語で作業してください。

最初に次を順番に読んでください。

1. `README.md`
2. `AGENTS.md`
3. `design/current_state.md`
4. `design/agent_context_map.md`
5. `design/tasks_next.md`
6. `docs/CHATGPT_WEB_GITHUB_ENVIRONMENT_JA.md`

現行プレイ基準はStage61、NPC配置修復候補はStage62です。タスク正本は
`USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT`がIN_PROGRESSであり、勝手にDONEへしません。

このGitHub接続では読取、branch／commit、Draft PR、PRコメント、既存run再実行を確認済みです。
新しい`workflow_dispatch` toolが無い場合はBLOCKEDにせず、対象PRへ`/vega-test <suite> [HEAD SHA]`を
1行コメントし、`chatgpt-comment-control`の新規runと自動結果コメントを確認してください。一通りの検証は
`/vega-test all <HEAD SHA>`を使います。

実iPad対戦はself-hosted runnerだけを使います。readは`/vega-live <JSON>`、ユーザーが明示許可した
writeだけは`/vega-live-write <JSON>`をPRへコメントしてください。wrapperが各write前に最新stateを
再読します。reward close、bank、vault、ROM／save操作はユーザーの明示依頼なしに実行しません。

ROM、save、private Release資材、device credentialの本文を会話へ転載しないでください。
