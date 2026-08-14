# 再現ビルドパイプライン

## 原則

最終ROMを手作業で継ぎ足さない。全工程をコマンド1つで再現できる状態を維持します。

```text
inputs/private/clean.gba
  -> build/reference/vega.gba
  -> build/stages/03_harness.gba
  -> build/stages/04_moves.gba
  -> build/stages/06_battle_core.gba
  -> build/stages/07_species.gba
  -> build/stages/10_engine_slice.gba
  -> build/stages/13_kanto_slice.gba
  -> build/final/vega_modern_kanto.gba
  -> dist/vega_modern_kanto.bps
```

## 各stageの要件

- 入力hashを記録する。
- 出力hashを記録する。
- 適用module一覧を記録する。
- ROM領域割当mapを出力する。
- expected-byte assertionに失敗したらそのstageを中止する。
- 前stageを上書きしない。

## T03 harness

```bash
make harness
make harness-check
```

`make harness` はclean ROMとVega IPSから毎回作り直し、Vega既知hash、32 MiB `0xFF` 拡張、allocator、expected-byte、no-op module、連続2 build、libmGBA smokeを1回のtask固有gateで確認します。生成ROMは `build/stages/03_harness.gba`、machine-readable metadataは `build/stages/03_harness.json`、人間向け結果は `reports/generated/harness_smoke.md` です。`make harness-check` はエミュレータを再実行せず、現在の入力/config fingerprintと公開済み成果を照合します。

## T04 move port

```bash
make moves
make moves-check
```

`make moves` はstage 03を入力に、Vega Move ID 0〜511、V3技調整、固定CFRU-JP 992技を単一modelへ統合します。CFRU未収録551技をappendし、game charmapの名前・説明、battle/effect/animation表、Vega固有70技のcompile済みadapter handlerを生成します。bridgeとaligned pointer 178件だけを変更し、連続2生成と固定wild battleの技実行を確認します。成果は `build/stages/04_moves.{gba,json}`、`generated/engine/moves/`、`manifests/move_ids.csv`、`reports/generated/move_port.md` です。`make moves-check` はmGBAを再実行せず、現在の入力から再構築したROM・table・allocation・runner binary identity・reportを照合します。

## T05 ID space model（ROM stageではない）

```bash
python3 scripts/build_id_spaces.py build
python3 scripts/build_id_spaces.py check
```

T05はVega既存Type/Ability/Item IDを凍結し、固定CFRU-JP/DPE-JPのsymbolとQOL追加道具をstable keyへ解決する配置前modelです。`generated/engine/ids/`、3種のID manifest、text-width結果、`reports/generated/id_space_report.md`を決定的に生成します。ROMへの配置、repoint、allocator requestは、T04とT05の両方に依存するT06がstage 04へ統合します。このためstage 05 ROMは作らず、`check`は公開済み成果のbyte照合と一時directory内のC compile probeだけを行います。

`generated/engine/ids/*_tables.c`はstable keyと分離済み意味fieldの配置前tableで、CFRUのpositional runtime ABI表をそのまま置換するものではありません。Itemのsource→canonical対応は非affineで、AbilityにもAir Lockのshiftがあるため、T06は`id_spaces.json.runtime_handoff`をhard gateとして、実`struct Item`/icon表を999行、Ability名/説明を312行のcanonical順で再生成します。全runtime consumerのrepoint、全行round-trip、source ID直index不在を検証し、`itemObtainedFlags`はT08でresize/translationするまで関連featureを無効のまま保ちます。

## T06 CFRU battle core

```bash
python3 scripts/build_battle_core.py build
python3 scripts/build_battle_core.py check
```

`build` はstage 04とT05 modelを入力に、固定CFRU-JPのbattle-only writeを隔離sandboxで2回構築します。955 writeのexpected-byte分類、allocator payload、canonical runtime表、battle-script境界、通常wild/trainer・主要戦闘経路、AI single/double、Factory/Mirage/Raid policyを検証し、2 runがbyte一致した場合だけ `build/stages/06_battle_core.{gba,json}` と4件の `reports/generated/` 成果を公開します。`check` は現在の入力fingerprint、stage identity、payload slice、allocation、report identity、進化表・固定Pokémon ABI・publish gateを副作用なしで再照合します。

## T07 Species port

```bash
make species
make species-check
```

