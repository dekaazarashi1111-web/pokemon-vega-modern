# Save13: 通常交代の育成1勝・保存再開

Save13のtraining.srm作業コピーから先だけ進める。自宅map4/0(8,5)上向き、先頭ツツケラLv4/EXP80/HP17/17/PP35/40、2番目リープンLv9/EXP479/HP26/26/PP35/30/25。通常並替・戦闘中の通常交代でスバメLv4に1勝し、53/29EXPを獲得。母親で通常回復、Save12→13と独立Continue後の全Save/RTC保持を確認。手持ち2、ボール3、2776円、RP0。次は必要な通常育成を続けてマオリ/通常ストーリーへ。トレーナー勝利/研究施設自然到達/図鑑統合/全story/release未完。255/cold40、受入済みSave12の153/cold40、Save11の176/cold50等を再生しない。

## 今回の受入範囲

Save12から通常手持ちメニューでツツケラを先頭へ。501番道路の野生スバメLv4でリープンへ通常交代し、ひっかく3回で勝利。相手のなきごえ・つつく・急所とHP26→20→9も保持。ツツケラ53EXP/Lv3→4/EXP80とリープン29EXP/EXP479を別々の実表示で確認する。均等な経験値分配を仮定しない。帰宅して母親が通常回復。保存前/独立Continue後の先頭順とHP17/17・26/26、PP35/40と35/30/25、両個体の経験値と全能力を7組の全画面一致で結合する。

## 勝利とfieldの境界

開始観測14から戦闘UI・通常交代・3攻撃・経験値/レベル表示を経て観測30のFIELD callback/lock0を1勝とする。倒れた表示や経験値途中はoutcome0のままで終端ではない。その後のflags4/outcome1残留とwire field:falseを追加勝利や未復帰と数えない。保存完了はlock1、次の観測でlock0。fresh Continueはflags/outcome0・field:true。探索セルのfield真値仮定だけを訂正し、runner/ROM/原本ログを変更しない。

## 保存byte境界

通常Save12→13。前回bank57344bytesと未使用party400bytesを保持。並替後の個体を整列して比較した変更は14bytes、母親回復はリープンのHP/PPの2bytesだけ。全5bag pocket/ボール3/2776円/RP0は不変。ledgerは時計/checksumの5bytesのみ。独立Continue後の全131088Save/RTCを保持。一般section checksum全種の受入は主張しない。帰宅迂回とバッグ誤選択も元入力のまま残す。

## 未受入

新規トレーナー勝利/捕獲/敗北/逃走0。マオリ勝利/研究施設自然到達/全story/release未完。図鑑No???・レポート1匹を保持し図鑑統合の受入へ転用しない。元Save10 run failureと旧敗北・一般CIの既存capacity failure/action_requiredは歴史のまま。

## 実行会計

開発2process/95検査、正式2process/95検査を別計上。旧受入の明示再実行0、ROM/runner/compile変更0。完走255/cold40入力/76画面は原本回収だけにして再生しない。Save12の153/cold40、Save11の176/cold50等も再生しない。

正式source `34d037bc5c56de271aba627a9a001f15b6534123`、run 36439214540。全step/保存artifact/commit終端は別API照合で確定する。

## 正式終端

run 36439214540 の全step成功、completion `e6ed6433459ac5e8c49badc996c7279655e5c838`、原本artifact 10976693019。次はこのartifactのtraining.srmのみ。終端回収native0/test0。
