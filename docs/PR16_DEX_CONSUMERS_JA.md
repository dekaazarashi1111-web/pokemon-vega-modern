# PR16 図鑑保存 consumer 接続監査（読取専用）

固定source: dekaazarashi1111-web/pokemon-vega-modern @ 1c71d539e245d6a9fe83650b8a19ff3282e66c94。
固定ROM: 33554432 bytes / SHA256 06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5。

## 結論

入口 GetSetPokedexFlag(0x08088A50) と DexScreen_GetSetPokedexFlag(0x0810586C) の2個置換では不十分。SIDからnationalへ情報を落とす上流、getterを使わず旧bitmapを直接読むcount、直接clear、transaction snapshot/restoreにも接続が必要。今回の追加発見は CFRU countのlive Bag誤読、reward rollbackの直接owned clear、Factory記念品transactionの4byte snapshot、Codex模擬戦の旧52byte seen rollback。

APIは最低4層に分ける。
- OwnerFlags(ownerKey, operation): 新保存ownerだけを扱う内部API。
- SpeciesFlags(rawSID, operation): stable key表からownerを決める。natural battle/capture/gift/hatch/evolution/research/reward/facility用。
- OfficialFlags(officialNational, operation) / OfficialCount: 公式集計専用。SIDを失ったnative値をこのAPIへ流さない。
- NativeUiFlags(nativeNumber, operation) と DexScreenFlags(value, operation, indexIsSpecies): 旧Vega UI番号を明示的にownerへ解決。indexIsSpecies=trueならraw SIDとしてSpeciesFlagsへ。

global SpeciesToNationalPokedexNum(0x08042988)の挙動は変更しない。T09はRaid側が依存するregister挙動と411 native行を意図して保持している。各SID→national→flags窓かraw SIDを受け取る親関数を接続する。nativeSID129とaddedSID481のnational129 aliasはこの区別で解消する。

## 最小 late-stage 接続集合

### 1. battle entry / switch-in

raw SIDを保持する窓は0x08012A5E→0x08012A68、0x08012AB6→0x08012AC0、0x08012AD6→0x08012AE0、0x08012E96→0x08012EA0、0x08023912→0x0802391C。変換側の入力r0がraw SID。これらをSpeciesFlags(SET_SEEN)へ接続する。

active opcode0x4Eのpointer slot0x0903F588は0x080238D5であり、switch-in窓の現rootが固定ROMで確認できる。旧opcode0xF1のstock body(0x0802D148等)を直すだけでは不十分。現在のF1 pointer slot0x0903F814は0x090DE8BD。

### 2. active capture / CFRU生成・取得

CFRU atkF1_trysetcaughtmondexflags=0x090DE8BC。raw speciesをGetMonDataから取った後、0x090DE8FEと0x090DE92Cでnationalへ変換し、GET_CAUGHT/HandleSetPokedexFlagへ渡す。Mega/Gmax/Tera/form revert、battle script分岐、personalityを保ってSID-aware登録へ接続。

SetMonPokedexFlags(mon*)=0x09131100はraw monを受け取る共通入口であり、0x090D9DA0/0x090DA0E6/0x090DA202/0x090DD140の4直接callerを集約できる。Egg判定を保つ。HandleSetPokedexFlag=0x091310A8ではnationalしか残っておらず、ここだけの置換でnative/officialを復元できない。Unown/Spinda personalityはSID/owner解決後に更新する。

Repeat Ball GET_CAUGHT: conversion0x090DDF3E、flags call0x090DDF46。CreateShedinja: conversion0x090FBFFC/0x090FC00A、flags0x090FC004/0x090FC010。これらもSpeciesFlagsへ。

### 3. 旧native取得・孵化・進化・field getter

retained native codeにも多数の直接callerが残る。raw SIDを失う主窓:
- 孵化: 0x08046338→0x08046346/0x0804634E
- party登録: 0x08050098→0x080500A6/0x080500AE
- ScriptGiveMon: 0x080A144E→0x080A1462/0x080A146A
- native進化: 0x080CF9B8/0x080CF9C8、0x080CFE9C/0x080CFEAC、0x080D0A0A/0x080D0A1A
- その他mon授受: 0x080DBC0C→0x080DBC1A/0x080DBC22
- battle caught表示: 0x0804902A→0x08049034
- field/表示seen・caught参照: 0x080BEFB4、0x080BF5E2、0x080BF602、0x080CB6AE、0x080CC30A、0x080CC344、0x080CCF62、0x080E7478

旧capture窓0x0802CDBE/0x0802D148/0x0802D182は走査には現れるが、少なくともF1はactive pointerがCFRUへ向く。変更・除外はroot証拠を添えて決める。inventory上の存在をruntime到達性と同一視しない。

