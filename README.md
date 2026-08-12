# プロジェクト README

このワークスペースは Codex Chat で継続運用するためのプロジェクトです。

## 入口

作業開始時は次を順に確認します。

1. `AGENTS.md`
2. `design/current_state.md`
3. `design/agent_context_map.md`
4. `design/tasks_next.md`

## 運用

- タスクは `design/tasks_next.md` で管理します。
- 実行ログは `design/run_log.md`、ブロッカーは `design/blockers.md` に追記します。
- バージョン履歴は `design/version_log.md` に追記します。
- 既定の検証は `bash scripts/verify_wsl.sh` です。

## ChatGPT Web ブリッジ

ChatGPT Web を補助的な相談、要約、レビュー、画像生成に使う場合は `tools/chatgpt_browser/README.md` を参照します。