`build` はstage 06を入力に、Vega Species 0〜411をlosslessなprefixとして固定し、DPE-JPの定義済み1415 IDを明示mappingします。primary identity 206件はVega IDへaliasし、欠落Species/form 1209件を412〜1620へappendします。T05 canonical Ability/ItemへBaseStats参照を変換し、DPE payload partitionへ1621×32 byteを配置してcanonical root 105件をrepointします。追加Species 412のparty生成をlibmGBA 2 processで検証します。`check`はエミュレータを再実行せず、現在入力からstage、manifest、table、report、smoke証跡をbyte照合します。

## T09 Species surface

```bash
make species-surface
make species-surface-check
python3 -m unittest -v tests.test_species_surface
```

`config/species_surface.json`はstage 07、T06進化ABI、T07 Species mapping、T04/T05 Move/Item alias、固定DPE ROMを入力に固定する。DPEアセット領域を元アドレスのまま保存し、ROM末尾に1621行のcanonical tableを配置する。`check`は全成果とstage 09をmemory内で再生成し、byte一致しない公開物を拒否する。

## T10 Engine vertical slice

```bash
make engine-slice
make engine-slice-check
python3 -m unittest -v tests.test_engine_vertical_slice
```

`config/feature_matrix.csv`でQOL-Aのrelease既定値とUI ownerを固定する。buildはstage 09で追加Species 445をlibmGBA 2 processで生成し、T06/T08/T09 runtimeをhost Cの継続save fixtureで結合する。release compileでdebug giftが無効、debug defineでだけ選定fixtureが有効であることを別binaryで確認する。

## T17 Regression release candidate

```bash
make regression
make regression-check
python3 -m unittest -v tests.test_regression
```

stage 16を入力に、KantoのMapHeader/layout/tileset/wild table、拡張trainer table、gym/League event、双方向portal、QOL-B Thumb overlayを実ROMへserializeする。`check`は同じstageを2回byte一致で構築し、libmGBAの自然new-game/Kanto往復を独立processで2回実行したうえで、16成果のdriftを副作用なしで拒否する。

## 最終目標コマンド

T18のrelease入口は次とする。

```bash
make clean-build
make final
make release-patch
make verify-release
```

`make trainer-rebalance` はT17を入力に、V4本編trainerの実record 648件と共有party blobを
stage 19へ結合する。`make trainer-rebalance-check` は141戦・610体のID解決、AI flags 1/3/5、
party pointer、変更span、allocator overlapを副作用なしで再照合する。

`make facility-runtime` はstage 19を入力に、クチバ受付NPC、3戦event、CFRU候補生成・
対戦policy、6体snapshot、交換、BP、sector 31保存をstage 20へ実結合する。
`make facility-runtime-check` は同じROMを再生成し、自然new-gameからのlibmGBA exact-ROM
スモーク2 processと成果物byteを副作用なしで照合する。

`make first-battle-hotfix` は検証済みstage 20を入力に、既存のQuick Claw/Custap通知直前の
hold effect 26/96再検証に加え、行動開始時にQuick Draw indicatorと実Ability 260を照合する
148-byte scheduler wrapperを適用し、stage 21を生成する。これにより、アクタシの正規Ability 64へ
残留indicatorが立った場合も、空の特性名と速度通知を反復しない。
`make first-battle-hotfix-check` は初戦3分岐、Ability 64を含む不正indicator fault injection、
正規Quick Claw / Custap / Quick Draw（Ability 260と有効な特性名）、allocation overlap 0、
clean ROMからのBPS完全往復を副作用なしで照合する。
全stageの再構築や公開release更新は行わず、最終QOL統合gateまでstage 21を後続入力として保持する。

`make hm-field-access` は検証済みstage 21へ408-byte Thumb runtimeを中央allocatorで配置し、
Vega既存HM Item 339..346をfield能力へ対応させたstage 22を生成する。CFRUの追加HM別名、
badge、party move、TM/HM適性は解禁判定に使わず、既存callbackへ入る直前だけHM所持をguardする。
`make hm-field-access-check` は8 HMの入手前後、手持ち0体／未習得／習得済み、save相当snapshot復元、
Surf中／非Surf中、既存map callback、allocation overlap 0、clean ROMからのBPS完全往復を
libmGBA 2 processと成果byteで副作用なしに照合する。公開releaseとfresh rebuildは更新しない。

`make battle-rules` は検証済みstage 22の5 battle-script root、command table、行動順・end-turn・
status hookと各handlerを固定CFRU-JP `e24a16f...` のsource/defaultへ照合する。legacy defineが全て
無効で、現行ownerが既に単一CFRU payloadだったためROM patchは追加せず、byte-identicalなstage 23を
生成する。`make battle-rules-check` は麻痺、眠り、凍り、毒、猛毒、やけど、急所、4天候を固定RNGで
再照合し、残HPを直接二重更新せず1回分だけdamageを予約すること、通常/trainer/double、Factory Trial、
Raidの現行stage回帰、allocation overlap 0、clean ROMからのBPS完全往復を確認する。libmGBA fixtureは
ROM/source/toolchain hashが一致する検証済み成果を再利用し、全stage再構築は行わない。

