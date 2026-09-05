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

通常のChatGPT GitHub接続は読取専用です。テストを実行したと推測せず、GitHub Actionsの
`source-validation`または`private-runtime`の実行結果を証跡として扱ってください。実iPad対戦は
self-hosted `live-battle-cli`だけを使い、各write前に最新stateを読み直し、write actionでは
`confirm_write=true`を要求してください。

ROM、save、private Release資材、device credentialの本文を会話へ転載しないでください。
