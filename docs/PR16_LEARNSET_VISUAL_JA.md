# Issue19: 一覧・summary撮影の限定修復

候補6e88a021、run35839299224、source `29f1d8ca2b4f8468471265418a6e42430a660616`、`PASS_CAPTURE_PENDING_VISUAL_REVIEW`。

既受入23ケース全体は再実行しない。Mew raw40-page4とFloette420の2対象のみ、通常Bag入口から一覧/summaryを表示し、習得選択・Save前に停止する。1対象1core/観測guard1。既存技/PP・Save counter不変。

一覧state4/6を両方認識し、表示開始から90frame待機後に選択行を撮影。summaryはTask/状態2の連続90frame後に撮影する。palette/VRAMを直接書き換えない。画像はartifact内のみ、trackedはhash・240x160・色数・明度・実行source/stdout/stderr。

新規unit 10、native 2。pixel検査と目視受入を区別する。`visual_reviewed=false` の間は実画像4枚の目視とActions終端を後続で照合する。正本 `content/modernization/pr16_learnset_visual_checkpoint.json`。Issue19/releaseは未完。
