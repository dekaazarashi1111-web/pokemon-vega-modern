# ChatGPT Web向けprivate GitHub開発環境

## 目的

この文書は、private GitHub repositoryをChatGPT Webへ接続し、現行ソース・全テスト・固定mGBA・
ROM開発資材・対戦CLIの状態を同じhashで参照／検証するための入口を定める。

GitHub connectorの操作範囲は、利用中のplugin、connector action control、GitHub側認可で変わる。
このrepositoryではChatGPT Webから読取、branch／commit、Draft PR、PRコメント、既存Actions再実行まで
実証済みだが、新しい`workflow_dispatch` actionは提供されていなかった。その差を吸収するため、
ChatGPT Webが実行できるownerのPRコメントを、固定allowlistのActions要求へ変換する。

## Repository構成

- 通常Git: ソース、manifest、全unit test、mGBA runner、対戦CLI、設計正本。
- private Release `private-environment-v1`: Git管理外のROM、patch、save、受領原本、固定source、
  generated report、現行build state。
- GitHub-hosted Actions: private ReleaseをSHA-256検証して復元し、unit test、Stage62 check、
  Stage62 mGBA、対戦CLIのoffline回帰を実行する。
- self-hosted Actions: 現在のWSLと同じLAN／owner-only device設定を使い、実iPadの対戦CLIを実行する。

GitHub-hosted runnerではUbuntuのsecurity revisionは現行配布版を使い、Python、host GCC、ARM GCC、
mGBAの実行版を`infra/toolchain_manifest.json`と照合する。OS package revisionやLAN／device状態まで
現行WSLと同一にする役割はself-hosted runnerが持つ。

private ReleaseはGit履歴へROMを入れない。各assetの外側SHA-256と全memberのsize／SHA-256を
`config/github_private_environment.json`およびasset内manifestで固定する。復元処理はpath traversal、
symlink、未宣言member、hash不一致を拒否する。

SSH private key、device host、credentialはReleaseへ入れない。受領済みiPad toolkitのうち
`credentials/**`と秘密鍵を含む元ZIPは明示除外する。実機接続はself-hosted runner userの
`~/.config/vega-codex-battle/device.json`とhost-local keyだけを使う。

## ChatGPT Webへ接続する

1. ChatGPT Webの「設定」→「Apps」→「GitHub」を開く。
2. GitHub側で`dekaazarashi1111-web/pokemon-vega-modern`だけを許可する。
3. 新規private repositoryが候補へ出るまで数分待つ。
4. ChatGPT Webへ`prompts/CHATGPT_WEB_GITHUB_HANDOFF_JA.md`を渡す。

GitHubアプリから見えるのは通常Gitの内容だけで、private ReleaseのROM byteは検索対象にしない。
ROM identityは設定・metadata・Actions結果から確認する。

## GitHub-hosted test

通常のpush／Pull Requestでは`source-validation`がGit管理内だけで完結するtask graph、private guard、
GitHub環境bundle／対戦wrapperのunit testを実行する。Git管理外成果まで必要な検証は、以下の
`private-runtime`を手動実行する。

Actionsの`private-runtime`を手動実行し、次から選ぶ。

- `battle-cli-offline`: 対戦runtime／報酬／Windows catalog／Box 14／protocol rebindのunit testと
  catalog実読取。
- `stage62-check`: 現行Stage61入力からStage62成果を副作用なしで照合。
- `stage62-mgba`: Stage62のmGBA fixtureを独立2 processで実行。
- `full-unit`: private環境を復元して全unit testを実行。
- `all`: Stage62 check、Stage62 mGBA、全unit test、CLI起動／catalog読取を1回の復元で実行。

### ChatGPT WebからPRコメントで起動する

ChatGPT Webは、同一repository内の対象branchでDraft PRを作成し、そのPRへ次のいずれかを1行だけ
コメントする。新しい`workflow_dispatch` toolやtoken貼付は不要である。

```text
/vega-test stage62-check
/vega-test stage62-mgba
/vega-test focused-unit
/vega-test full-unit
/vega-test battle-cli-offline
/vega-test all
```

特定のPR HEADだけを許可する場合は40桁commit SHAを末尾へ付ける。

```text
/vega-test all 93bd5d67da52eca6c99f58b15850713f3d9e0ee6
```

既定branch上の`chatgpt-comment-control`が、コメント投稿者がrepository ownerであること、対象がPRで
あること、PR headが同一repositoryであること、任意のexpected SHAが一致することを確認する。
成功した要求だけがexact PR HEADをcheckoutし、private Releaseをhash検証して復元する。結果とrun URLは
同じPRへ自動コメントされる。

`focused-unit`、`full-unit`、`all`では、artifactをChatGPT Webが直接取得できない場合にも継続できるよう、
schema、exact HEAD、件数、test ID、exception type、tracked Python source frame、skip分類、Stage62 ROM
identityをdefault branch上の固定sanitizerで検査し、限定結果を別のPRコメントへ自動返信する。例外本文、
subtest値、private入力、Actions生ログは返信しない。重複subtest failureは同じidentity／frame単位で集約する。

現在HEADのfocused全体を再測定する場合は、PRのclose／reopenやartifact取得を使わず、次を使う。

```text
/vega-test focused-unit <PR HEAD SHA>
```

返信された`Vega private test: limited result`を次の修正入力とする。`full-unit`と`all`も同じ形式で
限定結果を自動返信するため、通常は`collect-unit` markerや生ログ再取得を必要としない。

