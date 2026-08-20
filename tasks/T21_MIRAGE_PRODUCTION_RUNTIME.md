# T21 — Connect Mirage modernization to production runtime

- Lane: `maps/content/engine/save/qa`
- Depends on: `T20`

## 目的

T20完了済みのStage 37を固定baselineとし、T02/T06/T08/T10/T15〜T17で設計・生成・
単体検証まで完了しているMirage Battleの4周ルールを、Vega既存のMirage mapと通常field入力へ
production接続する。設計表、host-side fixture、battle-local helperだけで終わらせず、持込party選択、
7戦×4周、round別gimmick、記録、仮想item、全退出経路、save/reloadをStage 38実ROMで完走させる。

このタスクは新しい施設仕様やbalanceを考えるタスクではない。明記されていないfield挙動は
Stage 37に残るVega既存Mirageをbehavior oracleとして保持し、下記の固定済み差分だけを結合する。

## 固定入力

### 現行baseline

- ROM-producing commit: `ba3cf63a102f44860917ba855ac383adcabfd106`
- ROM: `build/stages/37_event_design.gba`
- ROM SHA-256: `76d4f6a4005a815e6faf33f2ae24c18c2a7b4a1fe6f1f313e6f1837ecaf5cb7c`
- ROM size: 33,554,432 bytes
- metadata: `build/stages/37_event_design.json`
- Stage 37の76 event、63 placement、80 state、既存trainer 1,302戦、6,490 member、
  取得イベント201件、QOL 35機能・97 hookを回帰不変条件とする。

キュー追加後のcommitが進んでいても、Stage 37 ROMとmetadataのidentityが上記と一致する限り
同じbaselineとして扱う。入力identityが異なる場合は推測でrebaseせず、差分原因を先に確定する。

### Mirageの機械可読正本

- `manifests/facility_modes.csv` の `party_owner=MIRAGE` 4行。
- `manifests/facility_trainers.csv` の `TRAINER_POOL_KEY_MIRAGE_1..4` 4行。
- `manifests/facility_rentals.csv` の `RENTAL_POOL_KEY_SPECIAL`。これは対戦相手poolの正本であり、
  playerをFactory rentalへ置換する意味ではない。
- `manifests/facility_rewards.csv` の `trigger_kind=MIRAGE_VIRTUAL_ITEM` 5行。
- `manifests/trainer_ids.csv` の `FACILITY_TRAINER_KEY_MIRAGE_1..4`。numeric IDはStage 37で
  実tableと再照合し、symbolic keyを正とする。
- `content/trainer_balance_constraints.csv` の `TRAINER_CONSTRAINT_MIRAGE`。
- `config/t02_audit_policy.json` の `facilities.mirage`。
- `config/save_layout.csv` と `overlays/save_migration/**` の `VegaMirageState`。
- `overlays/cfru/**` の `VegaConfigureNextMirageItem` / `CfruMirageItemState` とbattle出口cleanup。

### 既存Vega Mirageの物理oracle

- map group/map: `31/1`、map section 143、respawn 14。
- T02で確認した旧root: map header `0x08315B74`、events `0x08885DB0`、object script
  `0x08895760`、cleanup scripts `0x08896610` / `0x08896630` / `0x08896640`。
- 旧flag `0x1212..0x1215`、旧var `0x407D..0x407E`、badge `0x0820..0x0827`は
  evidenceであり、Stage 38の新規ownerへraw値を盲目的に流用しない。

物理addressはStage 37 rooted graphからexpected byte付きで再解決する。既存の受付、party選択、
戦闘間回復、勝敗・辞退、map遷移、会話、BGM、respawnのうち下記で明示的に変更しない挙動は保持する。

## 固定仕様

### partyと進行

- Mirageは育成済み持込party施設であり、Factory rental施設ではない。
- 標準party UIで自分の手持ちから3体を選ぶ。タマゴ、瀕死だけで3体を構成できない場合、重複選択、
  cancelは開始前に拒否し、persistent stateを変更しない。
- battle ruleは `LEVEL_100_FIXED`。実partyの永続level/EXPを書き換えず、既存MirageのLv.100
  battle変換またはbattle copyを利用する。
- 1周7戦、全4周28戦を順番に進める。途中の周を飛ばさない。各戦の相手3体は対応する
  `TRAINER_POOL_KEY_MIRAGE_n` の6体から、固定済みfacility RNG/selection policyで生成する。
  Species、技、特性、道具、性格、EV/IVをT21で再balanceしない。
