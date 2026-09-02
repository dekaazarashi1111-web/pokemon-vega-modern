# Stage61 表示・NPC・イベント監査 セッション引継ぎ

> **重要:** 本書前半は2026-08-31 01:14時点の履歴である。新セッションは、末尾の
> **「最新再開チェックポイント（2026-09-01T13:58:02+09:00）」**を正として再開する。
> 前半にある「builder統合が未完」等の古い未完一覧から作業をやり直さない。

- 作成: 2026-08-31T01:14:25+09:00
- Task: `USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT`
- 状態: `IN_PROGRESS`（完了・BLOCKEDではない。ユーザー要請によるセッション切替）
- Baseline: Stage60 `60_wild_species_root_repair`
- Branch: `codex/windows-battle-catalog`
- HEAD: `3b1941f36e99538c7f84a1fb233a68bac4957152`
- Commit: なし。全Stage61差分は作業treeに残っている。
- Network: インターネット未使用。

## 新セッションで最初に行うこと

1. `AGENTS.md`、`design/current_state.md`、`design/agent_context_map.md`、`design/tasks_next.md`、本書の順に読む。
2. `python3 scripts/taskctl.py next` が次を返すことを確認する。

   ```text
   RESUME USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT [auxiliary]
   ```

3. `git status --short`を確認する。未追跡のStage61実装を削除・再生成せず、そのまま再開する。既存のユーザー変更も戻さない。
4. 既存の`build/stages/61_display_npc_event_audit.gba`を最終ROMとして使わない。下記の安全なmap-script統合が未反映の旧候補である。
5. 最初の実装は「安全なmap-script projectionとLeague専用state machineのbuilder統合」。mGBA全件実走はその新ROMが生成できてから行う。

## ユーザーの最終要求

- 既知不具合だけを個別patchせず、同根不具合を全map・全event ownerから発見し、根本修正する。
- flagや関数を直接呼ぶだけでは合格にしない。
- PC上のmGBAで実際にplayerをteleport／warpし、歩行、向き変更、A入力、選択肢、field復帰まで行う。
- 初回／完了後、flag／var／item／bag容量／trainer状態など、発現条件が異なる複数状態を試す。
- 未発見の表示、NPC、イベント、セーブ、復帰バグも実機相当で調べて修正する。
- 時間やtokenより品質を優先し、未テストownerや未解決分岐を残さない。

## 現在の重要な結論

### 1. map-script欠落が複数の地形・扉不具合の根因

Stage17のcanonical Kanto importerはmap header/eventを移したが、FireRedのMapScriptsを原則移していなかった。このため、flagだけを操作しても次が成立しない。

- door／barrierの`setmetatile`
- `setmaplayoutindex`によるSeafoam等のalternate layout
- Elite Four各室の入室時移動、入口閉鎖、勝利後出口開放
- save/reloadやbattle復帰時の地形復元

FireRedの非空MapScripts 95件を丸ごと移す旧案は危険である。trainer、story、link、save、Hall of Fame、credits、warp等まで別namespaceのまま混入するため、採用禁止。

### 2. 安全なprojectionは完成、builder統合が未完

`tools/stage61_map_script_projection.py`と対応testは完成している。

- clean FireRed非空table 95件を `A21/B12/C8/D54`へexact分類。
- 184 table entries、346 root fields、139 unique roots、214 conditional rowsをroot/opcode/condition証跡付きで固定。
- A/B 33 map、34 DIRECT roots、293個のA2/A7 actionだけを有限状態で抽出。
- source conditional table、full root、write、trainer、special、link、credits、warp、saveを生成payloadへ入れない。
- Seafoamのsource layout `0x116/0x117`は、既存563件の`gMapLayouts`を保持したまま新ID 564/565へcloneする。clean border/blockdataとStage60 target tilesetの全使用metatileがexactであることを検証済み。
- Vermilion Gymの`TEMP_FLAG 0x0001`はidentity必須。producer root `0x08182FFA`／`0x08183012`とprojection consumer `0x08182E0A`のraw対応を証明済み。persistent 35 flags／5 varsだけをnon-identityにする。
- `python3 -m unittest -v tests.test_stage61_map_script_projection`: 15 tests PASS。
- `python3 tools/stage61_map_script_projection.py --require-ready`: READY、plan SHA-256 `3b948dc6951b001e4d1ffe38849aa369544e6f65483964de963df8471a7b93fa`。

### 3. Leagueはsource storyを移さずproject専用state machineにする

projection plan内の`league_explicit_adapter_contract`とbuilder内の`_materialize_project_league_map_scripts(...)`が存在する。helper単体の初期確認は通ったが、builder本線には未接続。

- `97/75..78`: tag 1/2/4/5、completion flags `0x1408..0x140B`、scene `0→1→2→3→4`。
- `97/79`: Champion entry movement `0x0816A327`の`WALK_UP×10`、scene `4→5`。
- project scene varは`0x516C`。FireRed `0x4068`をidentity使用しない。
- open／closeは証跡固定したA2だけ。FireRed本編battle/story rootはpayloadへ入れない。
- `97/80` Hall of Fameは現行project tag 3を保持し、credits/HOF source storyは移さない。
- 追補余地: Elite 4室のmovement pointer/rawをcontractのREADY assertionへさらに固定する。

### 4. 永続state namespaceの追加は途中まで統合済み

このセッション停止直前に、次を親側で追加した。

- `STAGE61_KANTO_TOPOLOGY_FLAG_MAPPING`
  - `0046→162D`, `0047→162E`, `004C→162F`, `004D→1630`
  - `0082→1631`, `02BE→1632`, `02D2→1633`, `02D3→1634`
- topology vars `4064..4067→5168..516B`
- League scene var `516C`
- `config/stage61_namespace_registry.json`へ上記ownerを追加。
- builderのregistry exact validatorと`tools/stage61_state_namespace_collision_audit.py`を新ownerへ更新。
- `config/stage61_display_npc_event_audit.json`内registry input SHAを`73df517fcee318415048f1919cae4efe2290ea32c69b43180ed0d3948523bd07`へ更新。

この変更後のbuildは未実行。collision auditの全unitも未実行。

## builderの危険な未完状態

`scripts/build_stage61_display_npc_event_audit.py`には、旧95-map一括移植経路がまだ本線として残る。

- import: `extend_relocation_plan_with_full_cfg_roots`
- `_canonical_map_script_relocation_contract(...)`
- `_materialize_canonical_map_script_tables(...)`
- build内の`map_script_contract`生成
- `semantic_complete = extend_relocation_plan_with_full_cfg_roots(...)`
- `_build_data_blob(...)`内の旧materializer呼出し

直前の旧案build試行はfull-CFG state namespace件数driftで停止した。出力は上書きされなかった。新セッションではこの旧経路を延命せず、安全projectionへ置換する。

### builder統合の具体手順

1. 次をimportする。

   ```python
   from tools.stage61_map_script_projection import (
       build_projection_plan,
       materialize_projection,
   )
   ```

2. `canonical`生成直後に次を作る。

   ```python
   map_script_projection = build_projection_plan(
       clean, stage60, canonical, require_ready=True,
   )
   ```

3. 旧95-root拡張を廃止し、通常semantic planだけからfull CFGを作る。

   ```python
   semantic_complete = semantic
   full_cfg = semantic.full_cfg_plan(clean)
   ```

4. `_build_data_blob(...)`へprojection planを渡す。
5. full-CFG materialization後、4-byte alignmentした現在blob末尾を`payload_base`として`materialize_projection(...)`を呼ぶ。
6. flag mappingは次の3集合を統合する。

   - `namespace_policy.mappings["flag"]`
   - `namespace_policy.mappings["temp_flag"]`（`0x0001→0x0001`を保持）
   - `STAGE61_KANTO_TOPOLOGY_FLAG_MAPPING`

7. var mappingは`namespace_policy.mappings["var"]`と`STAGE61_KANTO_TOPOLOGY_VAR_MAPPING`を統合する。
8. materializerのraw payloadをblobへ追加し、返却された次のexact patchだけを適用する。

   - `gMapLayouts` root pointer site
   - A/B 33 mapのmap-header MapScripts field

9. 続けて`_materialize_project_league_map_scripts(...)`を呼び、`97/75..79`の5 table patchを追加する。
10. patch categoryを旧`CANONICAL_MAP_SCRIPT_TABLE_INSTALLATION`ではなく、安全投影／League専用所有が分かる名称にする。
11. 旧3 helper/import/callは削除する。dead codeとして残して将来再有効化できる状態にしない。
12. reportへ、A/B 33、League 5、Hall of Fame preserve 1、C/D exclusion理由、source story pointer leak 0を出す。

## entry reachabilityで残る整合修正

旧exception manifestは26件だったが、map-script解析拡張後に14件のderived-only候補が現れた。

- source physical: `1/18`, `1/19`, `1/75`, `1/76`, `1/77`, `1/79`, `1/94`, `2/38`, `7/0`, `28/0`
- canonical: `97/75`, `97/76`, `97/77`, `97/79`

想定する最終分類は、単純なdiagnostic allowlist追加ではない。

- canonical cloneを持つsource map 9件: shadowed
- `2/38` Navel Rock base: 製品scope外のengine dormantを証跡化
- League 4件: `PROJECT_STATE_DEPENDENT_TOPOLOGY_ENTRY`として、実player移動のruntime transition証跡へ結ぶ

最終ROM生成後のexact producer/rootを使い、`config/stage61_entry_reachability_exceptions.json`、loader/audit、固定件数testを更新する。静的診断だけでLeagueを合格させない。

## 既に実装済みの主な根本修正

以下は作業tree内に実装されているが、最新ROMへの統合・最終mGBA再検証・完了commitはまだである。

- map section consumerのsource/project namespace分離、Kanto表示名、Town Map/Fly/Quest Log/raid consumer監査。
- 自動配置後の最終object集合監査、Diglett's Cave中央Trainer Archiveを含む到達可能性／会話port修正。
- SOURCE_DIRECT eventをclean FireRedからsemantic relocationし、数値ID・text・movement・effectを明示変換。
- Snorlax graphics closure、canonical Species 491、Tohoku flute story flag共有、Route12/16、Mr. Fuji重複配布防止。
- bag-full text-as-script 7件、Route2 EOS-only root、invalid `callstd`、gym BG敗北空文、trainer intro command等のserialization修正。
- Bill Sevii scopeを製品外航路へ入れず、有限project adapterへ置換。Sevii ferry multichoice ID衝突を拡張tableへ分離。
- invalid mapScripts、NULL coord/BG、braille pointer、misaligned goto等のroot repair。
- object visibility、trainer/archive、Raid completion flags、persistent varsのnamespace分離。
- expanded flag/var save record `S61E`、stock-save互換copy-on-write、legacy recordなしload、fault-injection基盤。
- COW damaged-sector bookkeepingをbounded direct set/clearへ修正。旧mGBAで露出したwrong damaged bitは新ROM再走待ち。
- project object `0x092D0A10`のstale `VAR_RESULT`比較をNOP化し、`checkflag 0x0820`のScriptContext comparisonResultだけを使用するpatchを追加。複数initial VAR_RESULTでの実走待ち。
- Wonder Card / signed RAM scriptのabsent／valid／corrupt fixtureとCRC／magic／program実行基盤。

## interaction oracle担当の停止時点

所有ファイル:

- `tools/stage61_interaction_oracle.py`
- `tests/test_stage61_interaction_oracle.py`

完了済み:

- 動的runtime root列挙、SemanticScriptGraph、control seed、runner fixture、decision/effect signature生成のproduction骨格。
- Bag／PC／party checksum／storage／RNG／REMATCH／doubles／PARTY_MOVE／SIGNED_RAM_SCRIPT fixture。
- signed RAM script: SB1 `+0x361C`, size `0x3EC`, Wonder Card CRC＋RamScript CRC、magic 33、program `160480a5610c`。
- engine special flagをpersistent mappingへ混ぜないguard、Billの`0x4001` atomic suppression。
- `SetHiddenItemFlag` special 150を`FlagSet(VAR_8004)` exact effectへ修正。
- OBJECT/BG/COORD/MAP/COMMON/HIDDEN trigger schemaの大幅更新。

最終検証:

- 大幅変更前の全unitは33件中31 PASS。2 FAILは旧graph node期待 `8585/11401`と現実 `8581/11397`の差だけ。
- 直近変更後は`py_compile`のみPASS。全unit未再実行。

未完:

1. hidden item 74 ownerのAVAILABLE_SUCCESS／BAG_FULL／ALREADY_COLLECTED実行。coin itemのCoin Case absent第4分岐を仕様として扱う。
2. special 350 `CheckAddCoins` exact ABIとhidden rootのABI scan追加。
3. relation-rich postconditionからrunner flat schemaへの変換。
4. deny-by-default `allowed_post_effect_families/allowed_post_effects` registryとdigest。
5. 全root実走、unresolved 0。
6. strict independent 3099 NPC catalog public API。
7. stale checkflagのflag false/true × initial VAR_RESULT複数値test。
8. COMMON caller、MAP resume nested trigger等のfocused unit。

## mGBA harness担当の停止時点

所有ファイル:

- `tools/mgba_stage61_display_npc_event_e2e.c`
- `scripts/run_stage61_mgba_validation.py`
- `tests/test_stage61_mgba_validation.py`

完了済み:

- stock warp、実歩行、face+A、fresh core/save/Continue、text printer raw capture。
- full SB1/SB2、flags/vars/bag/trainer/object/party/storage/economy/battle deltaとdeny-by-default validator骨格。
- PC capacity 4境界、popup 7 map、Bill、Fly、COW fault trace等。
- EVENT_RUNTIME dispatcher骨格: OBJECT/BG/COORD/MAP/COMMON/HIDDEN。
- SIGNED_RAM_SCRIPTのCRC、fixture、transport、C parser、scriptPtr dispatch capture、corrupt clear検査。

最終検証:

