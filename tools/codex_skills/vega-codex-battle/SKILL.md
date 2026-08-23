---
name: vega-codex-battle
description: ユーザーがPokémon Vega Stage 46 Codex対戦の開始・継続・確認・完了、明示的な対戦操作、対戦後の任意報酬、またはWindows対戦カタログからの個体・道具生成を依頼した時に、安全なCLI運用を案内する。
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
  `match view`、`reward status`、`bank status`、`session guide`。
- Wait: `wait`。ゲームまたはプレイヤーが次の入力権を持つ間に使う。
- Write: `match configure`、`match upload-team`、`choose ...`、明示的な
  disconnect/abort、`reward item`、`reward mon`、`reward close`、
  `bank item`、`bank mon`、`bank batch`。

Windows対戦カタログの依頼では、ROM内でCodex対戦NPCの前、runtime `IDLE`、reward window
`CLOSED`、通常field入力中であることを`bank status`で確認する。単件は`bank item`／`bank mon`、
複数件は`bank batch --file ...`を使う。batchが停止したら`resume_index`と同じJSONを保持し、
PCを整理して`--start-index`から再開する。カタログは減算されないtemplateであり、固有個体を
Windowsへ退避する機能だとは説明しない。不要個体は既存PCのSELECT複数選択と
SELECT+START一括逃がしを案内する。

各write直前に`match status`または`match view`を読み直す。報酬write直前には`reward status`も
読み直し、現在matchにboundされたwindowが`OPEN`の時だけ送る。複数報酬は別々の呼出しにする。
追加報酬がない時だけwindowを閉じる。closeは不可逆である。

CLIはnetwork I/O前にowner-onlyのexact reward requestを保存する。報酬がtimeoutした時、
`SAVE_FAILED`/`STORAGE_FULL`を返した時、またはexact retry待ちを示した時は、同一commandと引数を
再実行する。そのrequestがcommitするか、安全な決定的拒否をCLIが返すまで別報酬へ差し替えない。
ROM、save、party、bag、mailbox、pending JSONを直接編集しない。

CLIの公開battle stateだけを使う。未公開のプレイヤー技・道具・特性・選出順・pending input・RNG state・
private memoryを推測または要求しない。この運用にOpenAI API daemonやAPI keyは不要である。
