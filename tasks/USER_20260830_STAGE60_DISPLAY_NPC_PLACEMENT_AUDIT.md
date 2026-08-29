# USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT — 表示名衝突とNPC自動配置の全map監査

## 状態

- Queue ID: `USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT`
- Status: TODO
- Baseline: Stage 60 `60_wild_species_root_repair`
- 本文書は2026-08-30時点の既知不具合メモである。ユーザー指示により、記録時点ではROM、生成器、配置manifestを修正しない。

## 観測1: カントーのマップ名表示がトーホク名になる

- 再現地点: カントーのディグダのあな（physical map `97/36`、`97/37`、`97/38`）。
- 観測表示: 「ちえのどうくつ」。
- 期待表示: 「ディグダのあな」。
- 既知の物理根拠:
  - FireRedの`MAPSEC_DIGLETTS_CAVE`は数値ID `131`を使う。
  - 現行Vega側の同じ数値ID `131`は「ちえのどうくつ」の表示文字列を指す。
  - カントーimport後のmap headerがFireRed側の`regionMapSectionId`を保持したため、異なる名前空間の同値IDが表示時に衝突している疑いが強い。
- 横断監査範囲:
  - Stage 60の全678 physical map headerについて、`regionMapSectionId`、実際の表示文字列、logical map key、期待する地方／地名を列挙する。
  - カントーimport対象253 mapだけでなく、トーホク既存mapと後続追加mapも含め、同値ID衝突、誤った地方名、空文字、意図しない別名共有を検出する。
  - popup、タウンマップ、そらをとぶ等が別の名前取得経路を持つ場合はconsumerごとに確認する。

## 観測2: NPC自動配置後に会話対象が到達不能になる

- 再現地点: ディグダのあなB1F、physical map `97/37`。
- 再現対象: Stage 35で追加されたTrainer Archive NPC 5人。
- 最終配置:
  - 中央 local ID 1: `(42,40)`
  - 上 local ID 2: `(42,39)`
  - 左 local ID 3: `(41,40)`
  - 右 local ID 4: `(43,40)`
  - 下 local ID 5: `(42,41)`
- 実害:
  - 中央NPCの上下左右が永続NPCで埋まり、通常移動では隣接できないため会話・対戦を開始できない。
  - 周囲4人の勝利後scriptはNPCを移動・消去せず、その場でpost-battle会話へ移るため中央への導線は開かない。
- 既知の原因候補:
  - `tools/trainer_final/kanto_events.py`のArchive配置は、各NPCを追加した時点の空きtileで個別監査する。
  - 中央NPCを最初に配置した時点では隣接4方向が空いていたが、その後4方向へ別NPCを配置した後の最終到達可能性を再監査していない。
- 横断監査範囲:
  - Stage 60の全physical mapについて、import後に自動追加・再配置された会話NPC、trainer、受付、報酬host、field objectを最終object集合で再評価する。
  - 各interaction ownerに、入口から到達可能で、永続objectに占有されない会話隣接tileが最低1つあることを検証する。
  - 「戦闘勝利後に空く」という仮定を置かず、hide／remove／movement命令を実際に持つobjectだけを条件付き解放として扱う。
  - object単体のwalkable判定だけでなく、複数object追加後の囲い込み、通路封鎖、warp／coord／bg eventとの競合、視線による任意戦強制を検出する。
  - Stage 35 Trainer Archive以外の後続自動配置器も同じ最終状態validatorへ接続する。

## 別タスクでの完了条件

- [ ] 表示名監査とNPC最終到達可能性監査を機械可読レポートとして生成する。
- [ ] ディグダのあなの2件を再現する回帰fixtureを追加する。
- [ ] 同根の不具合を全mapから列挙し、個別座標だけの場当たり修正ではなく名前空間／最終配置validatorの所有境界で修正する。
- [ ] 修正後もトーホクの正規「ちえのどうくつ」表示、既存warp、story、trainer、item、Raid、event ownerを保持する。
- [ ] exact ROMで中央を含む全対象NPCへ通常入力だけで到達・会話できることを確認する。
- [ ] Stage 60入力、差分BPS、clean直接BPS、declared span、allocator overlap、private guardを対象タスクの完了gateで検証する。

## 記録時点で意図的に行わないこと

- Stage 60 ROM、BPS、saveの更新。
- map header、表示文字列table、NPC座標、object flag、event scriptの変更。
- ディグダのあなだけを対象にした暫定的なすり抜け、消去、座標移動。