- `python3 -m py_compile scripts/run_stage61_mgba_validation.py tests/test_stage61_mgba_validation.py`: PASS。
- compile-only Werror focused test: PASS。
- SIGNED同期後の全suiteは未再実行。

未完:

1. event validatorをREMATCH専用から共通deferred control validatorへ接続し、SIGNED 3 variantを結ぶ。
2. COMMONのevent bytecode caller PCとengine consumerを分離。
3. MAP resumeをhost直callbackでなく、実stock warp→START/B field returnへする。
4. effect registryとsite/symbol単位instrumentation。
5. 全runtime ownerを動的母数でruns=2、shard実走。旧固定5342は禁止。
6. 修正版ROMでCOW、WonderCard、League、ferry、stale checkflagを再走。

旧mGBA PASS artifactは実装の縦切り参考にのみ使える。最終ROMでは全て再走する。

- PC capacity: `/tmp/stage61-pc-capacity-043a-final.json`
- popup7: `/tmp/stage61-popup7-043a-final.json`
- Bill実walk/face+A: `/tmp/stage61-bill-601176-final.json`
- Fly実Town Map選択→着地: `/tmp/stage61-fly-3up.json`
- LinkFull旧縦切り: `/tmp/stage61_link_full_e3b3_fixed.json`

## 既存生成物の扱い

現在disk上の候補:

- ROM SHA-256: `60117675d848981a2ca2ec9442bc3e7011c17140faa4e09e14eab2bae640f5b2`
- metadata SHA-256: `02136cd57b5b84bed631bd2100d26f37c62ac5f7fa951cf5ea4a73c828e6828c`
- mGBA report SHA-256: `c2c774051150fc9e2be4d1fe6a57c8c6809c2aeae1a5196d43c02967cf41a7e2`
- mGBA report mode: `compile-only`

これらは安全projection、League、最新COW、stale checkflag、signed runtimeの最終統合前であり、受入証跡ではない。新buildが成功するまで消す必要はないが、final gate入力に使わない。

## 推奨する再開順

1. projectionのElite movement pointer/raw assertionを必要なら追補し、15 unitを維持する。
2. builderから旧95-map経路を削除し、安全projection＋League helperを統合する。
3. registry/collision、entry reachability exception、report schema、固定件数を新設計に合わせる。
4. builderのtargeted unit／py_compileを通し、Stage61 ROMを一度だけ再生成する。
5. 新ROMで最初にCOW full traceを実走する。永続stateが信用できる前に多数caseを走らせない。
6. signed RAM script absent／valid／corrupt、stale checkflagのflag×VAR_RESULT matrixを実走する。
7. Seafoam alternate layoutsとVermilion TEMP_FLAG puzzleを、実warp／歩行／操作で検証する。
8. LeagueをPC→Lorelei→Bruno→Agatha→Lance→Champion→HOF方向へ実warp／歩行し、scene 0..5、扉、battle resume、save/reloadを確認する。
9. ferry menu、Bill、Fuji、flute giver、Route12/16 Snorlax、bag-full、hidden itemの全状態を実走する。
10. oracle/harnessのschemaを同期し、effect registryをdeny-by-defaultで完成させる。
11. 全runtime owner／全NPC branchをruns=2、deterministic shardsで実走し、未実行／unresolved／空文／softlock／想定外effectを0にする。
12. `build --require-mgba`で生成identityと証跡を結合する。
13. task受入条件、`design/current_state.md`、`design/run_log.md`、`design/version_log.md`を更新し、task graph/private guard/diff check後に1 task commitを作る。pushしない。

## 再開用コマンド

```bash
python3 scripts/taskctl.py next
git status --short
python3 -m unittest -v tests.test_stage61_map_script_projection
python3 tools/stage61_map_script_projection.py --require-ready
python3 -m py_compile scripts/build_stage61_display_npc_event_audit.py
python3 -m py_compile tools/stage61_interaction_oracle.py scripts/run_stage61_mgba_validation.py
python3 scripts/run_stage61_mgba_validation.py --compile-only
```

builder統合後:

```bash
python3 scripts/build_stage61_display_npc_event_audit.py build
```

最終mGBA証跡が現ROM identityへ結合された後だけ:

```bash
python3 scripts/build_stage61_display_npc_event_audit.py check --require-mgba
```

WSLでは`make validate guard test`やrepository全体verifyを一括実行しない。変更とacceptanceに直結する検査だけを選ぶ。

## checkpoint file hashes

再開時に意図しない差替えを検知するための停止時点SHA-256:

```text
7b8bf8f7249d23904ac1e2dfbfd9ec14911c6d4805879eb1c64ac5b6982fb574  tools/stage61_map_script_projection.py
80e18d789e4018c587c397265936c1d7cb6b65114581aa830ab95ca1c84247ea  tests/test_stage61_map_script_projection.py
e2d6cfe5e447aa82400d399aaa2abe0668c0165fb4240419f324c5b232489c54  tools/stage61_interaction_oracle.py
2957d5428a204ffb51f4863c7845636543d92a3790a18d5f51636c22191d09d4  tests/test_stage61_interaction_oracle.py
fbebbd881ecdb4599cff257eea93ea31f8489969ffc5847d78bf9d0f6cd9be92  tools/mgba_stage61_display_npc_event_e2e.c
1ffb67db8c59e737d6194d0432bc9b1418d28030cd7c4f455bf8fed65271878f  scripts/run_stage61_mgba_validation.py
191b8fa96439f0e93840274f6dfd0c08c1569c0bd43043911f5854ce4019155a  tests/test_stage61_mgba_validation.py
6ffb69727716799770fe79968f63fe6dbff0feed822d4437dca5ab4fdcf382e1  scripts/build_stage61_display_npc_event_audit.py
73df517fcee318415048f1919cae4efe2290ea32c69b43180ed0d3948523bd07  config/stage61_namespace_registry.json
fed786b8ed1d42f65e326980d55e70433ed0203239fe00dd51507fef44e39004  config/stage61_display_npc_event_audit.json
7b914950feb4d9ca3e42c31728abf20ec42f05598c9fc59533ba72cbf02c3801  tools/stage61_state_namespace_collision_audit.py
```

## 作業tree注意

Stage61関連の多くは`git status`で`??`であり、`git diff`には出ない。未追跡だから未実装という意味ではない。特に上記7ファイルは数千〜一万行規模の継続実装を含む。削除、再scaffold、別生成器による上書きをしない。

tracked側にもStage61のための変更が残る。`config/ram_layout.csv`、`config/save_layout.csv`、trainer/species/map importer系、task文書等は既存作業であり、個別に由来を確認せず戻さない。

## 停止時検証

- `python3 -m unittest -v tests.test_stage61_map_script_projection`: 15 tests PASS。
- projection CLI `--require-ready`: READY。
- builder、namespace collision、interaction oracle、mGBA runnerを含む対象Pythonの`py_compile`: PASS。
- final Stage61 build: 未実行。
- final ROMでのmGBA full run: 未実行。
- task完了commit: なし。

このcheckpointは進捗保存であり、Stage61の品質保証やtask完了を宣言しない。

---

## 最新再開チェックポイント（2026-08-31T16:20:18+09:00）

この節は上の01:14時点checkpointを置き換える。Stage61は引き続き
`IN_PROGRESS`であり、完了・BLOCKEDではない。ユーザー要請によるセッション切替で、
コミットはまだ作らない。

### 0. 90秒で同じ地点へ戻る手順

新セッションでは、次の順で読む。

1. `AGENTS.md`
2. `design/current_state.md`
3. `design/agent_context_map.md`
4. `design/tasks_next.md`
5. 本書のこの最新節

その後、次を実行する。

```bash
cd "$(git rev-parse --show-toplevel)"
python3 scripts/taskctl.py next
git status --short
sha256sum tools/stage61_interaction_oracle.py scripts/build_stage61_display_npc_event_audit.py scripts/run_stage61_mgba_validation.py
```

期待するtask表示:

```text
RESUME USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT [auxiliary]
```

Branchは`codex/windows-battle-catalog`、HEADは
`3b1941f36e99538c7f84a1fb233a68bac4957152`。Stage61差分の多くは未追跡である。
`git reset`、`git checkout --`、再scaffold、未追跡ファイル削除をしない。
上記HEADから再実装せず、現worktreeをそのまま使う。

### 1. Goalの引継ぎ

現セッションでは次のGoalを作成済みだった。Goal tool上のstatusは古い
`usageLimited`のままだが、ユーザーは2026-08-31に「利用上限はリセットされた」と
明示している。これは製品上のblockerではない。新セッションでactive Goalがなければ、
同じ目的をそのままGoalへ設定して続行する。再確認は不要。

```text
Stage61を引継ぎ地点から完成させる。安全なmap-script projectionとLeague専用state machineを統合し、全map・全event owner・全NPC会話を複数のflag/var/item/bag/trainer/save状態で、実際のplayer warp・歩行・向き変更・A入力・選択・field復帰を伴うmGBA実機相当E2Eにより監査する。発見した表示・NPC・イベント・保存・復帰・進行不具合を所有境界から根本修正し、未実行・未解決を0にして、対象gate、証跡ログ、タスク状態更新、最終コミットまで完了する。
```

### 2. 旧checkpoint以後に完了した実装

#### 2.1 安全なmap-script projectionとLeague統合

- builderは`build_projection_plan(...)`を本線で呼び、generic safe projectionと
  `_materialize_project_league_map_scripts(...)`をROMへ統合するところまで進んでいる。
- 旧95-map丸ごと取込案へ戻さない。
- 2026-08-31 16:18時点:

  ```text
  python3 -m unittest -q \
    tests.test_stage61_map_script_projection \
    tests.test_stage61_map_section_consumer_policy
  Ran 39 tests ... OK
  ```

#### 2.2 製品save Cの根本修正

`overlays/stage61_display_npc_event_audit/stage61_display_npc_event_audit.c`へ次を実装済み。

- prepared sectorの期待byteと全sector readbackをexact比較する。
- replacement sectorはsignature byteを最後にprogramし、precommit全体比較後に確定する。
- mismatch時はtarget recordをinvalidateする。
- `Stage61State_CommitSignatureByte`をexportし、遅延signature経路も全sector exact
  readback／invalidate契約へ統一する。
- builderのstock callsite `0x080DACD8`と`0x080DAD70`を同関数へhookする。

2026-08-31 16:19時点:

```text
gcc -std=c11 -Wall -Wextra -Werror -fsyntax-only \
  overlays/stage61_display_npc_event_audit/stage61_display_npc_event_audit.c
# PASS
```

#### 2.3 NULL BG consumer修正

- product v5の実mGBAでmap `3/38`のnumeric-zero BGが、NULLではなく無関係scriptを
  返す根因を特定した。
- builderに`0x0806C908: 01 48 -> 00 20`（`movs r0,#0`）のexact preimage修正を
  実装済み。
- **disk上の現ROMにはまだこの修正が入っていない。** 現ROMの該当function spanは
  Stage60と同じSHAのまま。次の成功buildで初めて入る。

#### 2.4 effect契約のproduction骨格

`tools/stage61_interaction_oracle.py`へ公開API
`validate_effect_registries(...)`を実装済み。

- signature/template/instance/case bindingの全partitionとbijection。
- case由来fixture/preimage/input binding。
- hidden forced-no-dispatch、no-effect full unchanged。
- `case × effect instance` raw watch plan。
- TASKは実`CreateTask`戻りtaskIdからtable slot、function引数、state、DestroyTaskまで結合。
- COMPOSITEはchild hit count、global ordinal、forbidden zero-hit、DAG順序を閉じる。
- builderはeffect registry binding、raw watch plan、retention manifestのhashを
  `--require-mgba` gateへ結合する。

担当testは2026-08-31時点で次がPASS。

```text
python3 -m unittest -q tests.test_stage61_catalog_state_matrix
Ran 43 tests ... OK
```

ただし、後述のとおりmGBA runnerがこのeffect observerをまだ実行していないため、
最終gateは意図どおりfail-closedである。

#### 2.5 runner／実mGBAの進捗

担当ファイルは次の3つ。

- `tools/mgba_stage61_display_npc_event_e2e.c`
- `scripts/run_stage61_mgba_validation.py`
- `tests/test_stage61_mgba_validation.py`

実装済み:

- checkpointごとにcurrent SB1/SB2/storage pointerを再解決し、stale pointerを拒否。
- 実map connection境界歩行、着地、first-root、後続tag、RESUME callback順の観測。
- GiveEggをhost script直呼出しではなくscheduler-only経路で観測。
- stale checkflagでflag false/trueと初期`VAR_RESULT`の複数値を実走。
- raw stdout/stderr保持helperを通常processとpersistence processへ配線。

### 3. 保存済みの実mGBA PASS証跡

`/tmp`消去による再走を避けるため、次へ複製済み。

```text
.local/stage61-handoff-20260831T1613/
```

| 証跡 | ROM | 内容 | SHA-256 |
|---|---|---|---|
| `stage61-giveegg-scheduler-stability4.json` | `c014...` | scheduler-only GiveEgg 4 runs、direct host script false | `51607eb382e5a87b36cb70f113ebc7a39763686fbc611de217d95d59f11b39d0` |
| `stage61-giveegg-scheduler6.json` | `c014...` | GiveEgg 6-path縦切り | `7b9b40dc8f5140410cb8a4bc4ddd27858b5f5aba5b469a790b61278edbd9dbe4` |
| `stage61-connection-dispatch6.json` | `c014...` | Route1 source `3/19 (0,15)`を左へ実歩行しdest `3/0 (34,15)`、root `0x087F1600`、tag 1、START→B RESUME | `e7b7f87fb3560ffe44f46bb7edd333a7eadf6e2268cd03ac6ba2afc27eedd102` |
| `stage61-stale-reresolve7.json` | `c014...` | stale-checkflag 8/8分岐、current owner再解決、old pointer reject | `f371956d6e2af400cf5efd3624562fe22ead9ea5833056f497a43934c8132839` |
| `stage61-pc-capacity-fullmem.json` | `c014...` | PC容量境界を全memory snapshotで実走 | `f4dc04b27dde48e86566a507aec88373416acc49175ea5564fc5aefdc0e8acb0` |
| `stage61-fly-3up.json` | **旧ROM `c935...`** | Town Map origin `96/23`→dest `96/4`、着地 `[6,6]` | `e16852645bed619613b9938ed0b3129e92a3fde33fa49416b62354042b46294a` |
| `stage61-fixtures-GeEJxh.json` | `c014...` | 現runner fixture | `ef26c96f63b374046939ee9bf28224fbcdccb0a0387db95c29e5580889b69fd3` |
| `stage61-runtime-trigger-diagnostic.json` | `c014...` | runtime trigger入力診断 | `5a724ae77e3e62dd8a7e7e5c5c45086a0e89fb07e11931b3dfed2d71a214625d` |

