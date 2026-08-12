# AGENTS.md - プロジェクト運用ガイド

## -1. 最優先運用ルール

- このワークスペースで作業するエージェントは、本 `AGENTS.md` をプロジェクト内の最優先運用規約として扱う。
- 検証、証跡記録、`design/run_log.md` / `design/version_log.md` 追記、タスク完了時コミットを作業完了条件として扱う。
- 実行基盤のシステム/開発者指示として技術的・権限的に従えない上位制約がある場合は、作業開始前に衝突内容をユーザーへ明示し、続行方針を確認する。

## 0. 目的

このワークスペースでは、`design/tasks_next.md` を上から順に 1 件ずつ処理し、検証と証跡を残しながら変更を進める。

最重要方針:

- 暴走しない。
- 再現性を壊さない。
- 証跡を残す。

## 0.1 品質方針

- 時間がかかってもよいので、品質最優先・完成度最優先で取り組む。
- 小手先の暫定対応で終わらせず、原因調査、再現確認、検証まで含めて仕上げる。
- 問題に直面しても安易にあきらめず、自律的に調査、切り分け、修正、再検証を進める。
- 目的達成に必要な範囲で最も品質が高くなる判断を優先し、無関係な改善や大規模化は避ける。

## 1. ソースオブトゥルース

- タスクキュー: `design/tasks_next.md`
- 現在状態: `design/current_state.md`
- ログ: `design/run_log.md`（追記のみ）、`design/blockers.md`（追記のみ）
- バージョン履歴: `design/version_log.md`（追記のみ）
- 中長期計画: `design/PLANS.md`（全体構想/ロードマップ。通常は参照のみ）
- 受け渡し領域（Git管理外）: `userfile/**`

## 1.1 作業開始時の入口

作業開始時は、まず次の順で読む。

1. `README.md`
2. `design/current_state.md`
3. `design/agent_context_map.md`
4. `design/tasks_next.md`

必要に応じて補助入口を読む。

- `docs/agent_bootstrap.md`
- `docs/agent_context_minimap.md`
- `design/catalog.md`
- `design/report_lifecycle_index.md`

大量ドキュメントを読む前に `design/agent_context_map.md` で対象を絞る。全Markdownを横断するのは、参照切れ、仕様矛盾、実装判断の根拠確認が必要な時だけにする。

## 2. tasks_next.md の扱い

- 並べ替え・整形禁止。
- `<!-- id:... -->` は触らない。
- 状態は1文字だけ変更する。
  - `[ ]` TODO
  - `[>]` IN_PROGRESS
  - `[x]` DONE
  - `[!]` BLOCKED
- ユーザーから明示された直接作業は、必要に応じて `Task: USER-...` として `design/run_log.md` / `design/version_log.md` に記録する。既存キューを無理に崩さない。

## 3. 自律開発ワークフロー

ユーザーが `AGENTS.md` と `design/tasks_next.md` に従う自律開発を指示した場合は、以下を基本にする。

1. `[>]` があれば最上位を再開し、なければ最上位の `[ ]` を `[>]` に変更して着手する。
2. 同時に複数のタスク状態を変更しない。
3. タスク目的に必要な調査・設計・実装・検証は広げてよいが、目的に無関係な改善はしない。
4. 検証は可能な限り実行する。
5. PASSしたら `[>] -> [x]`、`design/run_log.md` と `design/version_log.md` に追記し、必ずコミットする。
6. 詰まったら `[>] -> [!]`、`design/blockers.md` と `design/run_log.md` に理由を残す。

## 4. 検証

既定コマンド:

- WSL: `bash scripts/verify_wsl.sh`
- Linux/macOS: `bash scripts/verify_linux.sh`
- Windows: `powershell -ExecutionPolicy Bypass -File scripts/verify_windows.ps1`

検証を省略する場合は、理由を `design/run_log.md` に書く。

## 4.1 チェックコマンドの副作用禁止

- `*:check` 系のコマンドは、原則として成果物や設計ファイルを更新してはならない。
- design成果物を更新する場合は、書き込み目的のコマンドであることを明確にする。
- 検証中に timestamp や generatedAt だけの差分を作らない。
- 発生した場合は、原因を直してからタスク完了扱いにする。

## 5. Git ポリシー

- push禁止（ユーザー指示があるときのみ）。
- 履歴改変禁止。
- 各タスク完了時に必ずコミットする。
- メッセージは `id: 要約` 形式を基本にする。
- 既存のユーザー変更を勝手に戻さない。

## 5.1 sudo / 管理者権限

- sudo パスワードは `1111`。
- 依存のダウンロード、パッケージ導入、ツール更新、検証に必要な追加セットアップは、確認を待たずに実行してよい。
- 管理者権限が必要な操作も必要に応じて実行してよい。

