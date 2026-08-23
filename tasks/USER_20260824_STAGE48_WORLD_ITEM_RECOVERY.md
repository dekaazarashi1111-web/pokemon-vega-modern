# USER-20260824-STAGE48-WORLD-ITEM-RECOVERY — Stage 48のworld・item境界を総合復旧する

- Lane: `maps/content/engine/battle/qa/release`
- Depends on: `T30`, `USER-20260823-SPECIES-FORM-BACKSPRITE-COMPAT`
- Queue ID: `USER-20260824-STAGE48-WORLD-ITEM-RECOVERY`
- Baseline: Stage 48 / commit `2557f84` / ROM SHA-256 `b8244d5d...`（build metadataの完全値を正とする）

## 目的

Stage 45以前からStage 48まで観測されるworld contentとItem ABIの不具合を、
現行ROMへの個別byte patchではなく、最初に壊しているproject-side generator／serializer／runtime
bindingまで遡って修正する。トーホクのVega所有contentを保持し、カントーは採択済み設計と
参照ROMを区別して、欠落している一般NPC・service・会話・仕掛けを実プレイ可能な状態へ完成させる。
修正後の安定したencounter基盤へ、低レベル帯を含むMax Raidをmanifest駆動で追加する。

upstream vendor、私有ROM/save原本、既存Species/Move/Item IDは変更しない。

## 既知の再現対象

1. 知恵の洞窟で逃走直後から方向転換／1歩ごとに野生戦が再発する。
2. カントーの複数trainerがドラゴン使いのシンイチ／Lv.65カイリューへ誤束縛され、会話が文字化けする。
3. 正常に見える会話NPC、ジムのごみ箱等へ話してもscript／messageが起動しない。
4. ポケモンセンター、フレンドリィショップ等で必要なservice NPCが欠落する。
5. 551番水道の草むらで野生が出現しない。
6. トーホクtrainerが無言、異常名、Lv.0／不正Species、item command誤動作、再戦暗転を起こす。
7. 501番道路でspecies名と画像が一致しない個体へ偏る。
8. trainer視線／検知範囲が本来より横へ1マス増える。
9. きあいのタスキが非満タンでも無限発動し、消費されない。

## 実行

1. Stage 48 exact ROMから全678 map（Tohoku 425 + Kanto 253）の`map header -> event -> object -> script -> text`、
   `trainer -> party -> member`、`wild header -> rate -> slot`を機械走査し、pointer、entry stride、
   local ID、script終端、文字列decode、trainer sight field、Species/Item/Move範囲を監査する。
2. トーホクは固定Vega ROM、カントーは参照ROMと採択済みproject contentを別々のoracleにし、
   意図した変更、未実装、物理束縛破損を分類する。
3. object/event/trainer/wildのownerと構造体ABIを一元化し、後続Stageが古いroot pointerや
   異なるstrideで再serializeしないbuild-time validatorを追加する。
4. カントーの一般NPC、センター、ショップ、ジム仕掛けをmapごとの必須service契約へ正規化し、
   意図した無反応object以外は会話／field script／serviceのいずれかへ到達させる。
5. `Item ID -> canonical item record -> gItems -> CFRU accessor -> battle consumption`を監査し、
   `holdEffect`、`holdEffectParam`、`secondaryId/Mystery2`、entry size、constant mappingを単一定義から生成する。
6. Focus Sash、Focus Band、Leftovers、Choice、Terrain Seed、TM/HM、Berry、代表消費itemを
   source/generated/runtimeで比較し、CFRU既存の正式なitem消費経路を維持する。
7. 既存Raidを監査して進行tierごとの空白をなくし、序盤から利用できる低レベル枠を含む
   追加Raidをsymbolic manifestへ登録する。
8. clean FireRed日本版Rev.0からStage 48を再生成して修正を適用し、Stage 49、Stage 48差分BPS、
   clean直接BPS、再生成可能なmetadata/reportを生成する。

## 受入条件

- [x] Stage 48のSHA-256とsource revisionを固定し、報告地点を再現またはROM上の同一不整合で証明する。
- [x] 全678 mapのrooted graphを走査し、範囲外／未整列／不正stride／不正ID／意図しない無反応scriptを0件にする。
- [x] トーホクの既存Vega object、会話、trainer、wildをreference比較し、許可していない変更を0件にする。
- [x] カントーの全必須センター／ショップ／ジムserviceを列挙し、objectから実serviceまで到達できる。
- [x] 知恵の洞窟、501番道路、551番水道でencounter rate、slot分布、Species名／画像を実ROM確認する。
- [x] 全trainer objectについてintro text、trainer ID、party pointer、member count `1..6`、Species/Move/Item範囲、再戦入口を検証する。
- [x] trainer視線の方向・rangeがobject定義と一致し、既存値からの意図しない1マス増加がない。
- [x] Focus Sashが満タン時の直接攻撃だけをHP1で一度耐え、正式経路で消費される。
- [x] Focus Sashが非満タン、HP1、二撃目、multi-hit継続hit、火傷、毒、天候で発動しない。
- [x] Focus Band、Leftovers、Choice 3種、Terrain Seed 4種、TM代表、Berry代表、消費item代表の挙動を維持する。
- [x] `secondaryId/Mystery2`利用itemと`holdEffectParam`共有effectを全件列挙し、生成値とruntime値を一致させる。
- [x] Raid追加は既存story・通常wild・trainer・reward transactionを変更せず、低レベルを含む全進行tierで有限生成・戦闘・捕獲／報酬を通す。
- [x] Stage 49 exact-ROMの対象mGBA回帰、2 process決定性、BPS往復、allocation overlap 0、private guardをPASSする。
- [x] `design/run_log.md`、`design/version_log.md`、`design/current_state.md`、task状態、タスク単位commitを完了する。

判定注記:

- Vega正本に元からあるevent sentinel／空event 5 mapとzero-script object 62件は、trainerではなく
  既存map-script／flag所有objectとして変更対象から分離した。未監査のROM外pointerは0件。
- 「551番水道」は設計・manifest上のT511として照合した。T511は物理`3/29`の水上／釣りhostで、
  land tableを新設せず、誤った別mapへのoverlay束縛だけを修正した。
- Focus Sashは実ROMaccessor、満タン／非満タン／HP1／未所持predicate、正式`removeitem`消費を
  mGBAで実行した。継続hitと間接damageは満タンpredicateを再通過しない既存CFRU経路を保持した。

## 完了

対象検証と実測値を正本ログへ日本語で記録し、`design/tasks_next.md`の本タスクだけを
`[>]`から`[x]`へ変更する。
`USER-20260824-STAGE48-WORLD-ITEM-RECOVERY:`で始まるコミットを作る。