これらは調査の再実行を避けるcheckpoint証跡であり、NULL BG修正後の最終ROM証跡ではない。
最終ROM identityが変わるため、最終gateでは同経路を再走する。Flyは特に旧ROM証跡である。
強制交代経路も実mGBAでPASSを確認したが、retained reportが残っていないので最終ROMでは
必ず再走する。

### 4. 現ROM／生成物は最終版ではない

現disk上のROM:

```text
c014d6718befc079eae5254c2df90d6cf653754f5e1afecc7dedaa8df1d8224c  build/stages/61_display_npc_event_audit.gba
966ef41fdbb84494af7de1457d48bd9d07a95d98cffae9a30853da4222b878cd  build/stages/61_display_npc_event_audit.json
```

mtimeは2026-08-31 03:18。03:46以後のbuild試行は例外で`_write`前に止まったため、
NULL BG修正、最新effect契約、最新runner契約は反映されていない。
このROMを消さずに診断用として保持するが、final ROM／final mGBA gateには使わない。

直近production buildは約21分32秒、peak RSS約5.66 GiB。12 GiBの実行枠では
memory不足ではなく、次の論理errorで止まった。

```text
event owner runtime case cardinality不一致:BG:004/001:001
```

重いbuildを再実行する前に、下記P0-1〜P0-3を直す。

### 5. 即時に直すP0

#### P0-1: `BG:004/001:001`のruntime case欠落を根因修正

対象owner:

```text
owner_id: BG:004/001:001
runtime_root: 0x0817BF17
BG raw direction: ANY
trigger path kind: BG_FACE_A
start: (3,2)
walk: LEFT, LEFT
stance: (1,2)
required facing: UP
target BG: (1,1)
```

`.local/stage61-handoff-20260831T1613/stage61-runtime-trigger-diagnostic.json`では、
このpathのBFS、collision/elevation、object-free、real-walk条件はすべて成立している。
それでも`tools/stage61_interaction_oracle.py`の
`case_ids_by_owner[owner_id]`が空になり、`_owner_trigger_contract(...)`で落ちる。

次は`build_runtime_control_expansion_contract`の次を局所計測する。

- root `0x0817BF17`が`root_rows`へ存在するか。
- `assignment_paths.get(0x0817BF17)`が空か。
- candidate assignmentがあっても`paths`が空なのか。
- owner-specific required values filterで全pathを落としていないか。
- `consumer_subkind=BG_FACE_ANY`とtrigger input側`BG_FACE_A`の表記差がcase生成前に
  不正なpartitionを起こしていないか。

`allow_missing_runtime_cases`、例外list、owner除外で通してはいけない。実warp／歩行可能な
runtime-required BGなので、最低1つの実行caseを生成するのが正解。

#### P0-2: SCRIPT opcode observerのhookが1命令早い

現在のcontractは`hook_pc=0x08069118`で`R1`をopcodeとしてcaptureするが、final ROMは:

```text
08069118: 7811  ldrb r1, [r2, #0]
0806911A: 1c50  adds r0, r2, #1
```

mGBA breakpointは命令実行前なので、`0x08069118`のR1はstaleである。

推奨修正:

- hookを`0x0806911A`へ移し、そこで`R1/u8 opcode`と`R2/u32 cursor`を捕捉する。
- `0x08069118`のraw `1178`、`0x0806911A`のraw `501c`、handler table解決まで
  source/ROMへ固定する。
- oracle、builder、runner、testsを同時に同期する。

別案として`0x08069118`で`[R2]`をpointer-byte captureしてもよいが、stale R1を
expected opcodeとして使う現状は不可。

#### P0-3: effect observerをrunnerへ実接続

builderはregistry／raw watch planを生成するが、runnerはまだconsumeしていない。
現在のreportへbindingを転載するだけでは偽PASSできる。

必要な閉包:

- `case_id × instance_id × watch_id`のexact bijection。
- before/after raw bytes、hook hit順、LR、args、R0、TASK、FLASH callback/readback。
- no-dispatch caseのzero-hit。
- C/mGBAへ期待semanticを渡さず、Python validatorだけが期待contractと実観測をjoin。
- watch欠落、余分watch、case取り違え、順序変更、raw 1 byte改変のnegativeを全てFAIL。

`rg`上、runnerには現時点で`SCRIPT_CURSOR_DISPATCH`、
`effect_registry_binding`、`artifact_retention`のconsumerがない。

### 6. P0の次に直すHigh

#### 6.1 FLASH consumer closure

`tools/stage61_interaction_oracle.py`の現実装はliteral/load/transfer/BLの個別byteを
見るが、同一CFG path、PC順、介在register clobber、stack slot overwriteを閉じていない。
`inbound_roots`も自己申告に近く、initializerのSTR/source descriptorと他writer閉包も不足。

根本修正:

- entry→literal load→pointee load→MOV/spill/reload→veneer BLを連続CFGでdecode。
- 各区間の全instruction raw、successor edge、kill/genをvalidatorが再計算。
- final ROM全体のslot destination writerとinbound call/branch edgeをexact partition。
- patched/dormant分類はhook entry rawとinbound edge zeroを独立再計算。

negative: 介在clobber、偽root、追加slot writer、old-body interior inboundを各1件注入しFAIL。

#### 6.2 FLASH mutation target closure

現状は任意`code_span` hashとPROGRAM_SECTORのdirect descendant 2件だけで、全reachable
block、return、FLASH bus write leaf、interior inboundを閉じていない。

各targetについてdecoded CFG全集合、全successor/return、direct descendants、
FLASH STRB leaf、全外部inbound edgeをsource-owned closureにし、validatorが現ROMから
再計算する。span短縮、追加branch、追加write leaf、interior caller mutationをFAILさせる。

現在固定した4 slotは次。

```text
PROGRAM_BYTE   slot 0x03007474 offset  0 -> 0x081C2F61
PROGRAM_SECTOR slot 0x0300746C offset  4 -> 0x081C302D
ERASE_CHIP     slot 0x0300747C offset  8 -> 0x081C2E1D
ERASE_SECTOR   slot 0x03007480 offset 12 -> 0x081C2E91
```

ERASE_CHIPはlive consumer 0、PROGRAM_SECTOR direct descendantsは
`0x081C304E -> 0x081C2E90`と`0x081C30B8 -> 0x081C2FF4`。これらの固定値だけで
closure完成と見なさない。

#### 6.3 retained artifact lattice

builder側のdisk再hashはあるが、runnerは現状PPM中心で、完全な
`artifact_retention`を生成していない。

- case別必須roleを固定。
- persistence caseはwriter/reader before/afterの131072-byte `.srm`を必須にする。
- result内path、SHA、ROM identity、case result SHAをexact join。
- manifest外ファイル禁止。
- `.srm`欠落、1 byte改変、role差替え、path差替え、別case leaf再利用をFAIL。

SAVE_LINK製品Cは、現時点で明示された単一callback-fault契約内では追加Highなし。

### 7. 現在の短時間test状態

再開直前の正確な結果:

```text
python3 -m py_compile \
  tools/stage61_interaction_oracle.py \
  scripts/build_stage61_display_npc_event_audit.py \
  scripts/run_stage61_mgba_validation.py
# PASS

python3 -m unittest -q \
  tests.test_stage61_map_script_projection \
  tests.test_stage61_map_section_consumer_policy
# Ran 39 tests, OK

python3 -m unittest -q tests.test_stage61_catalog_state_matrix
# Ran 43 tests, OK
```

次の2 suiteは各1件だけ赤。原因を誤認して古い実装へ戻さない。

1. `tests.test_stage61_interaction_oracle`: 58件中1 ERROR

   ```text
   hidden-item field consumer Stage61 declared NULL repair外差分
   ```

   testがdisk上の旧ROM `c014...`を読む一方、新contractはNULL BG patch済みROMを要求する
   ため。実測では該当268-byte spanの現Stage61 SHAはStage60と同一
   `d44f2c40...`、期待するpatch済みSHAは`f649f100...`。成功build後に解消すべきもの。
   testの期待を旧ROMへ緩めない。

2. `tests.test_stage61_mgba_validation`: 70件中1 FAIL

   ```text
   test_all_26_final_case_anchor_keys_fail_closed_on_deletion
   AssertionError: 27 != 26
   ```

   connection case追加により`RUNNER.ALL_CASES`が27へ増えたのに固定期待26が残った。
   単に数字だけ直すより、全case anchor key exact closureを27件から導出して、追加・欠落・
   renameのnegativeがfail-closedになるようtestを更新する。

### 8. 現在の主要ファイルSHA-256

再開時に差替え検知へ使う。

```text
c504d519f12b8c77cc6523bfe32e5a70fa792ab0f91df3677cb926d314149d28  tools/stage61_interaction_oracle.py
20c3e208988fc0208efc9b1d78da078723d4b5b8b5c15b072a71a0ff638d695a  tests/test_stage61_interaction_oracle.py
5a62c24713892dfadd885e9de18f1231d4210bbd57899b77d5c2175da031cbb2  scripts/build_stage61_display_npc_event_audit.py
a3738b7785da0c327a971073b5ae790033305a2470ecc024c4ef2aad2d316182  tests/test_stage61_catalog_state_matrix.py
4f47a71abd614d3818500ec3fb40c88845949002d61720a6bbbb36697f634738  tools/mgba_stage61_display_npc_event_e2e.c
0f7beb77738f2feb315f47a20a8d07c789f5dcd2dcc076d2fcb91787db9e1f9c  scripts/run_stage61_mgba_validation.py
a369db3ad09d8e5b5059f9a1ba303427da437b4b507d04a4056aa9ac94131ab7  tests/test_stage61_mgba_validation.py
91c8f5018668f42b6c954936093515e59a224a5ce777597ccd950990b0eec6a0  overlays/stage61_display_npc_event_audit/stage61_display_npc_event_audit.c
```

### 9. 推奨する並列再開レーン

新セッションでsubagentを使う場合、同じファイルへ書かせない。

- 親: `scripts/build_stage61_display_npc_event_audit.py`とBG owner case欠落、統合、重いbuild、
  logs/status/commit。
- Lane A: `tools/stage61_interaction_oracle.py`＋対応test。SCRIPT hookとFLASH CFG/target closure。
- Lane B: mGBA C/runner/testの3ファイル。effect observer、retention、SAVE_LINK actual fault。
- Lane C: read-only final review。P0/Highのnegative bypass監査。

`design/run_log.md`、`design/version_log.md`、`design/tasks_next.md`、共有config、commitは親だけが扱う。

### 10. 次の実行順

1. `SCRIPT_CURSOR_DISPATCH` hookを正す。
2. BG owner `BG:004/001:001`のcase生成欠落を根因修正する。
3. runnerの27-case anchor unitを直し、短時間suiteをgreenにする。
4. effect observer実接続とartifact retentionを完成する。
5. FLASH consumer/target closureとnegativeを完成する。
6. その時点で初めてproduction buildを1回走らせる。
7. 新ROM hashへ全fixture/catalog/matrix/raw watchを再結合する。
8. COW保存、SaveFailedScreen wipe→retry、fresh Continue全ownerを先に実走する。
9. special flag、stale checkflag、connection、Fly、GiveEgg、forced switch、PC capacityを
   新ROMで再走する。
10. 全map／全event owner／全NPC branchを、実warp／歩行／向き／A／選択／field復帰、
    flag/var/item/bag/trainer/save多状態、runs=2 deterministic shardで実走する。
11. untested、unresolved、unexpected effect、softlock、空文をすべて0にする。
12. `check --require-mgba`、task acceptance、logs、version、taskctl done、private guard、
    最終commit。pushしない。

P0修正前に21分超のbuildを繰り返さない。フラグやrootの直接呼出しだけでmGBA合格にしない。

### 11. mGBA focused再走コマンド

現ROM上でstale-pointer限定修正を再確認する場合だけ、次を使える。

```bash
python3 scripts/run_stage61_mgba_validation.py \
  --rom build/stages/61_display_npc_event_audit.gba \
  --expected-rom-sha256 c014d6718befc079eae5254c2df90d6cf653754f5e1afecc7dedaa8df1d8224c \
  --metadata build/stages/61_display_npc_event_audit.json \
  --fixtures .local/stage61-handoff-20260831T1613/stage61-fixtures-GeEJxh.json \
  --catalog reports/generated/stage61_npc_interaction_catalog.json \
  --legacy-catalog reports/generated/stage61_npc_interaction_catalog_legacy.json \
  --state-matrix reports/generated/stage61_npc_state_matrix.json \
  --case stale_checkflag_var_result_matrix \
  --runs 1 --jobs 1 --timeout-seconds 3600 \
  --output /tmp/stage61-stale-reresolve8.json
```

ただしこれは現runnerのpost-PASS pointer限定を確認するためのfocused再走であり、
最終ROM証跡ではない。新ROM生成後は`--expected-rom-sha256`と全生成artifactを更新する。

### 12. 完了していないもの

