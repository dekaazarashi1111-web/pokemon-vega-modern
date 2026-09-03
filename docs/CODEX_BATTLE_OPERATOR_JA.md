# Codex対戦 Stage 45 運用ガイド

> Stage 45は機能導入時の名称である。現在の実機依頼では古いStage 45を再生成せず、
> `design/active_play_baseline.md`に固定された現行ROMを使う。

## 対象と安全境界

Stage 45は、Stage 44の6体登録・双方3体選出・手動対戦に、対戦結果へ紐づく任意報酬を追加する。
通常運用はユーザーがCodex taskで対戦を依頼し、Codexが`vega-codex-battle`を実行する。OpenAI API
daemonやAPI keyは不要である。

CLIが読むのはversioned mailbox、公開battle state、128 byteのreward ownerだけである。プレイヤーの
未公開技・持ち物・特性・選出順・確定前入力・RNGは読まない。CLIが書くのはmailboxの宣言済みrequest
spanだけで、PCからsave、bag、party、boxを直接編集しない。NCIはplain UDPなので信頼できるLANだけで使う。

## 導入

Stage 45をbuildしたワークスペースで次を実行する。

```bash
bash scripts/install_vega_codex_battle_cli.sh
bash scripts/install_vega_codex_battle_skill.sh
```

CLIはStage 45 ROM、protocol、read-only catalogを個人用data directoryへ配置する。skill installerは
`${CODEX_HOME}/skills/vega-codex-battle`へsourceを配置する。device hostはCLIのowner-only設定へだけ保存し、
repository、skill、reportへ書かない。

## 1セッションの順序

最初に必ずread-only診断と現在状態を確認する。

```bash
vega-codex-battle doctor --json
vega-codex-battle session guide --json
vega-codex-battle match status --json
```

新規対戦では、会話で決めたルールとteamだけを明示送信する。

```bash
vega-codex-battle match configure --level flat50 --json
vega-codex-battle team validate --file TEAM.json --json
vega-codex-battle match upload-team --file TEAM.json --json
vega-codex-battle choose team 1,3,6 --json
```

対戦中は`wait`または`match view`で公開盤面を読み、現在の合法候補から呼出元が決めた操作だけを送る。

```bash
vega-codex-battle wait --timeout 55 --compact --json
vega-codex-battle choose move 2 --gimmick none --json
vega-codex-battle choose switch 3 --json
```

CLIやskillはteam、選出、行動、gimmick、報酬、乱数、理由説明、発話頻度を自動決定しない。

Codex戦は勝ち、負け、引分のいずれも通常の賞金授受と全滅ワープを行わない。結果表示後は受付へ戻り、
party、money、battle内消費を対戦前へexact復元してからreward windowを開く。家や回復地点へ移動した場合は
正常resultではないため報酬を送らず、Stage 45のROM identityとresult hookを確認する。

## 任意報酬

勝ち・負け・引分・明示forfeitの正常な`RESULT`だけが、直近session/matchにboundされたwindowを開く。
送信直前に必ず次を読む。

```bash
vega-codex-battle reward status --json
```

`available=true`かつ`window=OPEN`の時だけ、任意のitemまたは個体を送れる。複数報酬は別々の
sequenceになる。

```bash
vega-codex-battle reward item 100 --quantity 2 --json
vega-codex-battle reward mon 25 --level 50 --moves 85,98,129,237 \
  --held-item 0 --ability-slot 0 --nature 13 \
  --ivs 31,31,31,31,31,31 --evs 0,252,0,252,0,6 \
  --tera-type 13 --ball 4 --shiny --json
```

`--ability ABILITY_ID`は指定speciesのability IDからslotを解決する。省略値はmove 33、held item 0、
ability slot 0、nature 0、全IV 31、全EV 0、species第1type、非色違い、canonical item 4の
モンスターボールである。ballにはcanonical ball item IDだけを指定できる。内部ball typeは
item manifestの`ball_kind`からCFRU enumへ変換する（例: パークボール510→16、ドリームボール509→26）。
生成個体の捕獲ボール情報へ保存され、ball item自体は付与しない。
non-ball IDはROMを変更せず拒否する。

Pokémon報酬後は、PCカーソルのlevelだけで完了にせず「様子を見る」も開く。level、4技の全文、特性名・説明、
性格、捕獲ボールを指定値と照合する。画面が暗転したまま戻らない場合でも個体や送信payloadの破損と即断せず、
まず起動中ROMのidentityを`doctor --json`で確認する。旧Stage 45には概要画面hookの配置不良があるため、
修正版より前のversioned ROMでは報酬を再送しない。同じrequestの再送は表示修復にはならない。

追加報酬がなければ閉じる。報酬なしで直ちに閉じてもよい。

```bash
vega-codex-battle reward close --json
```

closeは不可逆であり、同じmatchへの追加報酬や別matchからのreplayは拒否される。

## exactly-once再試行

各rewardは`session nonce + match ID + request sequence + payload hash`で識別され、ROM側の
`PREPARED → STAGED → COMMITTED` journalを通る。CLIはnetwork write前に同じidentityとpayloadを
owner-only `reward-pending.json`へ保存する。

- timeout、応答lost、`SAVE_FAILED`では、引数を変えず同じcommandを再実行する。
- `STORAGE_FULL`では容量を空けた後、同じcommandと引数を再実行する。
- exact retryが残っている間は別の報酬を送らない。
- 成功応答前後でCLIが止まっても、再実行はROM ownerのCOMMITTEDを認識し、二重付与せず収束する。
- pending JSON、mailbox、save、bag、party、boxを手編集しない。

`INVALID_ITEM`、`INVALID_MON`等の決定的拒否は無変更であり、入力を修正して新しいrequestを送る。

## iPad配置と終了確認

iPadにはStage 45 ROMと専用save copyを新しいversioned filenameで配置する。既存ROM/saveは上書きしない。
SSH host key検査を緩めず、端末固有host、path、credentialをtracked reportへ残さない。対戦・報酬後はゲームの
通常saveを完了させ、contentを閉じて再起動し、`doctor`、`reward status`、bagまたはparty/box表示、通常進行を
再確認する。Continue後はfield上で5秒以上待ってから`reward status`を読む。Stage 45はstock load callbackの
一時領域を壊さないよう、field安定後に独立reward ownerをsector 31から遅延復元するためである。Pokémon報酬では
再起動後にもPCカーソルと「様子を見る」の両方を再確認する。PC収納または「様子を見る」を閉じた後も、
ポケモンセンター内外を問わず通常マップへ戻り5秒以上待ってから`reward status`や`reward close`を実行する。
PC Storage終了処理がEWRAM cacheをclearしても、この待機中にsector 31正本からCRC検証付きで自動復元される。
NCI writeにより
RetroAchievements hardcoreが無効化され得る点も事前に共有する。
