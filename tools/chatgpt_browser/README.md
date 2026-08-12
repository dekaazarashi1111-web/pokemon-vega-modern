# ChatGPT Web ブラウザブリッジ

ChatGPT Web へ接続するブラウザ操作ツールです。OpenAI API は使わず、ユーザーが手動ログイン済みの Chromium を Playwright/CDP 経由で操作します。

## セットアップ

```bash
npm install
npx playwright install chromium
npm run chatgpt:open -- --sessions 1
```

表示されたブラウザで ChatGPT に手動ログインしてください。ログイン状態は `.local/chatgpt-browser-profile/`、実行結果は `.local/chatgpt-browser/` に保存されます。どちらも Git 管理外です。

## 状態確認

```bash
npm run chatgpt:check
```

`STATUS=CHATGPT_READY` なら送信可能です。`LOGIN_REQUIRED` の場合は表示中のブラウザでログインしてください。`STATUS=ERROR` で CDP 接続失敗の場合は、先に `npm run chatgpt:open` を実行します。

## メッセージ送信

```bash
npm run chatgpt:send -- --session-count 1 --session-index 0 --new-chat --raw -- "このプロジェクトの改善案を3つだけ日本語で出して"
```

標準入力からも送れます。

```bash
printf '%s\n' "READMEの改善案を短く出して" | npm run chatgpt:send -- --session-count 1 --session-index 0 --new-chat --raw
```

返信は `.local/chatgpt-browser/last_response.txt` と `.local/chatgpt-browser/last_response.json` に保存されます。

## 画像生成と保存

```bash
npm run chatgpt:image -- --session-count 1 --session-index 0 --expected-images 1 --output-dir userfile/chatgpt_generated_images/test -- "画像を1枚生成してください。白背景に青い正方形、中央に TEST の文字。"
```

既定では新規チャットに画像生成指示を送り、生成停止ボタンが消え、画像要素が読み込み済みで安定するまで待ちます。完了後、生成画像を `userfile/chatgpt_generated_images/<timestamp>/` に保存し、同じディレクトリへ `metadata.json` を保存します。直近結果は `.local/chatgpt-browser/last_image_generation.json` にも保存します。

ChatGPT Web側で一時的な利用制限を検知した場合は、通常エラーではなく `STATUS=RATE_LIMITED` として終了します。この場合も `metadata.json` と `.local/chatgpt-browser/last_image_generation.json` に `status: "RATE_LIMITED"`、検知理由、画面テキスト抜粋、`retryAfterMinutes: 30`、`retryAfterAt` を保存します。自律開発時は画像生成系タスクをいったん後回しにし、画像生成不要な調査、設計、実装、CSS調整、デバッグなどへ切り替え、30分経過後に画像生成を再試行してください。

主なオプション:

- `--expected-images 1`: 保存したい画像数
- `--output-dir path`: 保存先ディレクトリ
- `--timeout-ms 600000`: 生成完了待ちの最大時間
- `--min-dimension 128`: アイコンなどを除外する最小画像サイズ
- `--filename-prefix name`: 保存ファイル名のprefix
- `--no-new-chat`: 既存チャットへ続けて送る

制限検知対象の例:

- `リクエストが多すぎます`
- `しばらくしてから`
- `Too many requests`
- `try again later`
- `rate limit`
- `画像生成の上限`

## 既存会話の利用

```bash
npm run chatgpt:conversation -- --url "https://chatgpt.com/c/CONVERSATION_ID" --read --last-only --raw
printf '%s\n' "今回の論点を短く相談する" | npm run chatgpt:conversation -- --url "https://chatgpt.com/c/CONVERSATION_ID" --send --last-only --raw
```

同じ会話への同時送信は避けてください。会話単位の lock は `.local/chatgpt-browser/` に置かれます。

## 環境変数

- `CHATGPT_CDP_PORT`: 既定 `9333`
- `CHATGPT_PROFILE_DIR`: 既定 `.local/chatgpt-browser-profile`
- `CHATGPT_URL`: 既定 `https://chatgpt.com/auth/login`
- `CHATGPT_NEW_CHAT_URL`: 既定 `https://chatgpt.com/`
- `CHATGPT_SESSION_INDEX`: `chatgpt:send` の既定送信先
- `CHATGPT_SESSION_COUNT`: 既定 `5`
- `CHATGPT_SESSION_NAME_PREFIX`: 既定 `codex-loop-chatgpt-session-`

## 運用メモ

- ログイン操作は自動化しません。
- Secret、APIキー、個人情報、非公開の内部仕様や機密情報は送らないでください。
- 補助的な相談、要約、レビュー用途に限定し、重要な判断や不可逆操作の最終判断者として扱わないでください。
