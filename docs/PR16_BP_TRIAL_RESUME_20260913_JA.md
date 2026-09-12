# PR16 BP Trial 再開点 — 2026-09-13

正本: `content/modernization/pr16_bp_trial_checkpoint.json` / `content/modernization/pr16_bp_trial_receipt.json`。旧受入を新候補実行へ読み替えない。

## 今回の差分

高モード受付のTrial(status10)から、誤って完了処理へ飛ぶ4byte operandを旧物理受付wrapperへ修正した。研究/credit wrapper、完了adapterを迂回しない。候補SHAは `df8a15c3b464854ca84a5c0533177cfa3187b5eef252d20248f7654edb72887c`、サイズ33554432、CRC32 `5283EC5F`。旧e630生成recipeは変更していない。工程間BPS往復は検証したがclean-ROM二重生成ではない。

## 実行結果と直接停止点

静的診断3runのうち最後34707830538が成功。nativeは34708218707の1新規プロセスで実受付、Trial/Standard/確認、6レンタル生成、元party snapshotまで到達。説明メッセージ「ランダムな6ひきから3ひきをえらんでください」で停止し、Chooser callback未観測。最終12615frames、party6、snapshot_valid1、marker1、BP0、save2。失敗原本を保持し、取消・通常保存・fresh Continue・獲得BPは未受入。

次はScriptContextの実構造、native wait、special0x2Fの実ROM bindingを確認する。旧ログのB_CONTEXT+8はcontext開始位置でありscript PCではない。同じ成功済み受付取消や静的探索を再実行しない。ROM条件変更や追加観測がない同一失敗再実行もしない。

## 証拠と境界

4原本ZIPを外側digest、最終member digest、実行HEADのソース、Actions run/jobで結合し、index/HEAD readbackをpush前に要求する。診断原本2件はプロセス終了前receiptのstream digest不一致を明示し、最終workflow manifestで検証する。原本receiptを上書きしない。P03 fixed-form5/5、generic FORM、P07等を再オープンしない。physical gap4件とP08 gate2件は未完。merge/undraft/release/active baseline切替なし。