`make battle-ui` は検証済みstage 23を入力に、固定CFRU-JPの
`DISPLAY_REAL_MOVE_TYPE_ON_MENU` / `DISPLAY_EFFECTIVENESS_ON_MENU` source経路と同じABIを持つ
adapterを中央allocatorへ置き、タイプ・有効度表示、inline済み初期化・カーソル入力、
戦闘中の旧HELP抑止の5 entryだけをstage 24へ接続する。
判定は `EmitChooseMove` が `VisualTypeCalc` から生成した `moveTypes/moveResults` を使い、独自相性表や
Factory ROM byteを持たない。`make battle-ui-check` は等倍・タイプ不一致が元CFRUどおり空欄であること、
2×以上、0.5×以下、0×、STAB、Stellar、Tera Blast、double対象別表示、通常action→技選択、
通常のHELP設定とL/R設定でのL詳細開閉、field HELPの維持、戦闘pointer不変、
wild/trainer/Factory/Raid入力復帰、canonical文字列、allocation、BPS往復、8成果のbyte一致を
副作用なしで照合する。

`make move-memory` は検証済みstage 24を入力に、Item 347と1個目のバッジ報酬、シオウ・
カラスバのobject script、CFRU技思い出しentryをexpected-byte付きでstage 25へ接続する。
通常候補はT09のVega packed-u16/DPE 3-byte混在learnsetを現在Lv境界で読み、タマゴ候補は
固定CFRU `GetAllEggMoves` を一時RAM modeから呼ぶ。技削除は固定CFRU `SetMonMoveSlot`、
`RemoveMonPPBonus`、`ShiftMoveSlot` を通す。`make move-memory-check` は入力hash、manifest ID、
script graph、候補・解禁・削除・contextのlibmGBA結果、allocation、BPS往復、7成果を照合する。
既存stageを再利用し、公開releaseと全stage fresh rebuildは後続QOL releaseまで更新しない。

`make qol-release-smoke` はstage 20→25のhash chainと各allocationを確認し、同じ最終stage 25を
Kanto/QOL-B、Factory、初戦、HM、戦闘規則、技選択UI、わざメモリーの既存libmGBA runnerへ渡す。
`make qol-release-smoke-check` はROM/source/toolchain hashが同じ検証済みfixtureとreportを
副作用なしで再照合する。stage 20以後にserialized fieldを増やさず、HMはバッグ所持から導出し、
技管理modeはvolatile RAMだけに置く。

`make final` は既存stage 25とQOL統合fixtureを副作用なしcheckして再利用し、欠落・drift時は
`bootstrap -> T03 -> ... -> T17 -> trainer-rebalance -> facility-runtime -> stage 21..25 -> qol-release-smoke`
を固定順に実行する。最終ROMとmetadataは
`build/final/vega-modern-kanto-v1.3.5.{gba,json}` へ出し、stageを上書きしない。

### 開発用差分ROM

```bash
make fast-rom
make fast-rom-battle-ui
make fast-rom-battle-core
```

`make fast-rom`は前回PASS時と現在のGit管理・未追跡非ignore入力をhash比較し、最初の変更所有stageを
自動選択する。再利用する各stageは32 MiB ROM、PASS metadata、出力SHA-256、invariantを相互照合し、
一致しない成果を黙って継ぎ足さない。所有stageを把握している場合は上記の明示targetを使える。
最終工程はcurrentなstage 25がない場合に全chainへfallbackせず失敗し、必要な所有stageからの再生成を促す。

`make release-patch` はclean FireRed日本版Rev.0から最終ROMへのBPSを生成し、自己実装とは
独立したdecode経路で完全往復する。README、changelog、credits、checksums、known issues、
save互換性、feature matrix、build metadataだけを固定時刻・辞書順のZIPへ格納する。
`make verify-release` は書き込みを行わず、最終hash、BPS CRC/往復、全package byte、ZIP順序、
ROM/save/元IPS・UPS/private path不在を再照合する。

source revisionのclean exportと私有入力だけから完全再構築する最終gateは
`make release-fresh-check`。一時Git worktree内で `make clean-build` から実行し、final ROM、BPS、
ZIPが現worktreeとbyte一致した時だけ証跡を公開する。私有入力が無ければ明確に失敗してよいが、
ソースのみのCIは`make validate`で通る。
