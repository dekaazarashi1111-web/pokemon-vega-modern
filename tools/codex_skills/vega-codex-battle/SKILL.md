---
name: vega-codex-battle
description: ユーザーがPokémon Vega Stage 47以降のCodex対戦、任意報酬、Windows対戦カタログ生成、またはBox 14とWindows間の固有個体移動を依頼した時に、versioned CLI運用を案内する。
---

# Vega Codex Battle

インストール済みの`vega-codex-battle`を使う。`PATH`になければワークスペースの
`tools/vega_codex_battle.py`を探し、どちらもなければCLI/skill installerが必要だと報告する。
端末addressやcredentialを推測しない。

実機セッションの開始時は、最初に次のread-only検査を実行する。

```bash
vega-codex-battle doctor --json
vega-codex-battle session guide --json
vega-codex-battle match status --json
```

team構築にはread-onlyの`catalog ... --json`を使う。現在のユーザー依頼と公開状態に基づいて決めた
regulation、team、3体選出、move、switch、gimmick、forfeit、disconnect、rewardだけを送る。
固定戦略、固定team、報酬table、乱数報酬、説明頻度、自動policyを追加しない。

正常な勝ち、負け、引分は通常の賞金授受や全滅ワープを行わず受付へ戻る。家や回復地点へ移動した時は
報酬を送らず、ROM identityと`match status`を読み直して不一致を報告する。

commandを次の3分類で扱う。

- Read: `doctor`、`device status`、`catalog`、`team validate`、`match status`、
  `match view`、`reward status`、`bank status`、`vault status`、`session guide`。
- Wait: `wait`。ゲームまたはプレイヤーが次の入力権を持つ間に使う。
- Write: `match configure`、`match upload-team`、`choose ...`、明示的な
  disconnect/abort、`reward item`、`reward mon`、`reward close`、
  `bank item`、`bank mon`、`bank batch`、`vault deposit`、`vault withdraw`。

Windows対戦カタログの依頼では、mapやNPC位置を問わず、runtime `IDLE`、reward window
`CLOSED`、通常field入力中であることを`bank status`で確認する。単件は`bank item`／`bank mon`、
複数件は`bank batch --file ...`を使う。batchが停止したら`resume_index`と同じJSONを保持し、
PCを整理して`--start-index`から再開する。カタログは減算されないtemplateであり、固有個体庫とは
区別する。

ユーザーが「Windowsに預ける」と依頼したら、Box 14を移動用boxとして`vault status`で確認し、
`vault deposit`を1回実行する。Box 14の全個体は、持ち物を含むCFRUの展開済みBoxPokemon 80 byte原本のまま
owner-only Windows blobへ先に永続化され、各slotの通常save成功後にBox 14から消える。ユーザーが
「Windowsから引き出す」と依頼したら`vault withdraw`を使い、省略時は現在ROMとABI互換な全個体を
Box 14の空きslotへ戻す。特定個体だけなら`vault status`のrecord IDを引数にする。timeoutや途中停止は
同じ`vault deposit`／`vault withdraw`を再実行してpending batchを再開する。mailは外部本文を80 byteで
表現できないため拒否される。save、box、transfer block、manifest、blob、pendingを手編集しない。

`vault deposit`、`vault withdraw`、`bank item`、`bank mon`、`bank batch`にCodex対戦NPC前という位置条件を
付けない。通常fieldならどのmapでもよい。対戦後報酬はresult windowを条件にするが、NPC位置は条件にしない。

各write直前に`match status`または`match view`を読み直す。報酬write直前には`reward status`も
読み直し、現在matchにboundされたwindowが`OPEN`の時だけ送る。複数報酬は別々の呼出しにする。
追加報酬がない時だけwindowを閉じる。closeは不可逆である。

CLIはnetwork I/O前にowner-onlyのexact reward requestを保存する。報酬がtimeoutした時、
`SAVE_FAILED`/`STORAGE_FULL`を返した時、またはexact retry待ちを示した時は、同一commandと引数を
再実行する。そのrequestがcommitするか、安全な決定的拒否をCLIが返すまで別報酬へ差し替えない。
ROM、save、party、bag、mailbox、pending JSONを直接編集しない。

CLIの公開battle stateだけを使う。未公開のプレイヤー技・道具・特性・選出順・pending input・RNG state・
private memoryを推測または要求しない。この運用にOpenAI API daemonやAPI keyは不要である。
