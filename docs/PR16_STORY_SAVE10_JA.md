# Save10: 通常ボール供給・二重受取防止・保存再開

## 開発測定済み、専用Actionsの正式終端は未確定

正式親はSave9（run36408354430、artifact10963436148）。新しい通常入力だけで、501番道路の民家map32/2の女性からモンスターボール5個を受け取り、再会話で増えないこと、通常レポート9→10の完了表示、独立Continue後にも5個のままで再受取できないことを観測した。

新区間218入力/16486frames、独立Continue62入力/4608frames、77画面。新規専用32検査は開発環境でPASS。正式Actionsへの保存・固定引継ぎ・両ログの完了記録は次の工程であり、現時点の正式再開点はまだSave9。

## 保存と非変更範囲

後継Save10は131088bytes / SHA-256 `c2c08321b12ef4b5039884d9e4155eb32a614415bb68a1497758cdedfb9000c0`。独立Continue後もRTCを含む全byteが一致。旧Save9 bank57344bytesを保持。バッグの再暗号化keyを解いた差分はボール欄のitem4×5だけで、他4pocketと残12ボール枠、所持金2776円は不変。

リープンLv9/EXP450/次まで110、HP26/26、PP35/30/25、手持ち1体、RP0。徒歩による友情104→106の1byte以外599partybytesを保持。通常保存された時計以外のledger ownerに変化なし。

バッグ・再会話・情報/能力/技・fieldの12組は全pixel一致。手持ち一覧はsprite animationの矩形内358pixelだけ異なり、一覧全画面一致とは主張しない。Save画面は「501ばんどうろ」。途中の502番道路という呼称は訂正する。贈与瞬間の空白画面から道具名の受取文章を創作しない。

## 次工程と受入境界

検証器 `scripts/pr16_story_save10.py`、拒否検査 `tests/test_pr16_story_save10.py`、固定開発原本 `content/modernization/pr16_story_save10_development/` を使う。終了済み開発入力を対話的に再生せず、専用Actionsの初回正式測定を原本へ結び付ける。測定が完了した後の記録回復ではnativeを再実行しない。

通常ボール供給以外の捕獲、トレーナー勝利、研究活動施設自然到達、全story、releaseは未受入。初期スターター研究室での図鑑評価を対象研究施設到達と混同しない。前回の未保存WIPと敗北記述は `docs/PR16_STORY_SAVE10_WIP_JA.md` に保持し、成功へ改作しない。

ROM変更・再生成・active baseline変更・merge・releaseは0。正式終端を確認後はSave10のtraining.srm作業コピーから先だけ進め、旧Save9の363/cold34入力も、この218/cold62入力も再生しない。