### 4. UI native番号・count

0x0810586Cは第3引数indexIsSpeciesを持つ。trueなら入力SIDを失う前にSpeciesFlagsへ、falseならNativeUiFlagsへ分ける。UIの一部は呼出し側が先にnational変換してfalseを渡すので、0x08104462、0x08106630、0x0810686A、0x08106BFAもSID保持への変更が必要。

native count0x08088A68、0x08088AB8、0x08105978、完成判定0x08088B00/0x08088B34/0x08088B60はnative UI/event専用集計とする。コード内のnationalという名前だけで公式1025集計へ改名しない。対象owner集合・数はnative manifestと実UI契約から固定し、数値範囲から推測しない。

DPEのCountSpeciesInDex(0x0960CB24)、GetRegionalPokedexCount(0x0960CBA4)、HasAllRegionalMons(0x0960CBF0)、HasSeenAllRegionalMons(0x0960CC34)、HasAllMons(0x0960CC74)、LoadPokedexViews(0x0960CCCC)相当コードはROM内に残る。しかしDPEが指定するstock hook entry0x08088AB8/0x08088B34/0x08088B60/0x08105978/0x081042C4は現ROMでstockであり、対象DPE entryへのdirect BL/通常pointerが見つからない。現段階はorphan候補。先行資料の「expanded dex count consumer」をactiveの証拠として使わない。

### 5. getterを使わないCFRU count

CFRU GetNationalPokedexCount=0x09131158。Save1+0x310または+0x3A6から129byteを直接popcountする。現save_layoutではlive Bagなので、bitmap getter差替え後も誤集計が残る。caller0x090DE3C8、0x090DE4CA（捕獲計算）を確認。公式捕獲数の新owner Countへ入口接続し、無効modeは明示拒否する。

### 6. 現行overlayのSID getter/setter/official集計

- acquisition_runtime: direct_registered=0x092D1C30、SetSpeciesRegistered=0x092D2010。SIDを受ける親入口またはnational_for_species呼出し前へ接続。collection/claim ledgerの意味を混ぜない。caught_count_rank内のofficial loop literal0x092D1F64はOfficialFlagsへ。source L367–392、L452–462、L671–685。
- QOL: official_caught_at_least_100。literal0x09376F2C、load0x09376EA6、call0x09376EA8。gVegaQolOfficialNationalDex配列を走査するためOfficialFlagsへ。source L725–733。
- research: dex_caught=0x093BF238。rawSID→national conversionを除去しSpeciesFlagsへ。wild_pre_caughtと戦闘後new捕獲の両方がこの入口を使う。
- reward_encounters_v2: dex_caught_entry=0x093C18A0、dex_caught_species=0x093C1900。未捕獲候補の選択、研究加算、捕獲成否に影響。source L418–438。
- facility_runtime: mark_seen旧像0x092CEBA8と再配置像0x09FF5B70は同一56byte SHA256。各像に8直接callerがあるため、最新export/rootの証明まで片方をdead扱いしない。
- factory_high_modes_v2: mark_seen=0x093C5798。GetMonData(mon)のSIDからSpeciesFlagsへ。source L828–838。

### 7. direct clear / transaction rollback

- reward clear_standard_caught=0x093C1B7C。source L809–829でSave2+0x28+(national-1)/8を直接AND消去。caller0x093C0ED4からrollbackされる。新SpeciesClearCaughtを使い、seenを残す元の意味を保つ。test_mode分岐も保つ。
- factory_shiny_memorial_runtime commit_staged=0x092DE5C4。source L491–579 register_memorial/snapshot_dex/restore_dexはseen三鏡とownedの4byteを直接snapshot/restoreする。新ownerの同じtransactionへ移し、giftのrawspecies/pool indexからownerを固定する。national<=386の旧guardを容量拡張扱いで単に外さない。
- Stage58QolItemAdapter_CodexSnapshotSeenMirrors / RestoreSeenMirrors / ContinueSeenHash。source L540–655。模擬戦前snapshot、終了rollback、Continue state hashが旧52byte×3 seenとpersonalityに固定されている。新ownerがこの保存/復帰契約から抜けると模擬戦のseenが永続化される。現patch slot0x093CB45A、0x093CD66A、0x093CCEACを署名化済み。既存snapshot buffer合計166byteを新bitmap容量として無宣言拡大しない。

### 8. 新規ゲーム / save / Continue

ClearPokedexFlags=0x08054270（40bytes）はSave2 owned/seen各52byteを直接memset。NewGame caller0x08054384。新owner ClearAllはこれと、新しい保存ownerのversioned NewGame初期化へ同時接続する。