- full production build: 未成功。
- NULL BG修正を含む新ROM: 未生成。
- effect observer actual join: 未実装。
- FLASH CFG/mutation full closure: 未実装。
- persistence必須`.srm` retention: 未実装。
- SAVE_LINK silent-success/no-op/wrong-byte、実SaveFailedScreen wipe→retry、fresh Continue
  full-owner: 未実走。
- 全runtime owner／全NPC branch actual mGBA: 未実走。
- `--require-mgba` final gate: 未PASS。
- task logs/version/status完了更新、task完了commit: 未実施。

したがって、このhandoff作成をStage61完了とは扱わない。新セッションはP0-1から同じ差分上で
直ちに再開し、既存PASS調査を再発見する作業はしない。

---

## 最新再開チェックポイント（2026-09-01T13:34:59+09:00）

この節は2026-08-31T16:20:18+09:00の節を置き換える。Stage61は引き続き
`IN_PROGRESS`であり、完了・BLOCKEDではない。ユーザーが長大化したセッションを
切り替えるよう依頼したため、P0の境界が明確になったところで停止した。
task状態の完了更新、version追記、完了commit、pushは行っていない。

### 0. 直ちに同じ編集地点へ戻る手順

新セッションでは次を読む。

1. `AGENTS.md`
2. `design/current_state.md`
3. `design/agent_context_map.md`
4. `design/tasks_next.md`
5. 本書のこの2026-09-01最新節

その後、次だけを実行する。

```bash
cd "$(git rev-parse --show-toplevel)"
python3 scripts/taskctl.py next
git status --short
sha256sum \
  tools/stage61_interaction_oracle.py \
  scripts/run_stage61_mgba_validation.py \
  tools/mgba_stage61_display_npc_event_e2e.c \
  tests/test_stage61_interaction_oracle.py \
  tests/test_stage61_mgba_validation.py
```

期待値:

```text
RESUME USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT [auxiliary]
branch: codex/windows-battle-catalog
HEAD: 3b1941f36e99538c7f84a1fb233a68bac4957152
```

停止時はtracked変更16件、未追跡68件である。Stage61の主要実装は未追跡なので、
`git diff`だけでは見えない。`git reset`、`git checkout --`、`git clean`、再scaffold、
未追跡ファイル削除を行わない。HEADから作り直さず、このworktreeをそのまま使う。

### 1. 継続するGoalと品質条件

Goal toolのactive objectiveは次である。新セッションでGoalが自動継承されていなければ、
同じ内容で作成してよい。ユーザーへの仕様再確認は不要。

```text
Stage61を引継ぎ地点から完成させる。安全なmap-script projectionとLeague専用state machineを統合し、全map・全event owner・全NPC会話を複数のflag/var/item/bag/trainer/save状態で、実際のplayer warp・歩行・向き変更・A入力・選択・field復帰を伴うmGBA実機相当E2Eにより監査する。発見した表示・NPC・イベント・保存・復帰・進行不具合を所有境界から根本修正し、未実行・未解決を0にして、対象gate、証跡ログ、タスク状態更新、最終コミットまで完了する。
```

ユーザーがこのセッションで再強調した条件:

- flag、VAR、event rootをhostから直接設定／呼出ししただけでは合格にしない。
- 実際のplayer teleport／stock warp／connection、歩行、向き、A、選択、戦闘、
  field return、save/reloadをmGBAで通す。
- TEMP clearや先行sibling map scriptなど、物理ライフサイクルでしか発現しない不具合を
  見落とさない。
- 初回、完了後、可視／非表示、trainer前後、bag空き／満杯、item有無、save破損／復旧等の
  異なる状態を試す。
- 全owner／全到達可能branch、空文、unexpected effect、softlock、未解決を0にする。

### 2. 旧checkpoint後に解決／前進した範囲

#### 2.1 旧P0の現在地

2026-08-31節の次の記述は古い。再調査や旧実装への巻き戻しをしない。

- `SCRIPT_CURSOR_DISPATCH`は`0x08069118`から`0x0806911A`へ修正済み。
  R1 opcode、R2 cursor、raw命令とhandler解決をsource／builder／runner／testへ同期済み。
- effect registry binding、raw watch、actual runner join、artifact retentionは現ソースへ
  接続済み。`scripts/run_stage61_mgba_validation.py`に
  `_build_artifact_retention`／`_validate_artifact_retention`が存在する。
- FLASH consumer／mutation closureは`STAGE61_FLASH_POINTER_CLOSURE_V2`として実装が進み、
  初期化store、pointer slot、reachable CFG、mutation descendantを再計算する。
- SAVE_LINK silent-successのerase no-op、program no-op、wrong-byte、COW fault／fresh readerの
  strict validatorがrunnerへ入っている。
- `BG:004/001:001`は4つの実quest-log状態を生成する回帰testが追加された。
- `BG:005/002:001`はfirst choice→各説明→実exitを有限被覆する回帰testが追加された。
  ただし後述のとおり、追加後のproduction buildは未実行である。
- final case anchorは27件へ追随済み。旧節の固定26件不一致は現時点のP0ではない。

これらはsource／focused test上の進捗であり、新ROM全件実走の完了宣言ではない。

#### 2.2 stateful menuを実物理操作で56 witness PASS

旧ROM `c014...`を使う局所検証だが、vending 44件とBill 12件、合計56 witnessを
stock warp、実歩行、向き、A、選択、B／明示終了で実走した。

```text
.local/stage61-stateful-final61d-WCPGjd/result.json
.local/stage61-stateful-final61d-WCPGjd/stateful.tsv
```

結果:

```text
status=PASS
fixture_count=56
vending_witness_count=44
bill_witness_count=12
failed=0
untested=0
warnings=0
actual_stock_warp_walk_face_a=true
direct_root_call_before=0
direct_root_call_after=0
required_peak_artifact_count=61
```

証跡SHA-256:

```text
9f659f73f177d961bdaff29266c548c747d8c4e7aec46f50df23420cdeb5ce74  .local/stage61-stateful-final61d-WCPGjd/result.json
306f712de48c88b28c78dcbbb75ac65582fdf3c599bd884ea9a2eb36b65cf477  .local/stage61-stateful-final61d-WCPGjd/stateful.tsv
```

これは「直接rootを叩かない」harnessの縦切り証拠として再利用する。NULL BG修正を含まない旧ROM、
かつstateful menu限定なので、最終ROMの全owner gateには代用しない。

#### 2.3 MAP条件tableのfirst-match precedence

`tools/stage61_interaction_oracle.py`へ、ROMから独立に次をdecodeする実装を追加した。

- map header、MapScripts outer table、conditional row table。
- target rowより前の同一VAR条件を全列挙する`precedence_guards`。
- targetを最初の一致にするためのguard値と、record address／raw／SHA証跡。
- oracle rootとは独立に再計算するprecedence independence guard。
- VAR control対象は`0x4000..0x40FF`または`0x5000..0x51FF`だけとし、中間gapを除外。

runner TSV、C readback、logical dispatcher callsite captureにもguardを伝播した。
MAP conditional row aliasでもroot pointerだけで合格せず、row identityを区別する方向へ進めた。

ただしこれは「単一rowを選ぶ前提」の局所修正であり、MAP全体の物理load lifecycleは未実装。
後述P0-3が完了するまでMAP owner gateは完成していない。outer tableの同一tag重複を
生成時に明示failするguardとnegative testも残る。

#### 2.4 COMMONの静的oracleを物理caller起点へ変更

`tools/stage61_interaction_oracle.py`のruntime executionはCOMMON standard rootを直接開始せず、
物理OBJECT callerから実行するよう変更済み。

- `_runtime_context(..., execution_owner=...)`はroot plan、EventDesign、NPC、visibility、
  `VAR_800F`を物理callerに束縛する。
- `_runtime_common_caller_execution_binding(...)`はdeclared common root、物理caller root、
  exact caller bytecode PC、required adjacent trace pairを固定する。
- `_runtime_execute_with_seed_discovery(...)`は
  `caller_instruction_pc -> declared_common_root`の隣接traceがないpathを除外する。
- root rowへ`physical_execution_root`と`common_caller_execution_binding`を保存する。
- direct common root実行は禁止した。

現ROMのactive COMMON 9件はすべてOBJECT callerで、standard root側はsingleton。
COMMON2／COMMON9だけ物理root `0x08756E5D`を共有し、callsiteはそれぞれ
`0x08756EA5`／`0x08756E9A`なので、別edgeとして保持する。

Python静的oracleのこの設計は保持する。ただしC実観測にはP0-1が残る。

#### 2.5 TSV／CのCOMMON proofを63列へ拡張したが、実観測にP0あり

event trigger TSVは62列から63列へ増え、次を別々に持つ。

- `root_pc`: declared COMMON standard root。
- `physical_root_pc`: 物理caller script root。
- `caller_instruction_pc`: event bytecode上のexact callstd instruction。
- `standard_index`: common index。

C／runnerにはphysical root hit、caller hit、standard root hit、ordinal、
`common_prefix_ordered`のJSON項目を追加した。strict C compileは通る。

しかし読取専用監査で、Cがevent bytecode PCをCPU命令PCのbreakpoint用途へ混同していることが
判明した。これはcompileが通っても実COMMON proofを成立させない。P0-1を必ず先に直す。

### 3. 未解決P0-1: COMMON C captureのアドレス空間混同

現在の誤り:

```text
tools/mgba_stage61_display_npc_event_e2e.c:14233付近
event_consumer_instruction_pc = trigger.caller_instruction_pc
```

`caller_instruction_pc`はevent script bytecode addressであり、CPU命令PCではない。
これをCPU instruction hookとして使ってもexact callstd hitは観測できない。

修正方針:

1. 既存のevent dispatcher hook `0x0806911A`を汎用event captureにも使う。
2. hook時のR2を実行中event opcode address、R1をopcodeとして記録する。
3. R2が`caller_instruction_pc`とexact一致することを要求する。
4. opcodeが`callstd`／`callstd_if`／`gotostd_if`の該当系で、operandのstandard indexが
   TSVの`standard_index`と一致することをdecodeする。
5. 同一ScriptContext1でphysical caller root、exact caller opcode、declared standard rootを
   orderedに観測し、cursorの隣接edgeを証明する。
6. caller opcode時の`LAST_TALKED_OBJECT == effective trigger.local_id`を要求する。
7. `consumer_hits`はexact caller opcode hitだけを数え、pointer hitとの加算をしない。

runnerのcatalog projectionにも`local_id: 0`固定が
`scripts/run_stage61_mgba_validation.py:8294`付近に残る。COMMON OBJECTではeffective triggerの
実local IDを渡す。

必須negative:

- caller PC欠落。
- standard rootが後で出るが非隣接。
- 同じstandard rootへの別callsite。
- opcode不一致、standard index不一致、ordinal逆転、LAST_TALKED不一致。
- COMMON2／9の同一物理root・別edge。
- COMMON1／5／6のvisibility flagと物理local ID。
- C sourceにevent bytecode PCをCPU-PC欄へ代入する旧式が再出現したらfail。

### 4. 未解決P0-2: `required_postconditions`のoracle／runner schema不一致

runnerの`_normalize_required_postconditions(...)`が受理するexact schemaは次の13キーだけ。

```text
flags, engine_special_flags, vars, items, trainers,
objects, warp, battle, money, coins, party, storage, persistent
```

配列系の未変更は`[]`、それ以外の未変更は`null`。値はsequence開始直前から物理
lifecycle完了後までに実際に変化するownerだけのexact finalである。

現在のoracle `_runtime_required_postconditions(...)`は14キーのraw relation wrapperを返し、
`relation`／`before`／`after`／`required_final`等を含む。runnerはこれを拒否する。
さらにOBJECT側には次が残る。

- sequence requiredが5-key `effect_contract.required_final`のまま。
- top-level `engine_special_flags`／`control_requirements`不足。
- `allowed_post_effect_families`／`allowed_post_effects`が空。
- runtime objectとtemplateが同じlocal IDで同時変更するrowをvalidatorが表現できない。

安全な修正:

1. raw `_effect_contract`は監査証跡として保持する。
2. 別の純関数 `_runner_required_postconditions(...)`を作る。
3. materialized fixture prestateへ`state.effects`を順番にfoldする。
4. pre/post diffをchanged-onlyの13キーへ射影する。
5. 未対応relation、preimage不足、非決定値は生成時fail-closed。空へ丸めない。
6. case直下とsequence内requiredはdeepcopy同値にする。
7. OBJECT、hidden item、ordinary eventを同じconverterへ通す。
8. battle開始snapshotと、勝利／逃走後field復帰のfinal stateを分離する。
   trainer battleのfinal requiredは通常`battle:null`＋`trainers.defeated:true`。

重要: 実測afterから期待値を学習してはいけない。flag／trainer bit、Bag／money／coinsの
暗号化save byteを単純な`persistent=[]`で隠してもいけない。論理domain全scanで説明済みbyteを
exact比較し、分類外raw byteだけを`persistent`へ出すか、実測beforeへsource-defined mutationを
適用してexpected byte／maskを計算する。

最低限の回帰:

- no-effect、flag、engine flag、VAR、trainerのlast-write-wins／changed-only。
- Bag add/remove、PC item非混入、money、coin saturation。
- hidden item success／full／already-collected。
- raw wrapper／余分key拒否。
- OBJECT runtime＋template同時変更。
- battle-startとpost-battle final分離。
- unsupported relation fail-fast。
- 全生成caseをmGBA起動前にnormalizerへ通す。

### 5. 未解決P0-3: MAP ownerを単一root実行から複合物理lifecycleへ置換

根因は確定済み。MAP ownerはtarget rootだけ実行しても正しいoracleにならない。
実engine順は次。

```text
stock warp / engine teleport:
TEMP_CLEAR -> tag3 -> tag1 -> tag5 -> tag4(first match) -> tag2(first match/repeat)

connection:
TEMP_CLEAR -> tag3 -> tag1 -> tag5 -> tag2

START attempt:
tag2 attempt -> START menu判定

START/B field return:
tag5 -> tag7
```

