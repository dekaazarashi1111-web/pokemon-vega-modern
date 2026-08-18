# USER-TRAINER-V5-STAGE33-TOHOKU-BATCH03 — Gym1直後＋map 3/21次15物理命令を累積54戦へ接続する

- Lane: `content/engine/save/qa`
- Depends on: `USER-TRAINER-V5-STAGE32-TOHOKU-BATCH02`
- Queue ID: `USER-TRAINER-V5-STAGE33-TOHOKU-BATCH03`
- Baseline: post-v1.4.0 stage 33 / SHA-256 `7d3ad7f55d76afdad92cb18965d4bba33ccf0c854f4efdc1268974f9829472f0`
- Output: post-v1.4.0 stage 34 / SHA-256 `84395df49b5cee3fa83b501714828fa03db29bc24b1ed0f1a9cb292e1437946f`

## 目的

Trainer Redesign V5正本のTohoku前章フェーズから、Stage 33の39戦に物理的に連続する
Gym1直後のmap-script命令とmap `3/21`の次帯を追加する。map/objectの論理行数ではなく、
実ROM上のcommand-data pointer、kind、physical source trainer IDを正本とし、再戦sourceの
位置依存とwrapper aliasを分離して累積54戦へ拡張する。

## 採用範囲

- Gym1直後map-script: physical root reference 1 / command `0x0842A553`。reference 0は同一命令の論理aliasとして除外する。
- map `3/21`: reference 6, 7, 8, 9, 18, 19, 1080, 1081, 1088, 1089, 1093, 1094, 1095, 1096。
- reference 419/424は既存Batch02の物理root 420/425を指す論理aliasとして引き続き除外する。
- 追加15戦はすべてSINGLE、58 member。累積は50 SINGLE / 4 DOUBLE、171 member。
- 同一story phaseの連続物理帯だけを採用し、件数調整のため遠隔mapを混在させない。

## 安全方針

- グローバル`FlagGet/Set/Clear`はbyte-identicalに保ち、trainer専用6入口だけで29高IDを物理flagへ写像する。
- 最適化private party関数はhookせず、公開`BuildTrainerPartySetup`後に16-byte sidecarを適用する。
- CFRUの公開`ConfigureTrainerBattle`を先に実行し、exact command-data pointer＋kind＋source IDの一致時だけ29行tableで再束縛する。
- 再戦はsource-only表を廃止し、8-byte RematchMap V2のcommand-data address＋physical source IDで23行を一意に解決する。
- 共有source 119は`0x08196B5D`→1043、`0x08E034A9`→1045として位置別に束縛し、context外では曖昧な高IDへcollapseしない。
- rooted kind-4 ID 702→1342、Stage33 Batch02、kind-7物理ID 100の既存経路を保持する。
- 中央allocator、expected-byte、declared-span、incremental/cumulative BPS往復をfail-closed gateにする。

## 受入条件

- [x] 54 encounter、54一意party、171 memberをdeterministic source／serializerへ固定する。
- [x] 50 SINGLE／4 DOUBLEをkind契約へ結合し、DOUBLE kindへSINGLE partyを割り当てない。
- [x] 新15物理命令をcommand-data pointer＋kind＋source IDで全件再読取りし、論理aliasを除外する。
- [x] RematchMap V2 23行、exact rebind 29行、trainer defeat flag map 29行を一意に生成する。
- [x] 1,367行Trainer tableを維持し、既存24参照をfield offset 0/4/10込みで新tableへrepointする。
- [x] ability slot、nature、exact IV、6EVをlive partyへ反映する。
- [x] source 119の二つの再戦位置、物理trainer defeat flag、既存saveを維持する。
- [x] libmGBA独立2 processで新15命令、Batch03 sidecar、RematchMap V2、Batch02、rooted DOUBLE、勝敗、flag、save/loadをPASSする。
- [x] allocator overlap 0、禁止領域回避、declared span外変更0、BPS完全往復をPASSする。

## 完了入口

`make trainer-v5-tohoku-batch03`でdeterministic buildとexact-ROM 2 processを実行し、
`make trainer-v5-tohoku-batch03-check`で全生成物を再計算照合する。
