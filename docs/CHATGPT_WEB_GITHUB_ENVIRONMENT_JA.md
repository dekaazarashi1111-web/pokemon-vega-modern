# ChatGPT Web向けprivate GitHub開発環境

## 目的

この文書は、private GitHub repositoryをChatGPT Webへ接続し、現行ソース・全テスト・固定mGBA・
ROM開発資材・対戦CLIの状態を同じhashで参照／検証するための入口を定める。

通常のChatGPT WebのGitHubアプリはrepositoryの読取・検索専用であり、shell実行、commit、push、
Pull Request作成、GitHub Actions起動は行わない。コードを直接編集してpushする機能はCodex製品の
境界である。このrepositoryは、ChatGPT Webには設計・コード読取を、GitHub Actionsには実行と証跡を
担当させる。ChatGPT Webのブラウザ操作でActions画面を扱える場合でも、GitHubアプリの権限とは別である。

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

GitHub-hosted runnerはprivate LANのiPadへ到達できないため、実機対戦には使わない。

## self-hosted実機対戦

repositoryのActions runnerへ`pokemon-vega-live` labelを付け、現在のWSLで起動する。runner userには
versioned `vega-codex-battle`とowner-only device設定が必要である。

Actionsの`live-battle-cli`へJSON requestを渡す。全commandは最初に`doctor`、`session guide`、
`match status`を再読する。write actionは`confirm_write=true`の時だけ実行する。

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