- connectionではtag4を実行しない。
- tag5はinitial loadとfield returnの2回、tag7はreturn時だけ1回。
- 0x4000..0x400Fはdestination transitionでclearされる。
- tag2がmatchするとSTARTを先取りするので、script完了後の次field-input境界で再試行する。
- condition tableもouter tag tableもROM順のfirst matchである。

現ROM集計:

```text
MAP owner 627 / scriptあり189 maps / multi-tag map owner 528
tag1=91, tag2=210, tag3=120, tag4=160, tag5=44, tag7=2
conditional owner=370, targetより前のrow=265
同root alias=39 groups / 211 row occurrences
```

oracle変更:

- MAP ownerを通常root単体case生成から外す。
- `_execute_from_state(...)`を分離し、vars／flags／effects／printersをsibling root間で保持する。
- TEMP clearをengine producerとして適用する。
- static topologyとcase別ordered executionを分ける。
- PRE_TRANSITIONとPRE_FIELD_INPUTのcontrol boundaryを別にする。
- tag2は固定600 framesでなくno-matchまで反復し、state再訪は
  `MAP_ON_FRAME_LIVELOCK`でfailする。
- composite全体のordered dispatch、ordered effect instance、final postconditionでdedupeする。

C／runner変更:

- captureをresume途中でresetせずphase markerを付ける。
- 全MAP dispatchを1本のordered bufferへ記録する。
- outer row、selected conditional row、root field、root PC、map identity、phase、ordinalを記録する。
- conditional selected rowは`0x080694DE`時のR6 root-field addressで区別する。
- direct entry `0x08069480`、conditional entry `0x08069498`、outer match
  `0x08069464/66`、direct executor `0x0806948E`、tag2 setup `0x08069548`、
  tag4 `0x08069568`のpreimageを新ROMごとに固定する。
- Cへ期待semanticを渡さず、Python validatorが独立contractとraw traceを照合する。

必須回帰:

- map `001/000`:
  `tag3 0x0887E7A2 -> tag1 0x086A5B10 -> tag4 0x08861650 -> tag2 0x08861680`。
- map `002/010`:
  `tag3 0x0816E61F -> tag1 0x0816E609 -> tag5 0x0816E5C5 -> tag2`。
  pre-transitionの`400D=0x11,4000=1`はTEMP clear後row0が勝ち、
  `PRE_FIELD_INPUT`境界で設定した時だけrow1を選ぶ。
- return時`tag5 0x0816E5C5 -> tag7 0x0816E5F9`。
- connectionでtag4、selected alias row差替え、TEMP clear欠落、sibling欠落／追加／逆転、
  tag5片方欠落、initial tag7、余分tag2、livelock、resume resetをすべてFAIL。

### 6. production buildとROMの正確な現在地

disk上のROM／metadataは依然として2026-08-31 03:18の旧候補である。

```text
c014d6718befc079eae5254c2df90d6cf653754f5e1afecc7dedaa8df1d8224c  build/stages/61_display_npc_event_audit.gba
966ef41fdbb84494af7de1457d48bd9d07a95d98cffae9a30853da4222b878cd  build/stages/61_display_npc_event_audit.json
```

NULL BG修正、最新oracle／runner／save契約を含む最終ROMではない。削除せず診断用に保持するが、
final gateへ使わない。

最後に走らせた重いbuildのlog:

```text
.local/stage61-final-build.log
SHA-256 5052b21d338fc2c8cfd9175529ace6e53eb6658932c613aab970129934d42ba0
event owner runtime case cardinality不一致:BG:005/002:001
```

その後、BG:005/002の有限menu回帰testを追加したが、production buildは再実行していない。
現在の3つのP0を直す前に20分超／約5.7 GiBの重いbuildを繰り返さない。

### 7. 停止時の短時間検証

2026-09-01 13:32に次を再実行した。

```text
python3 -m py_compile \
  tools/stage61_interaction_oracle.py \
  scripts/run_stage61_mgba_validation.py
# PASS

python3 -m unittest -v \
  tests.test_stage61_interaction_oracle.Stage61RuntimeControlFocusedTests.test_common_runtime_binding_starts_at_physical_caller \
  tests.test_stage61_mgba_validation.Stage61MgbaValidationTests.test_map_condition_precedence_guard_flattens_with_rom_evidence \
  tests.test_stage61_mgba_validation.Stage61MgbaValidationTests.test_common_effective_object_requires_direction_plus_a \
  tests.test_stage61_mgba_validation.Stage61MgbaValidationTests.test_map_resume_nested_contract_flattens_exact_tsv
# Ran 4 tests, OK

cc -std=c11 -O2 -Wall -Wextra -Werror -pedantic \
  tools/mgba_stage61_display_npc_event_e2e.c \
  -o .local/stage61-handoff-common-prefix-compile -lmgba
# PASS
```

C compile PASSはP0-1のsemantic正しさを意味しない。full interaction／runner suites、
production build、最終ROM mGBA fullはこの区切りでは走らせていない。

### 8. 停止時の主要ファイルSHA-256

```text
2652eddc6a2914cfcd50c8f0e95ef4ce95986b09b20ae40df54f23b19e8166ab  tools/stage61_interaction_oracle.py
54a15ab958a4d690ecac5cbf8d7b0b9ca679b6db70f6b2a1e977fc83fafa5512  tests/test_stage61_interaction_oracle.py
a92fb4d2121487a1b6783409de9bd10bc33a4c597abbdbb95742822f6c94e21d  scripts/build_stage61_display_npc_event_audit.py
5810ebbbdbbee7cb2918283b2e560ebe4202c0f92c0732c2ea51fa97709d5154  tests/test_stage61_catalog_state_matrix.py
144124d84f51449d2a673188d9865533c1570fda979a345acec1d64a00379a2d  scripts/run_stage61_mgba_validation.py
98d1d9cdd1ac3266c1b3e562716b8f28a3e4b67aa7e1243addc55e156495cb4a  tests/test_stage61_mgba_validation.py
feb7758cd68ac7b3000dd6ecd9749c02bfff90ae2fefff45d5a355d98dcbea3d  tools/mgba_stage61_display_npc_event_e2e.c
87de6de079128004514aebd91dd5858afd7048357d71ad14fb7f7c60635c0360  overlays/stage61_display_npc_event_audit/stage61_display_npc_event_audit.c
0636fc561dfdb633605c596a928c52d019dae6e9c3b089fe0e29fa849079bf5a  config/stage61_display_npc_event_audit.json
5717171e8f26cb8b4ee44d29b9178c7fd84c1f661831211fcec43c010c1e9c01  tools/stage61_catalog_state_matrix.py
b2038c34f47e12914e855fb9ae6f1632672688d1dda86dffba75bf2ac1e8202e  .local/stage61-handoff-common-prefix-compile
```

`git status --porcelain=v2`の停止時SHA-256は
`4c2dae3dcac99bc0ff6761a4d493e61d1c675e460a5bd42378b3b55b859b9067`。
handoff／run log追記後は当然変わるため、上記core file hashを再開同一性の主確認に使う。

### 9. 次セッションの実装順

1. COMMON C captureをdispatcher `0x0806911A`上のevent bytecode観測へ直し、effective local IDを
   渡して全negativeを追加する。Python静的caller起点設計は戻さない。
2. raw effect contractからrunner-ready 13-key changed-only exact postconditionを生成する
   純関数とOBJECT／hidden／battle統合を実装する。
3. MAP owner caseを単一rootからcomposite lifecycleへ置換し、C ordered dispatch bufferと
   Python独立validatorを実装する。
4. 上記3境界のfocused test後に、次の短時間suiteを走らせる。

   ```bash
   python3 -m unittest -q \
     tests.test_stage61_interaction_oracle \
     tests.test_stage61_catalog_state_matrix \
     tests.test_stage61_mgba_validation
   ```

5. その時点で初めてproduction buildを1回走らせ、BG:005/002を含む全owner生成を確認する。
6. 新ROM hashへcatalog、matrix、fixture、effect watch、retention manifestを再結合する。
7. COW、silent-success、SaveFailedScreen wipe→retry、fresh Continue全ownerを先に実走する。
8. connection、Fly、GiveEgg、forced switch、PC capacity、stateful menu、MAP lifecycle、
   COMMON2／9、visibility COMMONを新ROMで再走する。
9. 全map／全event owner／全NPC branchを実warp／歩行／向き／A／選択／battle／field return、
   flag／VAR／item／bag／trainer／save多状態、runs=2 deterministic shardで実走する。
10. `untested=0`、`unresolved=0`、unexpected effect 0、softlock 0、空文0を確認する。
11. task acceptance、`check --require-mgba`、targeted native gate、task graph、private guard、
    diff checkをPASSする。
12. `design/run_log.md`／`design/version_log.md`へ完了追記し、`taskctl.py done`、意図差分だけを
    stage、最終commit。pushしない。

### 10. サブエージェント再利用時の所有境界

このcheckpoint作成時の3 agentは全員読取専用監査を完了しており、実行中processはない。
新セッションで再度並列化するなら同じファイルへ書かせない。

- 親: 統合、builder、production build、logs／status／commit。
- Lane A: COMMON C capture＋runner projection＋対応test。
- Lane B: postcondition converter設計／実装。ただし`tools/stage61_interaction_oracle.py`を
  親またはMAP laneと同時編集しない。
- Lane C: MAP compositeのread-only reviewまたはC observer。Python oracleの同時編集を避ける。

`design/run_log.md`、`design/version_log.md`、`design/tasks_next.md`、`package.json`、共有config、
commitは親だけが扱う。

### 11. 完了していないもの

- COMMON exact caller edgeの実mGBA proof。
- runner-ready required postcondition全domain。
- MAP sibling／TEMP clear／tag2反復／tag5×2／tag7を含むcomposite lifecycle。
- 上記を含む成功production buildと新Stage61 ROM。
- 新ROMでのCOW／SAVE_LINK／fresh Continue full gate。
- 新ROMでの全runtime owner／全NPC branch actual mGBA runs=2。
- final `--require-mgba`、task acceptance、logs／version完了、task done、完了commit。

このhandoff自体はStage61完了ではない。新セッションはP0-1のCOMMON C dispatcher captureから
同じworktree上で直ちに再開し、旧checkpointの解決済みP0やstateful 56 witnessの調査を
やり直さない。

## 最新再開チェックポイント（2026-09-01T13:58:02+09:00）

> **ここが現時点の唯一の再開位置である。** 直前の13:34 checkpoint以後、COMMON dispatcher
> captureのsource／validator修正は完了した。次セッションはP0-1を再実装せず、下記P0-2の
> 未完統合から始め、その後にMAP compositeへ進む。Stage61 task自体はまだIN_PROGRESSであり、
> production build、最新ROMによる実mGBA全件、task完了、commit、pushはいずれも行っていない。

### 1. 再開同一性

```text
Branch: codex/windows-battle-catalog
HEAD: 3b1941f36e99538c7f84a1fb233a68bac4957152
taskctl.py next:
  RESUME USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT [auxiliary]
git status --porcelain=v2 SHA-256:
  5ca435b42faf0b02b8dc6fc3f4f0af842a3202df2cde73ff88c075347cc80b56
```

作業treeの大量のtracked／untracked Stage61差分は意図した継続成果である。削除、checkout、
clean、旧生成物からの再生成をしない。サブエージェント3件は全て完了し、Stage61／mGBA／
unittestの実行中processは0である。

disk上のStage61 ROM／metadataは依然として旧候補で、最終検証へ使わない。

```text
c014d6718befc079eae5254c2df90d6cf653754f5e1afecc7dedaa8df1d8224c  build/stages/61_display_npc_event_audit.gba
966ef41fdbb84494af7de1457d48bd9d07a95d98cffae9a30853da4222b878cd  build/stages/61_display_npc_event_audit.json
```

### 2. P0-1 COMMON dispatcher capture: source／validator修正済み

変更済みファイル:

- `tools/mgba_stage61_display_npc_event_e2e.c`
  - `s61_event_common_dispatch_sample`はline 4182付近。
  - CPU dispatcher `0x0806911A`でR2=event bytecode PC、R1=opcode、R4=ScriptContextを
    実観測する。event bytecode PCをCPU breakpoint PCへ代入する旧方式は廃止した。
  - callstd系`0x08..0x0B`をoperand位置込みでdecodeし、standard indexとROM table rootを照合。
  - 同一ScriptContext1で`physical OBJECT root -> exact caller opcode -> declared COMMON root`
    の順序、caller→COMMONの隣接dispatcher ordinal、`LAST_TALKED_OBJECT == effective local_id`
    を要求する。
  - `consumer_hits`はexact caller opcode hitだけで、physical root hitを加算しない。
- `scripts/run_stage61_mgba_validation.py`
  - `_validate_event_common_dispatch_evidence`はline 13705付近。
  - COMMON projectionの`local_id=0`固定を廃止し、effective OBJECTの実local ID／歩行／stanceを
    TSVへ渡す。
  - `common_dispatch` raw evidenceをexact schemaで検証する。
- `tests/test_stage61_mgba_validation.py`
  - `test_common_dispatcher_edge_is_exact_and_fail_closed`はline 7855付近。
  - COMMON2／9の同一physical root・別callsite、caller欠落、非隣接、opcode／index、ordinal、
    context、LAST_TALKED不一致をnegative化した。
  - COMMON1／5／6相当のvisibility flagと実local IDも回帰化した。

親側再検証:

