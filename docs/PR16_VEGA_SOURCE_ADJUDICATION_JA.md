# Issue19 Vega原本の裁定完了とruntime再開点

工程 `vega-source-adjudication-20260922`。正本は `content/modernization/pr16_vega_adjudication_checkpoint.json`。原本採取の旧checkpointは履歴のまま保持し、本書と固定引継ぎの次工程を優先する。

## 完了した実装

所有者決定 `VEGA_ORIGINAL_SOURCE_PRIORITY_20260921` により固定ROMを採用。リーテイルのLv32リーフブレード/Lv46こうごうせい、ディザソルのTutorギガスパーク/バグノイズ、ゴートンのLv18かみつく、計3群5行を別台帳へ記録。不採用Wiki3行とWiki側にないTutor2行の根拠、元順序/offset/版/hashを残す。raw `source_conflicts.json` は改変しない。

`content/modernization/pr16_vega_adjudication/adopted_vega_original_baseline.jsonl` は181種9923行の原作methodをそのまま保持したsource裁定済みprojectionであり、runtime入力への接続は未実施。

非直接egg92種2394行はすべて原作進化前の孵化種direct eggに存在し、`PRE_EVOLUTION_EGG` に分類。受取種へのdirect egg追加0、shared egg追加0、未解決0。元Wiki行・親注記7571件はそのまま保存。注記の分類は孵化種参照2336行/中間種参照57行/注記なし1行（カミギリー・よこどり）。注記欠落を補作しない。種名だけの注記も交配矢印へ変造しない。

原作進化表412枠/225非zero slot（target0の原文も保持）、egg147種3867行を不足範囲だけ追加採取。GetEggSpeciesのspecies1..411/5slot/first-match/最大5遡行、GetEggMovesのmarker/走査上限/50技容量に保存bytesを照合。独立走査と逆引き経路を全411種で比較した。GetEggMoves自身は孵化種へ変換しないため、進化後の種に直接eggを複製してはいけない。

## 証明の境界

これは原作表・固定consumer bytesの静的照合であり、親個体の自然入手、全交配手順、進化後の技保持のnative実行証明ではない。実機受入済みと表示しない。owner overlay追加0、ROM/ARM/new native変更0。公式1299件/118524経路、旧候補・Wiki・native原本を変更しない。Side Change非採用を維持し、効果/AI/新技は追加しない。

## 検証済み証拠と再実行防止

衝突5試験はrun35621880869（c8af78b7）の成功原本を再利用。欠落範囲だけの採取run35622433529（3da7acfe）、裁定13試験run35623180576（04b8ea96）、hash seed17/53の独立2生成、実CLI純読取byte/mtime不変、ローカルとActionsの全5出力一致を記録。記録器12境界試験とresume/最終index guardは今回の変更影響だけを検査する。完了artifactのID/digest/HEAD/job/全stepは証拠JSONへ保存。期限後もtrackedの全typed出力/consumer証拠/試験ログから再開できる。

入力変更のない受入済み5/13/43試験、182ページ採取、公式原本生成、nativeを反復しない。変更時の純読取入口は `python3 -B tools/pr16_vega_breeding.py check`。生成は明示 `generate` のみで、checkは修復しない。

## 次の未完作業

公式1299件と裁定済みVega181種と空owner overlayをruntime全consumerへ接続する後継生成器、既存候補との差分台帳、後継ROM/Wiki/影響nativeが次の区切り。raw方法別順序・条件・原本TM/TR番号とruntime slotの区別、原作孵化種direct eggを守る。旧CURRENT_PRESERVED/PRESERVE_V3/schemaV4等の履歴を新baseline受入根拠にしない。Side Change159経路/103種は証拠から削除せずactive除外を明示。除外だけで成立するなら補充不要、所有者が条件付きで許可したlevel-up仮技が必要な時だけstable key/IDを現行manifestで解決しcrosswalkを残す。Issue19全体/Issue18/merge/release/active baseline変更は未完・未承認のまま。
