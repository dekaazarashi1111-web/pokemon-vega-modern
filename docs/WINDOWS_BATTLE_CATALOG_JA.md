# Windows対戦カタログ運用手順

## これは何か

Windows上のcanonical catalogを再利用可能なテンプレート集として扱い、Codex対戦NPCの前で
指定したPokémonを通常の手持ち／PCへ、道具を通常のバッグへ生成する機能である。
GBAのPCは従来どおり14箱×30枠で、セーブ形式や箱数は拡張しない。

カタログから生成してもWindows側のテンプレートは減らない。固有個体をWindowsへ退避する
クラウドバンクではなく、対戦用個体を必要な時だけ作る仕組みである。

## 安全境界

ROMは次の条件をすべて満たす時だけ`bank`書込みを受理する。

- Codex対戦受付マップ`96/5`の通常フィールドにいる。
- 対戦runtimeが`IDLE`で、対戦・選出・結果処理中ではない。
- 対戦後の任意報酬windowが`CLOSED`である。
- PC、メニュー、scriptなど別のUIを開いていない。

条件外ではparty、box、bag、saveを変更せず`PRIVATE_BOUNDARY`で拒否する。Windows側は
mailboxの宣言済みrequest領域だけを書き、セーブ、party、boxを直接編集しない。

## 準備

Stage 46を生成する。

```bash
make windows-battle-catalog
```

成果物は`build/stages/46_windows_battle_catalog.gba`。CLIをユーザー領域へ入れる場合は次を使う。

```bash
scripts/install_vega_codex_battle_cli.sh
```

RetroArchのNetwork Command Interfaceを有効にし、初回だけ接続先を登録する。

```bash
vega-codex-battle device configure --host 127.0.0.1 --json
vega-codex-battle doctor --json
```

ROMを起動してCodex対戦NPCの前に立ち、メニューを閉じてから状態を確認する。

```bash
vega-codex-battle bank status --json
```

`available`が`true`なら生成できる。物理マップとUIの最終確認は各書込み時にROM自身が行う。

## 単件生成

Item 100を3個バッグへ入れる。

```bash
vega-codex-battle bank item 100 --quantity 3 --json
```

Species 25をLv.50で作る。手持ちが6体未満なら手持ち、満員なら空いている最初のPC枠へ入る。

```bash
vega-codex-battle bank mon 25 --level 50 --json
```

技、持ち物、特性slot、性格、IV、EV、色違い、Tera type、ボールも指定できる。

```bash
vega-codex-battle bank mon 494 --level 50 \
  --moves 200,53,85,157 --ability-slot 2 --nature 3 \
  --ivs 31,31,31,31,31,31 --evs 0,252,0,0,252,6 \
  --shiny --tera-type 16 --ball 510 --json
```

有効範囲はSpecies `1..1620`、Item `1..998`。個体指定の検査は対戦報酬と同じcanonical
Species／Move／Item／Ability境界を使う。

## 一括生成

JSONは0始まりの配列として扱う。

```json
{
  "schema_version": 1,
  "operations": [
    {"kind": "mon", "species_id": 25, "level": 50},
    {"kind": "mon", "species_id": 494, "level": 50,
     "moves": [200, 53, 85, 157], "ability_slot": 2},
    {"kind": "item", "item_id": 100, "quantity": 3}
  ]
}
```

実行する。

```bash
vega-codex-battle bank batch \
  --file tests/fixtures/windows_battle_catalog_batch.json --json
```

全行を先に検査してから、1件ずつ独立した通常save transactionとして確定する。最初の失敗で
停止し、`completed_count`、`failure.index`、`resume_index`をJSONで返す。例えば
`resume_index`が`4`なら、PCを整理した後に同じファイルを次のように再開する。

```bash
vega-codex-battle bank batch --file batch.json --start-index 4 --json
```

応答喪失、`SAVE_FAILED`、`STORAGE_FULL`ではowner-onlyの`catalog-pending.json`を保持する。
引数を変えず同じ行を再実行すれば、ROMのjournalへ再接続し、同じrequestを二重生成しない。

CLI 2.4.1以降は、別mapなどの物理境界で拒否された後にNPC前へ戻って同じ行を再実行した場合も、
未受理のsequenceと意味上のpayloadを維持したまま未使用paddingだけを更新し、ROMへ安全に再評価させる。
前回の拒否応答はaccepted sequenceまたはrejected countが進むまで完了扱いにせず、request bodyの
更新前には旧commit markerを無効化するため、中間状態を新しい応答と誤認しない。

## 不要個体の回収

既存PC画面で`SELECT`を押すと個体を複数選択でき、箱をまたいで選択できる。
選択後に`SELECT + START`で一括逃がしを確認する。通常の持ち物はバッグへ戻る。
禁止個体、mail／key item、バッグ満杯、保存失敗がある場合は既存のall-or-rollbackにより
一括処理全体を変更しない。

## 後続ROMでの再利用

CLIは特定の`FINALFIX`ファイル名を参照しない。既定では隣接または
`generated/runtime/windows_battle_catalog_protocol.json`を発見し、そのprotocol内のROM identity、
mailbox、command、catalog metadataを使う。後続ROMではStage 46 builderと同じように、直前stageの
metadata／symbols／protocolをconfigへ固定し、同じruntimeを再配置・再束縛すればよい。

検証や別配置で明示する場合だけ、次の環境変数を使う。

- `VEGA_CODEX_BATTLE_PROTOCOL`
- `VEGA_CODEX_BATTLE_ROM`
- `VEGA_CODEX_BATTLE_CATALOG`

通常運用では設定不要である。
