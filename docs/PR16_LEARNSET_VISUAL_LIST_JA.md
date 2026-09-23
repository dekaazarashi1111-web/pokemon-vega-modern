# フラエッテ一覧1枚の限定修復

run35839963209 / source `ec80e1a3d59911cf3a25fe29092a1f4658398ba9` / `PASS_CAPTURE_PENDING_VISUAL_REVIEW`。

旧run35839299224はcapture/記録/push成功だが、フラエッテ一覧の実描画カーソルだけ前行の「めいそう」に残っていた。正常なミュウ一覧・summaryとフラエッテsummaryの3枚は保持する。旧画像も証拠として改作しない。

一覧開始からの待機ではなく、内部index10が連続90frame安定した後に撮影する。通常キー入力だけ、一覧撮影で停止し、summary/習得/Saveは実行しない。1process/1core、8追加境界試験。画像はartifact、trackedはtext/hashのみ。

正本 `content/modernization/pr16_learnset_visual_list_checkpoint.json`。目視とActions終端は後続の記録限定照合で確定。
