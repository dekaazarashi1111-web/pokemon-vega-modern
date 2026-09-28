# Save10: 通常ボール供給・保存再開

Save10のtraining.srm作業コピーから先だけ進める。501番道路の民家map32/2(4,3)下向き、モンスターボール5個。女性の通常贈与0→5、再会話の二重受取防止、通常Save9→10、独立Continue後の5個/再受取防止を確認。リープンLv9/EXP450/HP26/26/PP35/30/25、手持ち1、RP0、2776円。次は自然捕獲で手持ち拡充または追加育成を経てマオリ/通常ストーリーへ。捕獲/トレーナー勝利/研究活動施設自然到達/全story/releaseは未完。218/cold62と旧363/cold34等の受入区間を再生しない。

## 原本と回復

測定source `02e451790c9b05d29861d29c3578ffca787061e6`、run 36423498952。測定/新規32検査/証拠生成/原本uploadは成功したが、引継ぎ2か所の次工程mirror不一致でcommit前に停止。run全体のfailureは保持する。artifact 10970079659の77画面・Save/RTC・測定結果・32検査原本を読み、ゲームやtestを再実行せず記録側だけを修正した。開発2process/32検査、正式2process/32検査、回復native0/test0。

Save10 SHA-256 `c2c08321b12ef4b5039884d9e4155eb32a614415bb68a1497758cdedfb9000c0`、131088bytes。保存前0→5個、再会話/独立Continue後も5個。他4bag pocket/残12ボール枠/2776円は不変。Save9 bank57344bytes保持、徒歩友情104→106以外599partybytes保持。Save10/cold全600partybytes・131088Save/RTC一致。12組の全画面一致。手持ち一覧だけ358pixelのsprite animation差を明示し、全画面一致とはしない。通常Save完了画面の地名は501番道路。贈与瞬間の空textに道具名を創作しない。

初期研究室での図鑑評価は研究活動施設自然到達ではない。捕獲/トレーナー勝利/全story/release未受入。前回未保存の敗北WIPを成功へ改作せず保持。次は本Save10の作業コピーのみを使い、218/cold62や既受入区間を再生しない。一般CIの既存capacity原本failureは未解決。

記録回復runのpush/upload終端は別のAPI照合で確定する。
