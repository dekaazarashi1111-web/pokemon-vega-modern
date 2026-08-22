# Codex対戦コンテンツ

`catalog.json`はStage 44のread-only構築catalog正本である。canonical
Species/Move/Item/Ability manifestとlevel/egg/TM/tutor/form learnsetからbuild時に生成し、
ROMやCLIへ戦略・構築・行動policyを埋め込まない。

## Team JSON

Teamは`schema_version: 1`と正確に6件の`team`を持つJSON objectで指定する。各memberの
必須fieldは`species_id`だけで、次を任意指定できる。

- `level`: 1..100
- `held_item_id`: 0またはcanonicalな安全held item ID
- `moves`: canonical move IDを1..4件
- `ability_slot`: 0..2
- `nature_id`: 0..24
- `ivs`: 0..31を6件
- `evs`: 0..252を6件、合計510以下
- `shiny`: boolean
- `tera_type`: canonical type ID

省略値はsession seedとslotから決定的に補完する。未知field、duplicate JSON key、invalid
ID/幅/配列長はfail-closedで拒否する。通常習得可否は構築banにしない。例は
`tests/fixtures/codex_battle_teams/valid_{minimal,full}.json`を参照する。

## 操作

```bash
vega-codex-battle doctor --json
vega-codex-battle device close-content --json
vega-codex-battle team validate --file TEAM.json --json
vega-codex-battle match configure --level flat50 --json
vega-codex-battle match upload-team --file TEAM.json --json
vega-codex-battle choose team 1,2,3 --json
vega-codex-battle match view --json
vega-codex-battle wait --timeout 55 --compact --json
vega-codex-battle choose move 1 --target 0 --gimmick none --json
vega-codex-battle choose switch 2 --json
vega-codex-battle choose forfeit --json
```

Codexが毎turn読む通常入口は`match view --json`、待機と一体化する入口は
`wait --compact --json`とする。どちらも現在の判断盤面を自己完結で返し、戦闘文eventだけは
owner-only cursor以後の新着差分にする。neutral/0の場効果、既読event全文、計算後のraw IV/EV、
ROM構造体やコードは繰り返さない。完全監査が必要なときだけ`match status --json`を使う。

compact viewには、自分の選出3体の実HP、activeのlive技/現在PP・実能力値、控えを含む技・
道具・特性・タイプ・性格・テラスタイプ・対戦levelでの計算済み能力値を載せる。相手は
画面公開HP、状態、能力ランク、場・side・遅延効果、公開済み技・道具・特性に加え、初登場順の
opaque ID（`P1..P3`）で既出個体を追跡する。opaque IDは実party slotや選出順を表さない。
技・道具・特性はAI用内部履歴ではなく、画面表示文または明示的な特性ポップアップだけから学習する。

Codex対戦中だけ相手controllerをinterposeする。`CHOOSEACTION`、`CHOOSEMOVE`、
`CHOOSEPOKEMON`はCodexの明示入力を待ち、それ以外のcontroller commandはfixed CFRU-JP
delegateへ渡す。disconnectの既定は無期限WAITで、CPU fallbackまたはforfeitは明示command
でのみ選ぶ。CLIはraw EWRAM/save dumpを公開しない。

勝敗、forfeit、abortではparty/saveのexact cleanup後も受付側の結果msgboxが閉じるまで
`field_completion_pending`を維持する。この間の`match configure`は`BUSY`であり、結果表示後に
`CodexBattleRuntime_FieldFinish`が`IDLE`へ戻してからだけ次のmatchを作れる。

RetroArchの「コンテンツを閉じる」は確認猶予があるため、`device close-content`は
`CLOSE_CONTENT`を150 ms間隔で必ず2連続送信する。単発送信へ戻さない。

iPad QA用レポートは`make codex-battle-ipad-bootstrap`で生成する。Stage 44 ROM自身の
`TrySavingData`を2回通し、slot 0/1を個別にfresh-core loadしてから`.local/`へ出力する。
既存レポートのslotやchecksumを直接加工して作らない。
