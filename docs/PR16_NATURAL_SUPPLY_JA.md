# PR16 Issue19: 通常配布・原本初期技孵化

状態 `PASS_NATURAL_SUPPLY_SCOPED`。3ケースを限定受入。native原本のActions終端 `True`。

候補 `b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91` / 33554432 bytes。ROM・runtime・ARMは変更せず、未受入経路の検証実装を追加した。全owner/全form/Issue19/releaseは未完、active baseline不変。

## 受入範囲

| case | 原本初期技（順序） | 通常操作の受入 | 実測run |
| --- | --- | --- | --- |
| caterpie-initial-hatch / Species649 | 33, 81, 0, 0 | 育て屋預け・歩行生成・受取・Save/fresh Continue・歩行孵化・Save/fresh Continue | 36102544792 |
| leepun-initial-hatch / Species1 | 10, 39, 0, 0 | 同上。Vega採用原本から期待値を解決 | 36102544792 |
| floette-eternal-npc-initial / Species1029 Lv50 | 204, 235, 382, 738（PP20,5,10,5） | map96/5 local15の実NPC配布・原本技/PP/HP・元party不変・通常Save/fresh Continue・再配布拒否 | 36104762658 |

孵化の親2体・開始地点、配布の開始party/場所/Ring/未受領flagはfixture。親の通常捕獲、Ringの通常取得、ストーリー到達はこの受入に含めない。guarded操作区間では7host書込APIを拒否し、通常キー入力だけを与える。配布JSONのguarded_phases=3は配布・手動Save・fresh-core操作の3カテゴリを表し、Continueと再受取の間にもgetter用解除/再guardがある（a_guardは4回）。観測区間間のgetter用CPU呼出しは読み取り専用の補助で、配布処理や保存関数の直接呼出しへ読み替えない。

## 失敗と限定修復

run 36102544792 は孵化2件成功・配布1件失敗、Actions全体 `failure` のまま保存した。配布は原本4技を生成済みだが、検証がSave counterを2→3と未検証で仮定し、実際の2→4で停止した。

中間run 36103989903で最初の遷移時はparty1体と判明し、原本のGetPending→ensure_save→旧内側Save移行を確認した。配布の最終run 36104762658 では、移行保存（party1）と配布保存（party2）を各frame・lock・PCとともにraw観測。手動Save後5、fresh Continue後5、再受取拒否後5を一致させる。二遷移を二回のhost保存呼出しとは解釈しない。元party100byteと配布後200byteを独立rawで照合。candidateの保存設計や全Save経路の性能を評価したものではない。

## 再実行防止と証拠

孵化各1回、配布は失敗2回+成功1回、計5native process。unitは初回20、中間12、配布phase変更影響13、host compile計4。成功済み孵化2件と初回20unitは修復で再実行しない。中間12試験はvalidator変更の影響があるため次の13試験に含めて再検証した。既存EXP/Bag/egg8/旧野生/ARM/Wikiは変更影響なし。

終端照合は新規15unitと保存ZIPのdigest/size/完全集合/全member hash/3caseのraw結果/反映commit親/Actions全stepを検査。native・旧unit・host/ARM compileの再実行0。失敗runは成功へ改ざんしない。正本 `content/modernization/pr16_natural_supply_checkpoint.json`。完了記録source `a82be04b86acec7dafccada87629ae7f62ba0329`、記録run `36105430192`。

## 次

Issue19: 自然配布/孵化の保存成功を再実行しない。限定3caseの終端確定後は未受入の他配布・form初期技、釣り/隠し野生の特殊技順を優先する。Floette12技の全供給/全owner/Issue19/release/baseline切替は未完。EXP進化共有3/EXP4/最初の拒否/アメ11/Bag23/egg8/旧野生/host/ARM/Wikiは変更影響なし。