- Round 1は `VEGA_HALL_OF_FAME` 後、Round 2〜4は `KANTO_CERT_4` 後に進行可能。
  外部gateを満たしていても、同一challenge内の前roundを完了せず後roundへ飛ばさない。
- Round 1=`NONE`、Round 2=`MEGA`、Round 3=`Z`、Round 4=`ONE_OF_MEGA_Z_TERA`。
  Round 4は標準list/yes-no UIで1つ選び、その7戦中は固定する。Dynamaxは対象外。
- 1 battle・1 sideにつき許可gimmickは最大1回。通常trainer、Factory、Raidへ選択stateを漏らさない。

### Mirage stateと仮想item

- `OWNER_KEY_MIRAGE_STATE` のcurrent/best record、reward claim、item reward transactionだけを更新し、
  Factoryのparty snapshot、BP、streak、reward、unlock、transactionを一切更新しない。
- Mirageは数値通貨を持たない。`CURRENCY_KEY_MIRAGE` / `amount=-1..-5`をBP・コイン・
  新規残高へ変換せず、既存manifest上の仮想item tier metadataとして扱う。
- streak 7/14/21/28/35の5行をmanifestどおり評価し、`REPEATABLE` / `ONCE`、unlock、
  `CLAIM_KEY_MIRAGE_ONCE` / `CLAIM_KEY_MIRAGE_TOP`を保持する。`MIRAGE_VIRTUAL_ITEM`は
  battle-local policyであり、player bag、persistent held item、Factory inventoryへ持ち出さない。
- `VegaConfigureNextMirageItem`を実際のMirage trainer battle開始前に呼び、勝利、敗北、全滅、
  辞退、reset、switch、盗む・すりかえる・消費・なげつける相当を含む全battle出口でclearする。
- 一度限りclaimは成功したsave transactionの後だけ成立する。保存失敗、reset、途中終了で
  二重claim、先行claim、virtual item残留を起こさない。
- current/best recordはround/battle結果と同じtransaction境界で更新し、save/reload後も一致する。
  既存40-byte `VegaMirageState`を優先して使い、save ABI変更が必要なら旧Stage 37 saveの
  migration、checksum、reserved領域、rollbackを同時に証明する。

### 全退出経路

- 入場前badge 8 bitをexact snapshotし、完走、敗北、全滅、辞退、selection cancel、script cancel、
  warp、reset後cleanupの全経路で同じbit列へ復元する。旧scriptの「全badgeをset」は禁止する。
- Mirage-owned active/round/gimmick/virtual-item stateだけをidempotentにclearする。Vega story、HM、
  Kanto認定章、QOL、Factory、Raid、acquisition、T20 event stateへ書き込まない。
- battle-local level、form、gimmick、held itemの一時変更を退出時に除去する。HP/PP/status、戦闘間回復、
  save可否、敗北時respawnは既存Mirageのfield behaviorを維持し、binding reportへoracleとの差分0を記録する。

## 並行作業との所有境界

T21は次を所有する。

- Stage 37上のMirage map `31/1`の受付・challenge・cleanup root。
- Mirage専用production binding、runtime adapter、save transaction、smoke、Stage 38 build/rebuild。
- `facility_*`のMirage行を読むserializer。既存manifestをbalance目的で書き換えない。

T21は次を読取・変更しない。

- ChatGPT Proへ渡したReward Encounters V2、Move Distribution V4、Factory High Modes V2、
  Research Economy V1のZIP、返却物、作業領域。
- FactoryのTrial/Standard/Full/Master、BP/shop/reward、施設外報酬遭遇。
- level-up/egg/TM/tutor、NORMAL/RESEARCH経済、Raid reward、trainer再設計、T20 eventの仕様。

共有allocator、save schema、release文書へ変更が必要な場合もMirage専用の最小差分に限定し、
4本のPro成果が後から独立統合できる所有境界をreportへ残す。

## 実行

1. Stage 37 ROM/metadata、task graph、private input guardを事前検査する。
2. Stage 37のmap `31/1`をrooted walkし、受付、party選択、7戦loop、round遷移、報酬、全cleanup、
   badge操作、trainerbattle、save/respawn rootをbinding台帳へ記録する。
3. Mirage正本4 mode・4 trainer pool・5 virtual-item row・4 symbolic trainer IDを厳密にparseし、
   未解決key、重複owner、Factory混入をfail-closedにする。
4. 既存field scriptを薄いproduction dispatcherへrepointし、通常NPC/bg/coord入力から開始、再開、
   辞退できるようにする。debug menu、helper直呼びだけを入口にしない。
5. 持込3体、Lv.100 battle変換、7戦×4周、round gimmick、相手pool、record、仮想itemを
   既存CFRU/save ABIへ接続する。
