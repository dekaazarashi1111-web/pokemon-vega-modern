# agent_context_map.md

## 最短読書順

1. `README.md`
2. `AGENTS.md`
3. `design/current_state.md`
4. `design/tasks_next.md`

## 目的別の入口

| 目的 | 読むファイル |
|---|---|
| 全体像 | `README.md` |
| 運用ルール | `AGENTS.md` |
| 現在状態 | `design/current_state.md` |
| 次タスク | `design/tasks_next.md` |
| 全体計画 | `design/PLANS.md` |
| 設計/成果物索引 | `design/catalog.md` |
| 実行ログ | `design/run_log.md` |
| バージョン履歴 | `design/version_log.md` |
| ブロッカー | `design/blockers.md` |
| ChatGPT Web 操作 | `tools/chatgpt_browser/README.md` |

## 読みすぎ防止

- まず `design/current_state.md` とこのファイルで対象を絞ります。
- 全Markdownを横断するのは、参照切れ、仕様矛盾、実装判断の根拠確認が必要な時だけにします。
- `userfile/` は受け渡し用のGit管理外領域です。通常作業では必要なファイルだけ参照します。