```text
python3 -m py_compile scripts/run_stage61_mgba_validation.py tests/test_stage61_mgba_validation.py
# PASS

cc -std=c11 -O2 -Wall -Wextra -Werror -pedantic \
  tools/mgba_stage61_display_npc_event_e2e.c \
  -o .local/stage61-common-dispatcher-compile-parent -lmgba
# PASS

python3 -m unittest -v \
  tests.test_stage61_mgba_validation.Stage61MgbaValidationTests.test_map_condition_precedence_guard_flattens_with_rom_evidence \
  tests.test_stage61_mgba_validation.Stage61MgbaValidationTests.test_common_effective_object_requires_direction_plus_a \
  tests.test_stage61_mgba_validation.Stage61MgbaValidationTests.test_common_dispatcher_edge_is_exact_and_fail_closed \
  tests.test_stage61_mgba_validation.Stage61MgbaValidationTests.test_event_physical_walk_preserves_non_up_multistep_and_common \
  tests.test_stage61_mgba_validation.Stage61MgbaValidationTests.test_structural_nontrigger_evidence_binds_null_and_dormant_common7
# Ran 5 tests, OK
```

P0-1はsource／static validatorとしては再実装不要。ただし新production ROM生成後の全COMMON
physical mGBA proofは未実行であり、完了扱いにはしない。

### 3. P0-2 required postconditions: converter骨格のみ入り、統合未完

`tools/stage61_interaction_oracle.py`だけに途中実装がある。

- `_RUNNER_REQUIRED_POSTCONDITION_KEYS`: line 6949付近。
- `_runner_required_postconditions`: line 7305付近。
- `_runtime_required_postconditions`: line 24329付近で新converterへ委譲。
- ordinary／hidden runtimeは旧raw relation wrapperから13-key changed-only converterへ切替済み。
- flag、engine flag、VAR、Bag item、trainer、object、warp、battle、money、coins、明示raw saveを
  source effectからfoldし、実測afterから期待値を学習しない骨格を追加した。
- battle開始snapshotと`FINAL_FIELD_RETURN`を分け、hidden already-collectedは13-key空契約へした。
- object runtime afterとtemplate FNV-1a hashを同一local ID rowへ併存できる内部表現を追加した。
- raw `_effect_contract`自体は監査証跡として保持している。

ただし、以下は未完であり、このままproduction buildを走らせない。

1. `build_case_oracle` line 7728以後のOBJECT経路は、line 7900台で旧5-key／旧baseline型
   `required_postconditions`を作る。各sequenceの実stateを新converterへ通し、case直下とsequence内を
   deepcopy同値にし、`control_requirements`とallowed effect family／effectを閉じる。
2. PC item effectは現在Bagへ混入しないため`continue`しているだけで、PC inventoryのexact
   source-only projectionがない。空へ丸めず`RUNNER_POSTCONDITION_PREIMAGE_REQUIRED`でfailするか、
   storage/persistent専用projectionを実装する。
3. `tools/stage61_catalog_state_matrix.py`へ13-key inner schema validatorと余分key拒否を追加する。
4. runner `scripts/run_stage61_mgba_validation.py`:
   - line 4259付近: OBJECT rowを`local_id`＋`after`／`template_after_fnv1a64`の少なくとも一方、
     両方併存可としてnormalizeする。
   - line 11718付近: `_mapping_changed_fields(None, after)`が存在しない`active` fieldを作る問題を直し、
     実runtime object snapshot schemaでspawn/removeを比較する。
   - line 11747〜11875付近: catalog OBJECT gateでruntime＋template併存rowを各1回exact検証する。
   - line 11900／13167／13350付近: structured logical full-scanが説明するSaveBlock byteをraw
     `persistent`から除外し、同じbyteの二重exact要求をなくす。明示raw-save effectだけを
     persistentへ残す。
   - battle finalは`battle:null`＋trainer defeatedをfield復帰後に検証し、battle-start snapshotは
     別captureとして検証する。
5. no-effect、last-write-wins、Bag add/remove、PC item非混入、money/coin saturation、hidden item
   success/full/already、OBJECT runtime＋template、battle start/final、unsupported relationのfocused
   unitを追加する。現在この新converter専用testは0件。

compileはPASSしたが、full interaction oracle suiteは次でFAILした。

```text
python3 -m unittest -q tests.test_stage61_interaction_oracle
# Ran 37 tests in 61.203s, FAILED (errors=1)
# setUpClassで既存generated semantic_reportに
# stage61_namespace_policy.engine_system_flagがなく
# ENGINE_SYSTEM_FLAG_IDENTITY_CONTRACT_REQUIRED
```

これは新converterの合否証明ではない。旧generated reportが現sourceより古いことを示すため、
focused converter testを先に追加し、P0-2／P0-3統合後の一度だけのproduction buildでreportを
再生成してfull suiteを再走する。

### 4. P0-3 MAP composite: ROM topology decoder完成、oracle／C統合は未着手

新規ファイル:

- `tools/stage61_map_lifecycle.py`
- `tests/test_stage61_map_lifecycle.py`

decoderは生成済みowner projectionを実行順の正本にせず、ROMの`gMapGroups`からMapHeader、
MapScripts outer 5-byte row、conditional 8-byte row、root-field／root PC／record raw hashを再復号する。
duplicate tag、不正tag、未終端、ROM範囲外はfail-closed。0x4000..0x400Fのdestination TEMP clear、
conditional ROM順first-match、次のphase列を純関数として固定した。

```text
STOCK_WARP / ENGINE_TELEPORT:
  DESTINATION_TEMP_CLEAR
  -> tag3 INITIAL_TRANSITION
  -> tag1 INITIAL_LOAD
  -> tag5 INITIAL_RESUME
  -> tag4 INITIAL_WARP_INTO
  -> tag2 PRE_FIELD_INPUT_ON_FRAME
  -> return tag5 FIELD_RETURN_RESUME
  -> return tag7 FIELD_RETURN_RETURN_TO_FIELD

CONNECTION:
  同じだがtag4なし
```

実ROM回帰:

- 全678 physical mapをdecode、scriptあり189 map。
- outer tag count: tag1=91、tag2=66、tag3=120、tag4=39、tag5=44、tag7=2。
- conditional row count: tag2=210、tag4=160（計370）。
- map `001/000`: tag3 `0x0887E7A2` -> tag1 `0x086A5B10` ->
  tag4 `0x08861650` -> tag2 `0x08861680`。
- map `002/010`: PRE_TRANSITIONの`4000=1,400D=0x11`はTEMP clear後row0
  `0x0816E65F`。TEMP clear後のPRE_FIELD_INPUTで再設定した場合だけrow1 `0x0816E63A`。
- field returnはtag5 `0x0816E5C5` -> tag7 `0x0816E5F9`を別phaseとして保持。

```text
python3 -m unittest -v tests.test_stage61_map_lifecycle
# Ran 5 tests in 9.768s, OK
```

次に実装するMAP compositeの正確な場所:

1. `_execute` line 5510付近を`_execute_from_states`へ分離し、非MAPは既存initial stateを渡すだけにする。
2. sibling開始helperでvars／flags／effects／printers／decisions／traceを保持し、pc／stack／comparison／
   loaded words／terminal等root-local stateだけを初期化する。lock残存はfail。
3. TEMP varsだけでなくengineがclearするtemp flags `0x0000..0x001F`と5 system flagsも、script effectと
   区別したengine transformで扱う。
4. `build_runtime_control_expansion_contract` line 26049以後でMAP ownerを通常root loopから外し、
   map単位の`_build_map_lifecycle_runtime_cases`へ渡す。1 caseは`covered_owner_ids`を持つ。
5. tag2はfixed 600 framesでなくfield-input boundaryごとにno-matchまで再試行し、state再訪を
   `MAP_ON_FRAME_LIVELOCK`でfailする。hard cap 256。
6. Cは単一target armから全attempt／dispatch ordered bufferへ変更する。resume前resetを廃止し、
   phase開始indexだけ保持する。direct `0x08069480`、conditional `0x08069498`、outer match
   `0x08069464/66`、condition selected `0x080694DE` (R6 root-field)、executor `0x0806948E`、
   tag2 `0x08069548`、tag4 `0x08069568`を新ROM preimage付きで捕捉する。
7. runnerのMAP 628／590／38 hardcodeを撤去し、inventory owner数とcomposite case数を別々に検証する。

read-only詳細監査では現ROM最大outer row数5、最大conditional row数8、duplicate outer tag 0を確認した。
推奨ordered buffer上限は256で、overflowはtruncateせず即FAIL。

### 5. このcheckpointで通した最終短時間gate

```text
python3 -m py_compile \
  tools/stage61_interaction_oracle.py \
  tools/stage61_catalog_state_matrix.py \
  scripts/run_stage61_mgba_validation.py \
  tests/test_stage61_interaction_oracle.py \
  tests/test_stage61_catalog_state_matrix.py \
  tests/test_stage61_mgba_validation.py \
  tools/stage61_map_lifecycle.py \
  tests/test_stage61_map_lifecycle.py
# PASS

python3 scripts/validate_task_graph.py
# OK
python3 scripts/guard_private_files.py
# OK
git diff --check
# PASS
python3 scripts/taskctl.py next
# RESUME USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT [auxiliary]
```

このcheckpoint差分では新しいmGBA実走をしていない。直前checkpointの旧ROM上56 physical witnessは
保持するが、最終ROM gateへ代用しない。

### 6. core file SHA-256

```text
dadfe1595ba5e5c6aad36e1f8d8a2c0e97b4ca37df68523caf6c0b6996a278ad  tools/stage61_interaction_oracle.py
a680a456b125c6c56b9537241bcdfa3be135ce080f539c80d6e3132a8c77b383  scripts/run_stage61_mgba_validation.py
468afa34aa31d46710f9f84d6682acc7ff4f43ddca9973b01ac9b0afc5b46d9a  tests/test_stage61_mgba_validation.py
0944bc4d9d8edfa95953800c200cd524704546f2b47e0800ddf2bc0701ca7541  tools/mgba_stage61_display_npc_event_e2e.c
6285c26df81774f263bf44dc346f0668122240379c235940dd58e204ec781516  tools/stage61_map_lifecycle.py
5f0de0de452e224008e14b01d8dc6014f45fcc665db5f1794afb27f7c250767e  tests/test_stage61_map_lifecycle.py
f385efa4987d8de19bd41128bb941da9d8e11574c8bc6fc4a31ce4ff261afb62  .local/stage61-common-dispatcher-compile-parent
```

handoff／run log追記後は`git status` hashが変わるので、再開時はcore file hashを主確認にする。

### 7. 新セッションの最初の実行順（やり直し防止）

```bash
cd "$(git rev-parse --show-toplevel)"
python3 scripts/taskctl.py next
sha256sum \
  tools/stage61_interaction_oracle.py \
  scripts/run_stage61_mgba_validation.py \
  tests/test_stage61_mgba_validation.py \
  tools/mgba_stage61_display_npc_event_e2e.c \
  tools/stage61_map_lifecycle.py \
  tests/test_stage61_map_lifecycle.py
python3 -m unittest -q tests.test_stage61_map_lifecycle
```

その後は次の順序だけを進める。

1. P0-2 converterのfocused testを追加し、OBJECT／catalog／runner／persistent／battle splitを完成。
2. 新MAP decoderをoracleへ統合し、sibling state、TEMP clear、tag2反復、field returnを完成。
3. C ordered MAP dispatch bufferとPython独立exact validatorを完成。
4. COMMON focused実装を触り直さず、3境界の短時間suiteを通す。
5. ここで初めてproduction buildを1回走らせ、semantic reportを含む全artifactを新ROM hashへ再結合。
6. 新ROMでCOMMON、MAP、COW、SAVE_LINK、fresh Continue、stateful menuを先に実mGBAで走らせる。
7. 全678 map／全owner／全NPC branchを実warp／歩行／向き／A／選択／battle／field return、複数state、
   runs=2で実走し、untested／unresolved／unexpected effect／softlock／空文を全て0にする。
8. acceptance、`--require-mgba`、対象gate、task graph、private guard、diff check、logs／version、
   `taskctl.py done`、最終commit。pushしない。

このcheckpointはStage61完了ではない。ユーザーが求める「実際のplayer操作を伴うmGBA実機相当監査」は
最終ROM生成後に必ず残っている。新セッションはP0-2の未完箇所からそのまま再開する。

## 最新再開チェックポイント（2026-09-02T07:26:25+09:00）

> **ここが現時点の唯一の再開位置である。** 2026-09-01 13:58 checkpointから
> oracle／catalog／builder／runner／Cの統合が進んでいる。旧checkpointの
> 「OBJECT postcondition未完」「RFU未実装」を前提に調査・再実装しない。
> Stage61 task自体はIN_PROGRESSで、production build、修復後ROMの実mGBA full gate、
> task完了化、commit、pushは行っていない。

### 1. 再開同一性と保全状態

```text
Branch: codex/windows-battle-catalog
HEAD: 3b1941f36e99538c7f84a1fb233a68bac4957152
taskctl.py next:
  RESUME USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT [auxiliary]
handoff追記直前 git status --porcelain=v2 SHA-256:
  ce16ff2225b696c0e4b908b2296eef1ceaf48f897bdc41692cc567a437b2c7a0
```

大量のtracked／untracked Stage61差分は意図した継続成果である。`git clean`、
`git checkout --`、reset、旧生成物を正とする上書きを行わない。今回の3 laneは
全て区切り済みで、共有log／config／statusは親以外が編集していない。

disk上のStage61 ROM／metadataはCreateBoxMon／GetSpeciesName修復前の旧候補であり、
最終検証や配布に使わない。

```text
c014d6718befc079eae5254c2df90d6cf653754f5e1afecc7dedaa8df1d8224c  build/stages/61_display_npc_event_audit.gba
966ef41fdbb84494af7de1457d48bd9d07a95d98cffae9a30853da4222b878cd  build/stages/61_display_npc_event_audit.json
```

### 2. このcheckpointまでに完了し、やり直さないもの

#### 2.1 builderのCreateBoxMon／Species name修復

`scripts/build_stage61_display_npc_event_audit.py`に次を実装済み。

