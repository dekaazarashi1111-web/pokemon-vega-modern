# P03 通常習得・保存・新規core再読込の代表通し試験

既採用のStage65経路、キャタピー Species 649 / Lv.9 / むしくい Move 535を、Stage80候補ROMで試験する。P03全体の受入とは分離した補助証跡である。

## 実行

```sh
python3 -m unittest tests.test_modernization_p03_learning_e2e -v
python3 scripts/run_modernization_p03_learning_e2e.py
```

GitHub Actionsは `p03-learning-e2e`。固定Ubuntu/mGBA toolchainを利用する。新規2 processを使い、過去のStage79 cacheを使わない。

## 観測する流れ

最初に固定QA saveの私有コピーを通常タイトル・Continueで読み込む。操作可能fieldへ入った後だけ、キャタピーとふしぎなアメ1個をfixtureとして作成する。技はたいあたり・いとをはく・空・空であり、むしくいは事前注入しない。

通常Start→Bag→Party操作でアメを使い、進化sceneのbegin/updateと物理B取消を観測する。成立ケースはLv8→9でslot3にMove535が入り、既存2技とslot4の空欄が維持され、PPが非0になることを要求する。対照ケースはLv7→8でMove535を習得しないことを要求する。どちらも種族を保持し、アメが厳密に1個消費される。

その後、通常Startメニューの保存actionを選ぶ。native保存callbackと保存counterの+1を観測し、元coreを破棄する。新規coreではfixtureやsnapshotを再注入せず、通常Continueだけで種族・レベル・4技・対象slotのPP・アメの消費・保存counterを再確認する。

## 証跡と失敗条件

`.local/p03-learning-e2e/` にコンパイル出力、各processのstdout/stderr、両ケース成功時のみ `result.json` を保存する。失敗終了・不正JSON・契約不一致・ROM/seed改変・source/baseline改変では成功記録を作らない。再実行の開始時に以前の成功記録を削除する。

ROMはStage80の既知SHA-256、seedは既知Stage60 QA saveのSHA-256へ固定する。依存するP02/UI共通runnerは既存Stage79 manifestのsize/SHA-256を検査し、この試験のために変更しない。元のROM・seed・Stage62基準・既存Stage79証跡は変更しない。

## 範囲外

これは空き技slotへ入る通常level-upの代表経路だけである。技4枠満杯時の入替・習得拒否、戦闘EXP由来のlevel-up、全species・全習得技、育て屋/タマゴ、machine/tutor/archive UI、P05戦闘schedulerは未検証である。既存のP03全体フラグを上書きせず、`full_p03_acceptance=false`、`breeding_e2e=false`、`release_ready=false`を維持する。