NewGame既存入口0x08054324は0x09097169へhookされ、CFRU NewGameWipeNewSaveDataはparasite全0x2EA4をclearする。新ownerのRAM位置次第でこの一括clearとの前後関係を固定しなければならない。通常Save/cold Continue・partial save・失敗rollback・CRC/version拒否は親のstorage監査と合わせる。serializerだけの変更では上記transaction pathsは覆えない。

### 9. CFRU DexNav

CFRU全top-level src .c読取走査で、図鑑flags本体参照はcatching.c、dexnav.c、evolution.c、util.cの4ファイル。DexNavの12使用箇所は以下。
- DexNavGenerateHiddenAbility L1419
- InitDexNavHUD L1882
- CapturedAllLandBasedPokemon L2012/2022
- CapturedAllWaterBasedPokemon L2055/2068
- TryAddSpeciesToArray L2084
- DexNavPopulateEncounterList L2305（NATIONAL_DEX_UNOWN定数201、他とは異なり明示公式番号）
- PrintGUIHiddenAbility L2756
- PrintGUIHeldItems L2797
- DexNavLoadMonIcons L3515/3574

通常はrawSID→SpeciesFlagsへ。official定数201の呼出しだけはOfficialFlagsへ。national値をsearchLevel/index/groupingにも再利用する関数ではSpeciesToNational全体をidentityにしてはならず、flags呼出しへrawSIDを別に渡す必要がある。exact ROM literalとload siteはinventory参照。

## 署名付き成果物

consumer_inventory.json は候補全体identity、重要27窓のaddress/size/SHA256、direct Thumb BL 113件（うちspecies変換39、legacy flags38、UI flags27、CFRU mon登録4、CFRU count2、personality2、clear1）、28 legacy wrapper literals + 2 UI flags literals等を収録する。ROM fragments/encoded namesは含まない。

consumer_inventory.json の source_audit に、固定HEADの全overlay C/H/S走査による8一致ファイルと、固定CFRU全top-level src C走査の一致4ファイルのsourcepath/行番号を収録する。

## late-stage build方針

固定candidateの後段に独立payload/owner tableを割り当て、候補全体hashと各変更窓の旧hashを必須照合する。新APIのfar branch/trampolineはregister/stack/lr契約を窓ごとに検証する。表だけのrepointやCFRU/DPEのbytereplacement再適用はしない。T09 C再リンクを避ければStage70の0x01FD9F94/0x01FDA050/0x01FDA13C/0x01FDA174/0x01FDA1F4絶対literal契約を保持できる。

全consumerが新ownerへ統一されたという受入はまだ不可。inventoryは静的call/ literal完全走査であり、全instructionのruntime到達性を証明したものではない。上記active rootと親の保存ABI監査を合わせ、各consumerのnative smokeとSave/fresh Continueで確認する。本調査でROM/save変更・native実行・tracked編集・commit/push/Actionsはしていない。

## 一次資料

- https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/1c71d539e245d6a9fe83650b8a19ff3282e66c94/overlays/acquisition_runtime/acquisition_engine_adapter_rom.c
- https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/1c71d539e245d6a9fe83650b8a19ff3282e66c94/overlays/reward_encounters_v2/reward_encounters_v2.c
- https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/1c71d539e245d6a9fe83650b8a19ff3282e66c94/overlays/factory_shiny_memorial_runtime/factory_shiny_memorial_runtime.c
- https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/1c71d539e245d6a9fe83650b8a19ff3282e66c94/overlays/stage58_qol_world_convenience/stage58_qol_item_adapter.c
- https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/1c71d539e245d6a9fe83650b8a19ff3282e66c94/scripts/build_species_surface.py
- https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/util.c
- https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/catching.c
- https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/dexnav.c
- https://github.com/kapibarasan000/DPE-JP/blob/10ff98c85ebf37ab5cb39a41b6e9b50f06efb19e/src/updated_code.c
- https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/pokedex_screen.c
- https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/new_game.c


## 到達性区分の読み方

ACTIVE_ROOT_CONFIRMEDは現battle-script pointer等から入口と旧setterまでの連結を固定ROMで確認したもの。SOURCE_MATCHED_STATIC_CALLERS_PRESENT_REACHABILITY_NOT_FULLY_PROVENはsourceと命令形および静的callerは一致するが全動的rootを証明していないもの。ORPHAN_CANDIDATE_STOCK_HOOK_ABSENTは対応するstock hook不在のためactive扱いを避けるもの。native実行による受入は全項目未実施。