6. badge exact restoreとMirage-owned idempotent cleanupを全exitへ集約する。
7. Stage 37へexpected-byte付きpatch/repointを適用し、Stage 38を生成する。declared span、ROM/RAM/save、
   map object、trainer table、CFRU/QOL/event hookの所有重複を0にする。
8. host focused test、exact-ROM mGBA quick/full独立2 process、clean rebuild、BPS往復をPASSさせる。

## 必須成果物

- `config/mirage_production_bindings.csv`
- `overlays/mirage_production/**`
- `scripts/build_mirage_production.py`
- `scripts/rebuild_mirage_production_from_clean.py`
- `tools/mgba_mirage_production_smoke.c`
- `tests/test_mirage_production.py`
- `reports/generated/mirage_production_{audit,coverage}.json`
- `build/stages/38_mirage_production.gba`（Git管理外）
- Stage 37→38 BPS、clean→Stage 38 BPS、mGBA quick/full、clean rebuild証跡（Git管理外）

既存builder/runtimeを再利用する方が安全な場合は、上記名の薄いadapterと同等の機械可読証跡を
用意してよい。空stub、host-only model、ROM未接続fixtureは不可。

## 受入条件

- [ ] Stage 37のsize/hash/metadata identityが固定値と一致し、入力ROM・clean ROM・saveを変更・追跡しない。
- [ ] Mirage 4 mode、4 trainer pool、5 virtual-item row、4 symbolic trainer IDを欠落・重複0でcompileする。
- [ ] map `31/1`の通常field入力から持込3体を選び、7戦×4周を順番に開始・完走できる。
- [ ] HOF前、HOF後、認定章3/4の境界でRound 1〜4の解禁が固定仕様どおりになり、round skipが0。
- [ ] 全28戦がLv.100 single 3v3、AI_FULL_SMARTで動き、Round 1/2/3/4がNONE/MEGA/Z/選択したMEGA・Z・TERAを使う。
- [ ] Round 4の選択は7戦固定、1 battle・1 side最大1 gimmick、Dynamax混入と通常戦へのstate漏出が0。
- [ ] 相手6体poolからの3体選択が固定facility policyで再現でき、T21による新規balance・違法構成が0。
- [ ] streak 7/14/21/28/35の仮想item tier、unlock、repeatability、claimがmanifestと一致し、
  player party/bag/save、Factory inventoryへvirtual itemが漏れない。
- [ ] current/best recordとonce claimが成功時だけatomicに保存され、save/reload、reset、保存失敗後に一致する。
- [ ] 入場前badge bit列が完走、敗北、全滅、辞退、cancel、warp、resetの全経路でexact restoreされ、
  全badge set、story/HM/認定章汚染、stale active stateが0。
- [ ] 盗む・交換・消費・form変化を含むbattle-local stateが全出口でclearされ、次の通常trainer、Factory、Raidで0から始まる。
- [ ] Factory BP/streak/reward/party snapshot、QOL、Raid、acquisition、T20 event、trainer 1,302戦・
  6,490 member、74 DOUBLE、201 Kanto trainerが回帰PASSする。
- [ ] ChatGPT Pro待ち4領域の入力・出力・所有fileを変更せず、後続統合を妨げるshared schema変更が0。
- [ ] Stage 38をclean FireRed日本版Rev.0から決定的に再構築でき、Stage 37差分BPSとclean直接BPSが完全往復する。
- [ ] changed byteがdeclared span内、allocator/RAM/save/map/trainer/hook overlap 0、mGBA quick/full独立2 processのresult identityが一致する。

## 禁止する完了判定

- manifest、fixture、host C test、既存T06 helperがあることだけでDONEにしない。
- 1戦または1周だけをつなぎ、4周28戦のproduction接続完了としない。
- Factory runtimeへMirage stateを相乗りさせない。BP、rental party、Factory rewardを流用しない。
- 旧Mirageのraw address、flag、var、badge cleanupをStage 37へexpected-byte監査なしでコピーしない。
- Pro待ち4領域を先回りして仮仕様で実装しない。

## 完了

1. task固有build/check、focused tests、通常field入力、全28戦境界、mGBA quick/full、clean rebuildをPASSする。
2. `design/run_log.md`と`design/version_log.md`へ証跡を追記する。
3. `python3 scripts/taskctl.py done T21 --summary "Mirage 4周をStage38の通常入口へproduction接続"`を実行する。
4. 意図した差分だけをstageし、task graph、private guard、`git diff --check`をPASSする。
5. `T21:`で始まるcommitを作る。pushしない。