GitHub-hosted runnerはprivate LANのiPadへ到達できないため、実機対戦には使わない。

## 巨大sourceの読取と最小patch

GitHub connectorのfile取得応答にはsize上限がある。権限やprivate設定に問題がなくても、数百KiBから
数MiBのtracked textでは本文が空になったり、応答が省略されたりする場合がある。この場合は停止せず、
ownerが同一repositoryのPRへ次を1行コメントする。

```text
/vega-find tools/stage61_interaction_oracle.py gift_storage_validate_create_mon_rom <PR HEAD SHA>
/vega-read tools/stage61_interaction_oracle.py 38020 38120 <PR HEAD SHA>
```

`chatgpt-comment-control`はdefault branch上の固定bridgeでexact PR HEADをcheckoutし、最大200行の
UTF-8 text、または空白なしの検索語に一致する先頭20行だけを行番号付きで同じPRへ返す。指定できるのは
Git管理中のsource／test／文書領域だけで、
`.github`、private入力、生成物、credential候補、binaryは拒否する。必要なsymbolは通常のGitHub検索で
見つからない場合も`/vega-find`で行番号を特定し、その周辺だけを複数回読む。

修正内容が確定したら、ChatGPT WebはGitHubの通常の新規ファイル作成で次のような小さいunified diffを
対象branchへ追加する。pathは`.chatgpt/patches/<safe-name>.patch`限定で、patch file追加後の新しい
PR HEAD SHAを必ず再取得する。

```diff
diff --git a/tools/example.py b/tools/example.py
--- a/tools/example.py
+++ b/tools/example.py
@@ -10,3 +10,3 @@
-old_value = 1
+old_value = 2
```

次に、patch fileを含むHEADを指定してコメントする。

```text
/vega-patch .chatgpt/patches/fix-example.patch <patch追加後のPR HEAD SHA> tests.test_example.ExampleTests.test_value
```

Actionsはtrusted default branchのbridgeを使い、次をすべて満たす時だけ同じPR branchへ1 commitをpushする。

- 投稿者がrepository ownerで、forkではなく、指定HEADが現在のPR HEADと一致する。
- patchは64 KiB以下、既存tracked UTF-8 textの更新だけ、最大4ファイルである。
- workflow、bridge／guard、private設定、source lock、task status、ROM／save／生成物を変更しない。
- secret候補、binary、新規作成、削除、rename、mode変更、path traversalがない。
- task graphとprivate file guardがPASSする。
- Private Releaseをhash検証して復元後、指定した単一`unittest` IDがPASSする。
- テスト中にpatch対象外のtracked差分が生じない。

成功時はpatch request fileを削除し、対象変更だけを`CHATGPT-BRIDGE: apply <name>`でcommitする。結果、
old／new SHA、変更path、run URLはPRへ自動返信される。失敗時はcommit／pushしない。Actionsの成功pushは
別workflowを自動起動しないため、必要ならnew SHAを付けた`/vega-test <suite> <new SHA>`を続けて使う。

このbridgeは巨大ファイルに対するGitHub connectorの転送上限を回避するためのものに限定する。通常サイズの
ファイル、branch、PR、コメントはGitHub connectorをそのまま使う。ROM、save、Private Release本文を
PRコメントやpatchへ入れない。

## self-hosted実機対戦

repositoryのActions runnerへ`pokemon-vega-live` labelを付け、現在のWSLで起動する。runner userには
versioned `vega-codex-battle`とowner-only device設定が必要である。

Actionsの`live-battle-cli`へJSON requestを渡す。全commandは最初に`doctor`、`session guide`、
`match status`を再読する。write actionは`confirm_write=true`の時だけ実行する。

ChatGPT Webからは、対象PRへread actionを次の形式でコメントする。

```text
/vega-live {"action":"doctor"}
/vega-live {"action":"match_status"}
/vega-live {"action":"match_view"}
```

write actionは明示的に別prefixを使う。このprefixだけがwrapperへ`--confirm-write`を渡す。

```text
/vega-live-write {"action":"match_configure","level":"flat50"}
```

read prefixへwrite actionを渡すこと、write prefixへread actionを渡すこと、allowlist外action、owner以外、
fork PRはすべて拒否する。live結果も同じPRへrun URL付きで自動コメントする。

読取例:

```json
{"action":"match_view"}
```

対戦設定:

```json
{"action":"match_configure","level":"flat50"}
```

3体選出:

```json
{"action":"choose_team","selection":[1,3,6]}
```

技選択:

```json
{"action":"choose_move","index":2,"gimmick":"none"}
```

交代:

```json
{"action":"choose_switch","index":3}
```

対応actionは`doctor`、`session_guide`、`match_status`、`match_view`、`reward_status`、
`bank_status`、`vault_status`、`wait`、`match_configure`、`match_upload_team`、`choose_team`、
`choose_move`、`choose_switch`、`match_forfeit`、`match_disconnect`、`reward_close`である。
team uploadではrequestの`team`に通常の6体team JSON objectを入れる。

GitHub Actionsの各起動は独立jobであり、interactive battleでは現在stateを毎回読み直し、
次の1 commandだけを送る。複数turnを一括推測しない。

## ローカルbundle操作

```bash
make github-private-assets
make github-private-assets-check
make github-private-assets-restore
make github-battle-wrapper-test
```

Release assetを更新する時は新しいversioned tag／asset名を使い、既存assetを上書きしない。