- `CreateBoxMon` friendship計算の`0x0803D384`:
  - 旧`48 01` = `lsls r0,r1,#5`
  - 新`42 01` = `lsls r2,r0,#5`
  - 修復後function SHA-256:
    `ae230ae8c8e1cb110e03fb81d5b0e8ca92ed82fe053edab77c457a427202f4a4`
- `GetSpeciesName` thunk `0x080406C4` -> implementation `0x09FDA145`の
  `0x09FDA160` `04 d0` -> `c0 46`でcanonical 11-byte rowのEOS後paddingまでcopy。
  修復後implementation SHA-256:
  `a7e69fa0df1111485ec170f38a4e53fbe8cf08a28d9a35eaef4bd2efee70e8cc`。
- Species name table `0x09FD2730`、1,621 x 11 bytes、SHA-256
  `2f0a184e6b566a3196a1d064c8c40c451de758f75e14b1a584a1891d14e889da`。
- `tests/test_stage61_create_box_mon_friendship_repair.py`: 6 tests PASS。
- 修復ROMのGift generated mon 100 bytes期待SHA-256:
  `9b5a170e0328ca717f571405484054a14a264aa2b1ecddd8ece20348e82ea2a6`。
  friendship=70、ball=4、PP=19、physical map section=92。

修復ロジックは完了しているが、disk上ROMへは未反映。一時診断overrideを
正式成果として復元せず、後述の統合後production buildで反映する。

#### 2.2 14-key postcondition／OBJECT／catalog

- `tools/stage61_interaction_oracle.py`:
  - `_RUNNER_REQUIRED_POSTCONDITION_KEYS`は14-key固定。
  - OBJECT runtime rowとtemplate FNV-1a64 rowの併存、余分／欠落拒否、raw persistentと
    structured fieldの二重要求分離は接続済み。focused postcondition 11件PASS。
  - FACE／TURN方向はsnapshot外でraw opcode evidenceにより監査する現仕様。
- `tools/stage61_catalog_state_matrix.py`:
  - Giftの4 executor representative／30 runner layoutを`dedicated_fixture_sweeps`で保持。
  - `DAYCARE_TRANSACTION_STATE`、`PARTY_MOVE_TRANSACTION_STATE`、
    `GIFT_STORAGE_TRANSACTION_STATE`、`FOSSIL_REVIVAL_STATE`、`PARTY_MINIGAME`、
    `RFU_SESSION`のexact external kind schemaを実装済み。
  - partyは`{count, raw_sha256, raw_byte_length=600}`、storageは
    `{raw_sha256, raw_byte_length=0x83D0}`のsource-only raw SHA ABI。旧FNV schemaを拒否。
  - focused 4 tests PASS。

旧checkpointの「OBJECT／catalog schema未完」は解決済みで、再実装しない。

#### 2.3 oracleの進捗

`tools/stage61_interaction_oracle.py`と対応testに次を接続済み。

- PC cyclic `_fork_pinned_pc_menu` line 7621付近:
  root `0x08194221`、232 paths、全flag seed、blocker 0、B／MENU_CANCEL再訪、
  one-cycle witness、real exit、negative。
- DayCare `DAYCARE_TRANSACTION_STATE` line 1081付近:
  root `0x08191780`、94 paths、blocker 0。
- Move `PARTY_MOVE_TRANSACTION_STATE` line 1117付近:
  既検証70／11／11 paths、Move関連23 tests PASS。
- Gift `GIFT_STORAGE_TRANSACTION_STATE` line 1195付近:
  opcode79 executor、4 representative／30 layout manifest、party 600 bytes／storage `0x83D0`
  bytes／Pokedex／RNG／CreateMon raw SHA契約を実装済み。
- Fossil `FOSSIL_REVIVAL_STATE` line 1349付近:
  13 prefix payload、state導入、不可能なstate2／which0除外。旧ROM一時override診断で
  root `0x09433696`は62 paths／blocker 0だったが、診断overrideは保存していない。
- aggregate cap `_runtime_execute_with_seed_discovery` line 36011付近:
  4,097到達時のpartial破棄blockerを実装。focused 2 tests PASS。
- RFU:
  20 scenario定義、source-correlated executor、required type、relation／materializerまで
  接続済み。実root focused 3 testsは505 paths／blocker 0、全20 materializationもPASS。

RFUは14-key persistent postconditionではなくtransient external evidence gateとする設計。
「RFU未実装」は誤りで、未完なのはrunnerの全20実mGBA sweepと
coverage／forge-negativeである。

#### 2.4 runner／Cへ入った範囲

- `scripts/run_stage61_mgba_validation.py`:
  - DayCare／Move strict external-control、TSV、binary fixture。
  - Gift 30-layout registry、`_normalize_gift_storage_dedicated_fixture_sweep` line 3373付近、
    TSV encoding line 10739付近、fixture writer line 10966付近。
  - RFU registry／TSV／compact projection／observation validator
    `_validate_rfu_session_observation` line 16904付近。runner focused 4件PASS。
- `tools/mgba_stage61_display_npc_event_e2e.c`:
  - Gift fixture apply／readback line 13839付近。
  - opcode79実行 `s61_execute_givemon_opcode` line 14672付近。
  - party／storage／Pokedex／RNG／generated-mon exact検証
    `s61_verify_gift_storage_transaction_postimage` line 15096付近。
  - Gift probe line 15920付近と30-layout C sweep line 16110付近。
  - RFU peripheralと`S61_CONTROL_RFU_SESSION`のattach contractは静的接続済み。
- Gift physical rootはmap `010/015`、local `002`、MapHeader `0x0831543C`、
  section 92、local3 `(4,2)`。hostからmap-header byteを直接書きする旧診断は破棄し、
  physical map load／readbackへ変更済み。

#### 2.5 独立helper／decoder

- `tools/stage61_map_lifecycle.py`／`tests/test_stage61_map_lifecycle.py`:
  ROM `gMapGroups`から全678 physical mapのMapScripts outer／conditional tableを独立復号。
  8 tests PASS。scriptあり189 map、conditional 370 row。
  これはdecoder完成であり、oracle／C composite lifecycleは未統合。
- `tools/stage61_facility_sessions.py`／`tests/test_stage61_facility_sessions.py`:
  Mirage 33／Factory 10／Codex 6のimmutable scenarioとFactory loss／prepare errorを固定。
  19 tests PASS。oracle／catalog／runner／Cとの統合は未実装。
- COMMON dispatcher source／validator修正は前checkpointで完了済み。
  修復後ROMでのphysical mGBA proofだけ残る。

### 3. 正確な未完統合

#### P0-A: party／storage raw SHA-256がrunner／Cを貫通していない

oracle／catalogはsource-only raw SHA-256 ABIに変更済みだが、runner／Cは旧FNV形式が残る。

- Python normalizer:
  `scripts/run_stage61_mgba_validation.py::_normalize_required_postconditions`
  line 5385付近、特にline 5603〜5635。
- runtime exact compare: 同file line 17795付近。
- C snapshot: `tools/mgba_stage61_display_npc_event_e2e.c` line 2553付近の
  `S61SideEffectSnapshot`。
- C output: `s61_print_side_effects` line 18131付近。

次の最初の修正は、実RAMのparty 600 bytesとstorage `0x83D0` bytesから
SHA-256を計算／出力し、Pythonでlowercase 64 hex、固定byte length、exact postimageを
比較する。DayCare／Move／Giftに共通で効く。旧`changed_slots`／FNV1a64 schemaは
互換層として残さずfail-closedにする。

#### P0-B: `FOSSIL_REVIVAL_STATE`がoracle／catalogからrunner／Cへ未貫通

- `scripts/run_stage61_mgba_validation.py` line 3023付近の`_CONTROL_EXTERNAL_KINDS`に
  `FOSSIL_REVIVAL_STATE`がない。
- required-value normalizer、TSV／binary fixture、C parser／apply／readback、exact observationを追加する。
- 区切り時runner focused 10件は7 PASS／2 FAIL／1 ERROR。3件の原因は全て
  `oracle_minus_runner=['FOSSIL_REVIVAL_STATE']`で、逆差分0。
- この不一致を解消するまで同じ10件を再実行しない。実装後に一度だけ再走する。

#### P0-C: Gift C sweepがproduction runnerに未登録

- Cの30-layout sweepは存在するが、Python `CASE_DOMAINS` line 141付近へのcase登録、
  manifest生成／環境変数接続／結果集計が未完。
- Gift専用Python negative testが未追加。
- 修復後ROMでphysical map `010/015`のactualとGame Corner最終値、全14 rootの
  path countを再固定する。

#### P0-D: MAP composite lifecycleはdecoderの次が未完

2026-09-01 13:58 checkpointのP0-3がそのまま残る。新decoderの調査をやり直さず、
次を統合する。

1. oracleでmap単位composite caseを作り、sibling root間でvars／flags／effects／traceを維持。
2. destination TEMP var／temp flag／system flag clearをengine transformとして分離。
3. tag2をfield-input boundaryごとにno-matchまで反復、再訪はlivelock、hard cap 256。
4. tag5／tag7 field-return、connectionのtag4省略を別phaseで保持。
5. Cの単一target armをordered dispatch bufferへ変更し、runnerで独立exact比較。

#### P1: facility／Ruin／RFU final coverage

- Mirage 33／Factory 10／Codex 6:
  helperは完成。独立facility external kind、EWRAM preimage、phase／status trace、
  terminal cleanup／reward相関をoracle／catalog／runner／Cへ接続する。
- Ruin roots `0x088668A0`／`0x088669B0`:
  prefix-correlated FLAG modelが未着手。
- RFU:
  20 scenarioの実mGBA sweep、保存される明示coverage assertion、
  materializer forge-negativeが未完。source modelや20 scenario定義はやり直さない。

### 4. 既知FAIL／SKIPの扱い

- `tests.test_stage61_interaction_oracle` full:
  旧generated semantic reportに
  `stage61_namespace_policy.engine_system_flag`がなく
  `ENGINE_SYSTEM_FLAG_IDENTITY_CONTRACT_REQUIRED`でERROR。現sourceの不具合として
  旧reportに合わせず、統合後production buildで再生成してから再走。
- `tests.test_stage61_catalog_state_matrix` full:
  61件中60 PASS／1 ERROR。旧generated interaction control ABIが新external kind集合を
  持たないことが原因。旧reportを手修正しない。
- runner focused 10:
  7 PASS／2 FAIL／1 ERROR。原因はP0-BのFossil未貫通のみ。
- production build／修復後ROM mGBA／`--require-mgba`: SKIP。

上記3系統のFAILを現在の旧生成物で繰り返し実行しない。P0-A〜Dの対象実装と
artifact再生成後に一度だけfull suiteを実行する。

### 5. このcheckpointの最終短時間gate

```text
Stage61 builder／oracle／cyclic／catalog／runner／facility／MAP／対応testの
python3 -m py_compile:
  PASS

python module import:
  scripts.run_stage61_mgba_validation
  tools.stage61_catalog_state_matrix
  tools.stage61_interaction_oracle
  PASS

cc -std=c11 -O2 -Wall -Wextra -Werror -pedantic \
  tools/mgba_stage61_display_npc_event_e2e.c \
  tools/mgba_stage61_rfu_peripheral.c \
  -o .local/stage61-session-boundary-compile -lmgba
  PASS

tests.test_stage61_create_box_mon_friendship_repair: 6 PASS
tests.test_stage61_map_lifecycle: 8 PASS
tests.test_stage61_facility_sessions: 19 PASS
合計33 tests: PASS

catalog 14-key／transaction／RFU／phase3 focused: 4 PASS

oracle lane:
  Stage61PartyMinigameRFUFocusedTests: 3 PASS、505 paths、blocker 0
  Stage61RuntimeAggregateCapFocusedTests: 2 PASS
  RFU全20 required-value materialization: PASS
```

### 6. core file SHA-256

```text
2f86659920a8e18f0079b5e834a489ea83a64710f53bcc7d6219a7f82d78fa80  scripts/build_stage61_display_npc_event_audit.py
b67155cff2adc40d70dd6851969ce5fe335ab2efb740bb847b1e571a5f590379  tools/stage61_catalog_state_matrix.py
160dc9cac3c1bf3e8f8255bc349b8805952dc7f661ed476262aae0bc287e57ef  tests/test_stage61_catalog_state_matrix.py
a1a923cb9dae49a7eb62d9e334ba80092a0c7d9f00f891d3c2b9a2c08a66e989  tests/test_stage61_create_box_mon_friendship_repair.py
613ae3a7cf4e5015a44647b3a1a9945b360056d78252101252ef54ac9b79e7cd  tools/stage61_interaction_oracle.py
e097cd84ffa41f990547c5a80a75bf227e6e8a3738fdbfc96f708366dc9f587a  tools/stage61_cyclic_decision_contracts.py
bfa1c1029262e4f2982337103493728b1c8662a1c1256383219a0a31515837fa  tests/test_stage61_interaction_oracle.py
52beffdde2914698dc603aec487a1b6684378c9fa0d9777124b12392d4e9bcad  tests/test_stage61_cyclic_decision_contracts.py
8c9f56d0bdeca122bca46da45a3d2a0cc5f9e7cfdad82300b361a176792ac221  scripts/run_stage61_mgba_validation.py
8073b5f0e6be185438df2374a76573d5d902a07ec246dac4cae4c25f871a1ec4  tools/mgba_stage61_display_npc_event_e2e.c
3786da9025cdaa91f48e71526e8f5e2e8b0a25ff1f8b911df95988657da668ee  tests/test_stage61_mgba_validation.py
51c70a876287d797d6ef43d518027a7de618eb478787c51a99c6db5484e44a62  tools/stage61_facility_sessions.py
a57adeba5ac568ea580cb9d1d2c113642d48cf4b1201c256e73fa8685ac810d6  tests/test_stage61_facility_sessions.py
9bdd34adbcd07060a91190f4bf49e15c59c5c6716f3c069e7ac2b21c71a74213  tools/stage61_map_lifecycle.py
b400e0389dff6068fedb039eebb284d0a6b87f77fa4e901fb4e4dd2d1ce92df6  tests/test_stage61_map_lifecycle.py
7d90d4a73c4f82a52486ec2f35ae699c2ce49c49cf091ae950b51f960bd803b5  .local/stage61-session-boundary-compile
```