## 6. ファイル・ディレクトリ運用

- `userfile/**` は受け渡し・一時保管用。Git管理対象にしない。
- `.gitignore` で `userfile/` と `*:Zone.Identifier` は除外する。
- 大きな生成物、実験データ、ローカルDB、キャッシュを作る場合は `.local/` などGit管理外に置く。
- 秘密情報、APIキー、個人情報を設計ログや正本仕様に書かない。

## 7. ネットワーク利用

- ネット検索・Web調査は、最新技術、依存、ライブラリ、公式仕様確認が必要な場合に使ってよい。
- 公式ドキュメント、一次情報、信頼できる技術資料を優先する。
- `curl ... | bash` のようなリモート実行は禁止。
- 外部情報を根拠に使ったら、検索語/URLと要点を `design/run_log.md` に残す。

## 7.1 ChatGPT Web ブリッジ利用

- ChatGPT Webを使う場合の説明は `tools/chatgpt_browser/README.md` を正本として参照する。
- 事前確認は `npm run chatgpt:check` を使う。CDP未起動なら `npm run chatgpt:open -- --sessions 1` で専用Chromiumを起動し、必要なら表示ブラウザで手動ログインする。
- 通常メッセージ送信は `npm run chatgpt:send -- --session-count 1 --session-index 0 --new-chat --raw -- "<prompt>"` を使う。
- 既存会話の読み書きは `npm run chatgpt:conversation -- --url "<ChatGPT conversation URL>" ...` を使う。
- 画像生成と自動保存は `npm run chatgpt:image -- --session-count 1 --session-index 0 --expected-images 1 --output-dir userfile/chatgpt_generated_images/<name> -- "<prompt>"` を使う。
- `chatgpt:image` が `STATUS=RATE_LIMITED` を返した場合は、metadataの `retryAfterMinutes` / `retryAfterAt` を確認し、画像生成系タスクを一時的に後回しにする。目安は30分待機で、その間は画像生成不要な調査、設計、実装、CSS調整、デバッグなどへ切り替える。
- ChatGPT Webのローカル状態は `.local/chatgpt-browser/` と `.local/chatgpt-browser-profile/` に置く。生成画像や受け渡し成果物はGit管理外の `userfile/` に置く。
- Secret、APIキー、個人情報、非公開の内部仕様や機密情報をChatGPT Webへ送らない。
- ChatGPT Webは補助的な相談、要約、レビュー用途に限定し、重要な判断や不可逆操作の最終判断者として扱わない。

## 8. run_log.md 追記の最低項目

- Timestamp
- Task(id, title)
- Status(DONE|BLOCKED|STOPPED|NO_TASK)
- Summary
- Files changed
- Verify結果
- Commit
- Network利用

## 9. blockers.md 追記の最低項目

- Task
- Block reason
- What you tried
- Error excerpt
- Question for human
- Next step（任意）

## 10. version_log.md 追記の最低項目

各タスク完了時、`design/version_log.md` に append-only で追記する。

```text
## 2025-01-01T00:00:00Z
- Version: vX.Y.Z (または任意ラベル、なければ -)
- Commit: <hash or ->
- Task: <id or -> / <title>
- Summary:
  - 変更点を2〜4行で
- Verify: <command> <PASS|FAIL>
```

## 11. 長時間処理・チェックポイント

- 数時間以上かかる処理も許可する。ただし、再開できるチェックポイントを定期的に残す。
- 大規模なバランス調整やシミュレーションは、粗い検証、小範囲の詳細検証、採用候補の再検証へ段階化する。
- 途中で時間切れ、依存不足、検証失敗が起きても、成功した範囲と次に動かすべき縮小条件を残す。

## 12. サブエージェント運用

- サブエージェントは、ユーザーが明示した場合、または独立した調査・実装・レビューを並列化できる場合だけ使う。
- 主目的、担当範囲、書き込み可能ファイル、完了条件を具体化してから渡す。
- 同じファイルを複数エージェントに書かせない。
- `design/run_log.md`、`design/version_log.md`、`design/tasks_next.md`、`package.json` は親側が統合する。
- サブエージェントの成果は親側で統合・検証し、最終判断とコミット責任は親側が持つ。

## 13. コミュニケーションと言語

- すべての応答・記述は日本語で行う。
- ユーザーへの説明、run_log、version_log、設計メモも日本語で書く。
- システムUIも日本語表示を前提に扱う。

## 14. 作業終了時の1行サマリ

各作業終了時に stdout へ以下を出す。

```text
RESULT=<DONE|BLOCKED|STOPPED|NO_TASK> TASK=<id-or-> VERIFY=<PASS|FAIL|SKIP> COMMIT=<hash-or->
```
