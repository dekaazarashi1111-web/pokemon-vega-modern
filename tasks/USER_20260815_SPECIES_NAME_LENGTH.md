# USER-20260815-SPECIES-NAME-LENGTH — 6文字のSpecies名を全UIで欠けずに表示する

- Lane: `engine/species/ui/qa/release`
- Depends on: `T09`, `USER-20260814-BATTLE-UI`
- Queue ID: `USER-20260815-SPECIES-NAME-LENGTH`
- Baseline: v1.3.8 / commit `8539596` / ROM SHA-256 `51b154c056f5bd83cdff6d9afbe124204d88ab65137d85271480ffce4448a1f2`

## 目的

FireRed/Vega由来の「5文字＋終端」Species名ABIが残るstock UI経路を安全に拡張し、
canonical名表に完全な名前がある6文字Speciesを省略せず表示する。公式名を5文字へ略さず、
Vega既存名、フォームのbase name、性別・メガ・キョダイマックスの表示を維持する。

## 確定済みの原因と再現

- `generated/engine/species/species_names.bin` は1,621行×11 byteで、現行名の最大長は6文字。
  6文字行はformを含め134行ある。
- `scripts/build_species_surface.py::legacy_species_names` が各行を明示的に`[:5]`へ切り、
  6 byte互換表 `species_names_legacy.bin` を生成している。
- 同buildはstockの直接参照40か所を互換表へ一括repointする。これらは
  `VegaSpeciesSurface_GetSpeciesName` の11 byte adapterを通らない。
- Species 1288 エースバーンはcanonical
  `54 AE 5D 96 AE 7E FF`に対してlegacy `54 AE 5D 96 AE FF`、
  Species 1363 ムゲンダイナはcanonical
  `71 8A 7E 91 52 65 FF`に対してlegacy `71 8A 7E 91 52 FF`となる。
- v1.3.8実ROMの野生戦では「エースバー」「ムゲンダイ」と表示される。
  emulatorやsaveではなくROM側の系統的不具合である。

## 実行

1. 40個のstock直接参照をaddress・用途・row stride・出力buffer長・最大描画幅で分類し、
   機械可読なconsumer inventoryとfail-closed検査を作る。
2. 11 byte表へpointerだけを差し替えない。旧コードの6 byte strideと小さいbufferを監査し、
   consumerごとにfull-name getter、bounded copy、または必要最小限のwrapperへ置き換える。
3. 戦闘HUD／戦闘メッセージ、手持ち・概要、PC、図鑑、進化・習得、道具対象選択など、
   実際にSpecies名を表示するstock経路を6文字対応にする。
4. `VegaSpeciesSurface_GetSpeciesName` とcanonical 11 byte表を正本にし、
   `manifests/species_ids.csv`の`display_name`を省略名へ変更しない。
5. 検証済みstageを再利用し、変更所有stage以降だけを高速再生成する。

## 受入条件

- [ ] canonical全1,621行の長さ分布を検査し、6文字の134行を欠落なく列挙できる。
- [ ] 旧名前表の40 consumerを全件分類し、未監査・未移行・境界不明が0件である。
- [ ] エースバーン（1288）とムゲンダイナ（1363）が戦闘HUDと戦闘メッセージで6文字すべて表示される。
- [ ] 6文字の全134行がcanonical bytesと同じ名前を返し、末尾文字と終端を保持する。
- [ ] 5文字以下のVega既存種・追加種の名前byteが変化しない。
- [ ] アローラ等のリージョン名をbattle base nameへ不必要に付加せず、フォーム画像・性別を維持する。
- [ ] Lv.100のメガピジョットとキョダイマックスゲンガーで、フォームアイコン・名前・3桁levelが重ならない。
- [ ] 代表6文字名を手持ち・概要、PC、図鑑、進化／習得通知、道具対象選択でも実ROM確認する。
- [ ] buffer canary、EWRAM/IWRAM境界、battle pointer、旧HELP、single/double、trainer/wild、Factory/RaidがPASSする。
- [ ] tracked exact-ROM smokeが画面またはtile/text bufferを検証し、単なる名前表読出しだけでPASSしない。
- [ ] 高速差分build、対象test、BPS往復、release検証、ログ、version履歴、タスク単位commitを完了する。

## 完了

対象検証と実測値を `design/run_log.md` / `design/version_log.md` / `design/current_state.md`へ記録し、
`design/tasks_next.md`の本タスクだけを`[ ]`から`[x]`へ変更する。
`USER-20260815-SPECIES-NAME-LENGTH:`で始まるコミットを作る。
