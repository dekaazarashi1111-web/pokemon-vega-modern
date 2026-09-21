# Issue19 後継learnset表の完了境界とbinary接続再開点

正本は `content/modernization/pr16_learnset_successor_checkpoint.json`。工程 `learnset-successor-consumer-tables-v1` は表生成・差分・検証まで完了。実ROMへの接続や実機受入の完了ではない。

## 完了した実装

`tools/pr16_learnset_successor.py` は裁定済み公式1299件118524行、Vega181種9923行、空owner overlayだけを採用し、9consumerを分離する。全128447原本行の方法・条件・順序・ID・form・provenanceを保存し、Side Change159行/103種を別の明示除外台帳へ移す。採用128288行、新技・代替技0。原作TM/TR番号を現在候補のslotと混同せず、現在候補のmachine128/tutor64 slotをmove単位で逆引きする。候補slotがある33321行も互換bitを勝手に付与せず、archive接続が必要な28188行と区別する。

旧候補1671枠の全行を差分へ対応づけた。直接習得のmembership共通88863、旧表のみ11692、新表のみ3872、level列の変更346種。これは方法・条件の完全同値や自然供給の証明ではなく、削除/追加の実ROM適用を表す数でもない。条件付きegg、進化前持越し、姿変更、legacy preservationは直接技へ平坦化しない。

Vega非直接egg2394行は原作の孵化種表へ結合し、直接/shared付与0。公式孵化種に結びつく655行のうち、新しい孵化先direct eggのmembershipにない531行を明示。原本裁定を変更せず、後継adapterが扱うcross-source差分として残す。これは全習得経路で取得不能という判定ではない。

## 検証と再利用

Actions run `35627966003` / HEAD `1bd7e126dd4083581b43ade0776b72eddd38b9d1`。新39試験、seed17/53の独立2生成、check前後のbyte/mtime不変、原本128447行の独立全行監査、ローカル/Actions全13出力一致。生成物はartifact `10653200020`、digest `sha256:3710144d6698eb6d516adf10cb3f633cc71a2ff13a5c01dc30220fe8bc4e94b2` に保存。受入済み公式生成/182Wiki再採取/旧native再実行0。約310MiBの全表はtrackedへ複製せず、小型receipt・proof・差分台帳だけを本工程のevidenceへ保存する。

入力/生成器が不変なら、checkpointのartifactを取得してreceiptのSHA/sizeを照合するだけで再開する。期限切れ等で回復が必要なときだけ理由を記録し、固定公式artifactまたは原本ZIPと裁定済みVega入力から再生成する。CLIは `python3 -B tools/pr16_learnset_successor.py generate --official <受入済みoutputs> --output <repository>/.local/<新規出力>`。`check` は同じ引数で純読取。既存出力の上書き、symlink、.local外出力は禁止。

## 次の未完作業

`compact-review.json` の未選択191枠（canonical141/拡張50）に対するSpecies/Form binding、原作孵化先531差分の扱いを原本/所有者方針から明示する。非選択は「全削除」や「旧表fallback」を意味しない。キャタピー旧P03補正も公式1299へ暗黙混入させない。孵化差分を進化後direct/shared eggやowner overlayへ自動追加しない。

その明示bindingを使って既存binary consumerへ接続し、level-up/初期生成/思い出し/進化/持越し/TM・Tutor・archive/egg・shared egg/姿条件の影響範囲を確認する。後継ROMは別候補として生成、旧Wikiを保持した別snapshotと変更影響nativeだけを追加する。既存原本裁定・全nativeの反復は不要。

ROM/ARM/active play baseline変更0、Issue19/18全体未完、PR16 draft/open維持、merge/releaseなし。固定入口CHATGPT_RESUMEには変動進捗を重複記載せず、固定引継ぎMD/JSONを次工程へ同期した。
