# USER-TRAINER-V5-STAGE32-TOHOKU-BATCH02 — Tohoku次14物理命令を累積39戦へ接続する

- Lane: `content/engine/save/qa`
- Depends on: `USER-TRAINER-V5-STAGE31-INTEGRATION-FOUNDATION`
- Queue ID: `USER-TRAINER-V5-STAGE32-TOHOKU-BATCH02`
- Baseline: post-v1.4.0 stage 32 / SHA-256 `bd426a1fc48d09ee2bdaede9c7d56df3f1a125646852b6b54302589cdb758694`
- Output: post-v1.4.0 stage 33 / SHA-256 `7d3ad7f55d76afdad92cb18965d4bba33ccf0c854f4efdc1268974f9829472f0`

## 目的

Trainer Redesign V5正本のTohoku前章フェーズから、Stage 32の25戦に物理的に連続する
trainerbattle命令を追加する。map/objectの論理行数ではなく、実ROM上の命令pointer、kind、
source trainer IDを正本とし、重複source IDとwrapper aliasを区別して累積39戦へ拡張する。

## 採用範囲

- map `3/21`: reference 4, 5, 10, 11, 14, 15, 20, 21, 43, 44
- map `3/22`: reference 41, 42
- map `22/1`: physical root reference 420, 425
- reference 419/424は420/425と同一物理命令を指す論理aliasのため除外する。
- 追加14戦は12 SINGLE / 2 DOUBLE、42 member。累積は35 SINGLE / 4 DOUBLE、113 member。

## 安全方針

- グローバル`FlagGet/Set/Clear`はbyte-identicalに保ち、trainer専用6入口だけで高IDを物理flagへ写像する。
- 最適化private party関数はhookせず、公開`BuildTrainerPartySetup`後に16-byte sidecarを適用する。
- CFRUの公開`ConfigureTrainerBattle`を先に実行し、その後でexact pointer＋kind＋source IDの一致時だけ高IDへ再束縛する。
- kind-3の非整列source IDはbyte合成で監査し、GBAのunaligned halfword rotateを値として採用しない。
- rooted kind-4 ID 702→1342回帰とkind-7物理ID 100の直接経路を保持する。
- 中央allocator、expected-byte、declared-span、incremental/cumulative BPS往復をfail-closed gateにする。

## 受入条件

- [x] 39 encounter、39一意party、113 memberをdeterministic source／serializerへ固定する。
- [x] 35 SINGLE／4 DOUBLEをkind契約へ結合し、DOUBLE kindへSINGLE partyを割り当てない。
- [x] source 119の別物理命令とkind-3 aliasを20行exact rebind tableで一意に解決する。
- [x] 1,367行Trainer tableを維持し、既存24参照をfield offset 0/4/10込みで新tableへrepointする。
- [x] ability slot、nature、exact IV、6EVをlive partyへ反映する。
- [x] 物理trainerのdefeat flag、再戦状態、既存saveを維持する。
- [x] libmGBA独立2 processで20 exact rebind、通常初戦、Batch02 sidecar、AI record、rooted DOUBLE、勝敗、再戦、flag、save/loadをPASSする。
- [x] allocator overlap 0、禁止領域回避、declared span外変更0、BPS完全往復をPASSする。

## 完了入口

`make trainer-v5-tohoku-batch02`でdeterministic buildとexact-ROM 2 processを実行し、
`make trainer-v5-tohoku-batch02-check`で全生成物を再計算照合する。
