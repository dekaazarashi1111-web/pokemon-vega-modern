# USER-TRAINER-V5-STAGE31-INTEGRATION-FOUNDATION — Trainer V5先行25戦を実ROMへ接続する

- Lane: `content/engine/save/qa`
- Depends on: `USER-20260818-FACTORY-SHINY-MEMORIAL-RUNTIME`
- Queue ID: `USER-TRAINER-V5-STAGE31-INTEGRATION-FOUNDATION`
- Baseline: post-v1.4.0 stage 31 / SHA-256 `3a962877175d837ddb18d446182e6a63f5b72247567b93b0cc8982c74f1c8703`
- Output: post-v1.4.0 stage 32 / SHA-256 `bd426a1fc48d09ee2bdaede9c7d56df3f1a125646852b6b54302589cdb758694`

## 目的

Trainer Redesign V5から先行25 encounterを選び、Stage 31で確定したmap/object/script/
trainer IDへ個別に結合する。既存Trainer ABIで表現できないability、nature、exact IV、
6EVをlive partyへ適用し、SINGLE／DOUBLE、敗北flag、再戦、save/loadを実ROMで検証する。

## 安全方針

- グローバル`FlagGet/Set/Clear`はbyte-identicalに保ち、trainer専用入口だけで高IDを物理flagへ写像する。
- 最適化で引数ABIが変わるprivate `CreateNPCTrainerParty`はhookせず、公開`BuildTrainerPartySetup`をwrapする。
- 初回DOUBLEのrooted scriptは物理ID 702のまま保持し、正確なkind-4引数を消費した直後だけV5 ID 1342へ再束縛する。
- P4B2c禁止領域を避け、中央allocator、expected-byte、declared-span、BPS往復をfail-closed gateにする。

## 受入条件

- [x] 25 encounter、25一意party、71 memberをStage 31の物理bindingへ一意に結合する。
- [x] SINGLE 23戦／DOUBLE 2戦を別契約にし、DOUBLE kindへSINGLE partyを割り当てない。
- [x] 0x20 Trainer record、16-byte party member、16-byte sidecar V1を決定的に生成する。
- [x] ability slot、nature、exact IV、6EVを公開party生成入口後のlive `Pokemon`へ反映する。
- [x] Trainer tableを1,367行へ拡張し、既存24参照をfield offset込みでrepointする。
- [x] グローバルflag APIを変更せず、高IDの敗北状態を物理trainerの既存flagへ保存・再読込する。
- [x] 初回DOUBLE scriptの物理ID 702を保持し、runtimeだけでID 1342へ再束縛する。
- [x] 通常自然初戦、SINGLE sidecar、rooted kind-4 DOUBLE、4 controller、勝利、敗北、再戦、flag、save/loadをlibmGBA独立2 processでPASSする。
- [x] allocator overlap 0、禁止領域回避、declared span外変更0、incremental/cumulative BPS完全往復をPASSする。
- [x] build/check、ログ、タスク単位commit、単体で再開可能な完全snapshot ZIPを残す。

## 完了入口

`make trainer-v5-foundation`で決定的buildとexact-ROM 2 processを実行し、
`make trainer-v5-foundation-check`で全生成物を再計算照合する。
