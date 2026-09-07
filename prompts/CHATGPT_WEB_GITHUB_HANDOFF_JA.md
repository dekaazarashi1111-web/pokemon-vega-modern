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

現在HEADのfocused全体は`/vega-test focused-unit <HEAD SHA>`で起動してください。`focused-unit`、
`full-unit`、`all`は、artifactを直接取得しなくても、件数、失敗test ID、exception type、source frame、
skip分類、Stage62 ROM identityを`Vega private test: limited result`コメントとして自動返信します。
この限定コメントを正とし、Actions生ログやartifact本文を再取得しないでください。

巨大なtracked text sourceの取得本文が空、400、size制限、または応答省略になった場合、それを権限不足や
private資材不足として停止理由にしないでください。対象PRへ次を1行コメントし、返された最大200行の
sliceだけを読んでください。

```text
/vega-find <repository-relative-path> <空白なしの検索語> <現在のPR HEAD SHA>
/vega-read <repository-relative-path> <start-line> <end-line> <現在のPR HEAD SHA>
```

symbolの行番号が不明なら先に`/vega-find`を使います。検索結果は先頭20件に制限されます。

必要な周辺行を読み、根拠が確定した後だけ、小さいunified diffをGitHubの通常の新規ファイル作成で
`.chatgpt/patches/<safe-name>.patch`へcommitしてください。patch追加後のPR HEADを再取得し、単一の
focused unittest IDを指定して次を1行コメントします。

```text
/vega-patch .chatgpt/patches/<safe-name>.patch <patch追加後のPR HEAD SHA> <tests.module.Class.test_method>
```

Actionsがprivate資材を復元し、guardと指定テストを通した時だけ、patch fileを削除して修正を同じPR
branchへcommit／pushします。PRの自動返信からnew SHAを取得してください。失敗時にexpected値の緩和、
skip化、ROM／save／Release資材のGit追加、workflowやguardの変更で回避しないでください。

指定テストがFAIL／ERROR／SKIPの場合も、PRの自動返信にexact test ID、outcome、4種の件数、例外class、
Git管理中Python sourceのframeと行番号だけが表示されます。その限定結果を次の修正入力にし、例外本文、
actual／expected値、subtest値、private path、生ログやartifact本文を要求・転載しないでください。限定結果の
schema、HEAD、test ID、tracked frameを検証できない場合はコメントせずfail closedとなり、修正のcommit／pushも
行われません。

通常サイズのファイルは従来どおりGitHub connectorで直接編集してください。`/vega-read`と
`/vega-patch`の詳細な制約は`docs/CHATGPT_WEB_GITHUB_ENVIRONMENT_JA.md`を正とします。

実iPad対戦はself-hosted runnerだけを使います。readは`/vega-live <JSON>`、ユーザーが明示許可した
writeだけは`/vega-live-write <JSON>`をPRへコメントしてください。wrapperが各write前に最新stateを
再読します。reward close、bank、vault、ROM／save操作はユーザーの明示依頼なしに実行しません。

ROM、save、private Release資材、device credentialの本文を会話へ転載しないでください。
