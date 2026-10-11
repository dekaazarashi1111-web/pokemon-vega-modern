# Save12: 母親による2体回復・保存再開

Save12のtraining.srm作業コピーから先だけ進める。自宅map4/0(8,5)上向き、リープンLv9/EXP450/HP26/26/PP35/30/25、ツツケラLv3/EXP27/HP15/15/PP35/40。母親の通常会話1回で2体全回復、Save11→12と独立Continue後の全Save/RTC保持を確認。手持ち2、ボール3、2776円、RP0。次は育成からマオリ/通常ストーリーへ。今回に新しい戦闘/捕獲/経験値獲得はない。トレーナー勝利/研究施設自然到達/図鑑統合/全story/release未完。153/cold40と旧176/cold50等は再生しない。

## 今回の受入範囲

Save11から通常歩行で501番道路→ハクジタウン→自宅。回復前の両個体情報/技画面、母親の通常会話1回、回復後HP26/26と15/15・全PP、通常レポート確認/上書き/4つの途中Flash/完了表示/field復帰、独立Continueを結合する。歩行によるなつき度106→108/50→51を回復とは分ける。メニューや会話中の不発入力も原本に保持。

## 保存byte境界

前回Save11 bank57344bytesと未使用400partybytes保持。partyの変化は歩行2bytesと回復5bytesだけ。EXP450/27、Lv9/3、全5bag pocket/ボール3/2776円/RP0は不変。ledgerは時計/checksumの5bytesのみ。通常Save11→12の完了はlock1、次の観測でfield解除。独立Continue後の全131088Save/RTC保持と手持ち/両個体情報/能力/技の7組全画像一致。一般section checksum全種の受入を主張しない。

## 未受入

今回の戦闘/捕獲/経験値獲得0。マオリ勝利/研究施設自然到達/全story/release未完。図鑑No???・レポート1匹を保持し図鑑統合を受入にしない。元Save10 run failureと旧敗北・一般CIの既存capacity failure/action_requiredは歴史のまま。

## 実行会計

開発2process/69検査、正式2process/69検査を別計上。旧受入の明示再実行0、ROM/runner/compile変更0。完走153/cold40入力/57画面は原本回収だけにして再生しない。

正式source `1540de2edb1dab0479b95a4468176e07b0bfd086`、run 36435307920。全step/保存artifact/commit終端は別API照合で確定する。

## 正式終端

run 36435307920 の全step成功、completion `92f9a632ba2114a3624ca71ea64063363349b35f`、原本artifact 10975157558。次はこのartifactのtraining.srmのみ。終端回収native0/test0。