### 7. 新セッションの最初のコマンド

検証済みsuiteや旧generated reportを再計算せず、同一性だけ確認する。

```bash
cd "$(git rev-parse --show-toplevel)"
python3 scripts/taskctl.py next
sha256sum \
  tools/stage61_interaction_oracle.py \
  tools/stage61_catalog_state_matrix.py \
  scripts/run_stage61_mgba_validation.py \
  tools/mgba_stage61_display_npc_event_e2e.c \
  tools/stage61_facility_sessions.py \
  tools/stage61_map_lifecycle.py
```

その後は次の順序でそのまま続行する。

1. P0-A: Python normalizer -> C raw SHA output -> runtime exact compare -> focused negative test。
2. P0-B: Fossil kindをrunner／TSV／binary／Cへ貫通し、既知の10 focusedを再走。
3. P0-C: Gift 30-layout sweepを`CASE_DOMAINS`／manifest／result aggregationへ登録。
4. P0-D: 既存MAP decoderからoracle composite／C ordered bufferへ統合。
5. facility／Ruin／RFU final coverageを接続。
6. source／focused／strict C compileを通し、ここで初めて
   `python3 scripts/build_stage61_display_npc_event_audit.py build`を1回実行。
7. 再生成artifactでfull oracle／catalog／runner suite、修復後ROMのGift／Fossil／RFU／
   facility／COMMON／MAP／COW／SAVE_LINK／fresh Continueをfocused mGBA。
8. 最後に全owner／全NPC branch、runs=2、`--require-mgba`、acceptance／log／version／
   `taskctl.py done`／完了commit。pushしない。

### 8. 並列化する場合の所有境界

- parent: builder、production build、統合検証、shared design／log／status／commit。
- runner lane: `scripts/run_stage61_mgba_validation.py`、
  `tools/mgba_stage61_display_npc_event_e2e.c`、`tests/test_stage61_mgba_validation.py`。
- oracle lane: `tools/stage61_interaction_oracle.py`、`tools/stage61_cyclic_decision_contracts.py`、
  対応2 test。
- facility／MAP helperは現時点でimmutable参照とし、別laneが同時編集しない。

`design/run_log.md`、`design/version_log.md`、`design/tasks_next.md`、`package.json`、
shared config、commitはparentだけが扱う。

このcheckpointは完了報告ではない。次セッションはP0-Aのparty／storage raw SHA貫通の
最初の未実装行から開始し、上記の完了済み調査／実装／長時間testをやり直さない。

## 最新再開チェックポイント（2026-09-02T22:31:48+09:00）

> **この節が現在唯一の再開位置である。** ユーザー指示で今回の中間出口を
> 「重大なゲーム進行不具合を検出しないStage61候補ROM」へ変更した。
> 元の全件監査taskは`IN_PROGRESS`のまま、strict期待値／oracleは維持し、
> 全件動的監査を完了したとは扱わない。候補とcritical証跡は生成済みである。

### 1. ユーザー指定scopeと状態

- 既存strict buildを途中停止せず最後まで回収した。
- strict build、oracle、既存期待値は削除・緩和・結果追認していない。
- `scripts/build_stage61_display_npc_event_audit.py`の既定`build`／`check`はstrictのまま。
  候補専用の`critical-release`／`critical-release-check`を別artifact名で実装した。
- monolithic production buildはstrict失敗回収の1回だけで、原因探索には再実行していない。
- 全678 map×全owner×全branch×runs=2、unused state完全列挙、全owner exact trace ordinal、
  complete coverage 0 omissionは後続`DEFERRED_AUDIT`。
- task状態は`design/tasks_next.md`の`[>]`を維持。`taskctl.py done`、production完成扱い、
  push、iPad配置は行っていない。

### 2. 回収したstrict buildの停止点

strict buildは約14分後、次の非ゲーム進行oracle relationでexit 1となった。

```text
RUNTIME_CONTROL_MATERIALIZATION_UNRESOLVED:0x0936B5A3
instruction: 0x08E0338E
ABI: SPECIAL:0039:0x0810D825
kind: REMATCH_STATE
owner: LOCAL_OBJECT:3
candidate_values: [false, true]
required_value: false
relation: SAVEBLOCK1_TRAINER_REMATCH_BYTE_NONZERO
SaveBlock1 offset: 1597
```

原因はSPECIAL57のsource-exact rematch byte evidenceに`trainerbattle_type`がなく、
汎用relation normalizerの必須fieldと未接続なこと。ROMのcrash、softlock、save破損、
進行不能ではない。`reports/generated/stage61_critical_release_deferred_audit.json`へ
`PLAY_NONCRITICAL_ORACLE_RELATION`として保存した。strict buildを同じ状態で再実行しない。

### 3. Stage61 critical candidate identity

```text
ROM:
  build/stages/61_critical_release_candidate.gba
  33,554,432 bytes
  SHA-256 e736acd0828be5ccb583b85b4a07c940f08a7f880026c8e14bd4e520b0433669
metadata:
  build/stages/61_critical_release_candidate.json
  SHA-256 569a216adc3828c25bc3f1f4d79d7fbb3679a1819ec058ba5e041ba9a5a06ed1
payload:
  213,120 bytes
  SHA-256 ef473a22e5aa2b4d3fda85f97a2285b2ef48bf176c59e931cd38cc570b0bf40b
Stage60 incremental BPS:
  build/patches/stage60-to-stage61-critical-release-candidate.bps
  SHA-256 cb8e19bc66635991ec96736bf76a7944420141a0df99ff3fa5f07a9ac8aaf3bd
clean direct BPS:
  build/patches/firered-jpn-rev0-to-stage61-critical-release-candidate.bps
  SHA-256 435454cd411a42abd7e18a5e142fe9e99c63075aab2f923ead49238acc523c89
```

`critical-release`生成と`critical-release-check`はともにPASS済み。さらに最終集約器が
Stage60+BPSとclean ROM+BPSを独立適用し、両方が上記ROM byte列へ一致することを再確認した。
Stage60との差分は6,202 contiguous span、220,250 changed bytesで、builder報告spanと完全一致、
宣言patch interval外は0。構造gateは次をPASSした。

- physical map catalog 678面。
- script object／24-byte ObjectEventTemplate exact 3,108体。
- structural event owner inventory 6,417件。
- final placement、namespace、map-section consumer、BPS両経路、32 MiB size。

### 4. critical mGBA結果

全critical実走は同一ROM／metadata、同じC runner source
`30c48a4ea935102e42a5e5d81ad600c800d4c11026a91847c75e14d3a166d0a0`
へ固定し、各対象を独立2 processで実行した。

#### 4.1 主要進行・移動・save

`reports/generated/stage61_critical_release_runtime.json`、SHA-256
`dca9f368de1541602813d633ed8780674da7f967e2ca6ba2493631e83cac5016`。
5 case×2 runs、全caseのnormalized result hash一致、failed／untested／warnings 0。

- `critical_fixed_encounter_save`:
  - title生成saveからfresh Continue 3回。
  - D・HだんNPCへ実歩行＋向き＋A、可視会話から笛Item 350とflag `0x119E`を取得。
  - Route12へstock warp/save後にfresh Continueし、移設後の実objectへ歩行。
  - No branchはobject／stateを保持、Yes branchはcanonical Species 491固定戦を開始。
  - 通常Fight入力で戦闘を終了し、hidden flag `0x149E`、object非表示、field入力復帰を確認。
  - 通常START menuから2世代save。canonical 131,072-byte saveはfresh Continue前後で
    FNV-1a64 `8644216A4C430569`完全一致し、笛／hidden stateも保持。
- `snorlax_missing_flute`: 未取得時の有限会話、戦闘なし、object／flag保持。
- `fuji_before_after`: 笛取得前後の異なる可視会話、重複Itemなし、field復帰。
- `fly_normal_menu`: 通常START→Party→Fly→Town Map入力で`96/23`から`96/4 (6,6)`へ遷移し、
  着地後START/Bまで復帰。
- `connection_transition_lifecycle`: stock west connectionを実LEFT境界入力で`3/19`から
  `3/0 (34,15)`へ遷移。direct／START-B resumeの両variantでfield復帰。
- 全PPMはregistryと実file集合、115,215-byte P6、RGB FNV-1a64を照合した。

#### 4.2 Gift／party／PC storage

`reports/generated/stage61_critical_release_gift_party_storage.json`、SHA-256
`eac29181379359c77a23142fa0ebd3e25076c60c3121527f78cd65329b74f1ff`。

- `giveegg_result_contract` 6経路×2 process完全一致。
- party空き成功、current box／後続box／wrap各PC格納、party+全PC満杯を網羅。
- party 600 bytes、storage `0x83D0` bytes、target／non-target raw byte、current box、
  plaintext BoxMon、API readback、RNG、field復帰をPASS。
- 旧generated fixture類は読み込まずembedded fixed fixtureだけを使用し、strict全件監査の
  未完artifactを候補合否へ混入させていない。

#### 4.3 Four Island／Route5 DayCare

`reports/generated/stage61_critical_release_daycare.json`、SHA-256
`bda8c63b22f3be0511d1346184d7613263d9bf36f91489d6ced36f11a5b982a5`。

- Four IslandとRoute5を各2 process完全一致。
- script context経由deposit、party compaction、費用100、所持金500→400、withdraw、
  party復元、daycare storage clearをPASS。
- PC storageとmodern egg queueはbyte不変、field入力復帰、failed／untested／warnings 0。

### 5. 集約判定

正本は`reports/generated/stage61_critical_release_validation.json`、SHA-256
`fb6f4f41df9a36d058f7398eeb3ab43ee196edd83f37b6b9ee0a7ffcead3c84b`。

```text
status: PASS
status_scope: CRITICAL_RELEASE_PLAYABILITY_GATE
candidate_decision: PLAYTEST_CANDIDATE_READY
strict_audit_status: DEFERRED_AUDIT
original_audit_task_status: IN_PROGRESS
critical_failure_counts:
  crash: 0
  softlock: 0
  save_corruption: 0
  progression_blockage: 0
```

このPASSは指定されたcritical scopeだけに対する判定で、元taskの全件合格ではない。

### 6. strict側で観測し、期待値へ合わせず延期したもの

集約reportへ9件を`DEFERRED_AUDIT`として固定した。

1. rematch relation materialization未接続。
2. Vermilion strict authored fixed path witnessのblocked。
3. League tag5 exact trace ordinal未完。
4. Seafoam Route20 tag3 owner PC witness未完。
5. 注入flash failure後のstrict START retry未完。通常saveはcriticalでPASS。
6. 旧persistence snapshotがlibmGBA RTC footer付き131,088-byte `.srm`を拒否。
   criticalはcanonical 131,072-byte rawを直接照合済み。
7. `framebuffer_artifacts`追加を旧strict exact capture keysetが拒否。
   C自己検査とcritical PPM validatorはPASS。
8. strict warp preview consumer exact contract未完。Fly／connectionはcriticalでPASS。
9. Snorlax Runのexact `B_OUTCOME_RAN` witness未完。通常Fight完了、field復帰、保存再開はPASS。

これらを削除、allowlist化、期待値変更で合格させていない。

### 7. 実装・対象検証

追加した専用経路:

- `scripts/build_stage61_display_npc_event_audit.py`の`CRITICAL_RELEASE` profile。
- `scripts/run_stage61_critical_runtime.py`。
- `scripts/run_stage61_critical_daycare.py`。
- `scripts/run_stage61_critical_release_validation.py`。
- `tools/mgba_stage61_display_npc_event_e2e.c`の
  `critical_fixed_encounter_save`／`critical_daycare_transaction`。
- `tests/test_stage61_critical_release.py`。

実行済みgate:

```text
python3 -m unittest tests.test_stage61_critical_release
  6 tests PASS

event lifecycle / progression lifecycle / save UI COW / main mGBA runnerの
strict compile-only contract 4 tests
  4 tests PASS

critical runtime 5 cases x 2 independent processes
  PASS

Gift 6 paths x 2 independent processes
  PASS

DayCare 2 families x 2 independent processes
  PASS

python3 scripts/run_stage61_critical_release_validation.py
  PASS / PLAYTEST_CANDIDATE_READY

python3 -m py_compile（critical 3 scripts）
git diff --check
  PASS
```

ネットワーク未使用。固定ローカルROM、固定source、ローカルlibmGBAだけを使用した。

### 8. 次回の再開手順

候補をプレイ確認する場合は上記SHA-256の
`build/stages/61_critical_release_candidate.gba`だけを使う。iPad配置は未実施であり、
明示依頼なしに配置しない。候補inputが不変ならcritical build／runtimeを再生成しない。

元のstrict全件監査を再開する場合は、monolithic buildを探索ループに使わず次の順にする。

1. `RUNTIME_CONTROL_MATERIALIZATION_UNRESOLVED`のrematch source byte evidenceと
   `trainerbattle_type` relation normalizerをfocused fixtureで接続する。期待値は変更しない。
2. 上記9 `DEFERRED_AUDIT`を対象別runner／focused testで解消する。
3. 全対象修正後にstrict production buildを1回だけ実行する。
4. 全678 map×全owner×全branch×runs=2、unused states、exact ordinal、coverage 0 omissionを
   最終acceptanceとして走らせる。
5. すべて完了して初めて`taskctl.py done`、version log、task完了commitへ進む。

checkpoint時点でStage61／mGBA／builder関連の実行プロセスは残っていない。
今回のcommitはtask完了commitではなくWIP checkpointである。pushしない。
