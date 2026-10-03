# PR16 Save8後の通常育成・逃走対照・Save9

Save9のtraining.srm作業コピーから先だけ進める。リープンLv9/EXP450、次Lvまで110、HP26/26、PP35/30/25、手持ち1体、RP0、map4/0(8,5)。Save8からの野生3勝119EXP・通常逃走2回・母親回復2回・通常Save8→9完了表示・独立Continueを確認。捕獲/トレーナー勝利0。次は自然な用品入手/手持ち拡充または追加育成を経て、東側道路map3/19のマオリ/通常ストーリーへ。マオリ勝利/研究施設自然到達/実渡航/全story/releaseは未完。本区間363/cold34、親316/cold34とそれ以前の既受入nativeを再生しない。

## 新しく実測した範囲

エネコLv5・ドードーLv5・フロンLv4を通常技で倒し、37+45+37=119EXP。EXP331→450、Lv8→9。ドードー戦後HP6/24で帰宅し、途中のスバメLv3から通常逃走。2巡目のフロンLv3からも通常逃走。逃走前後の全600partybytesを比較し、経験値やHPを加算せず、3勝と2逃走を分離した。母親で2回通常回復。捕獲/手持ち追加/トレーナー戦/敗北は0。この区間を用品供給やマオリ勝利完了とはしない。

## レポート完了までの観測

Start→レポート→書込確認→上書き確認→書込中→「しっかり かきのこした！」→field復帰を通常キーだけで実行。counter9は最終Flashより先に見えたため、counterだけで完了判定しない。観測65はcounter9だが書込中、66で完了表示と最終Flash、67でlock解除。Save8 bank57344bytesを保持し、14sectionの一意ID/署名/counter、成長関連11bytesと残るparty589bytes、ledgerの時刻以外の所有領域保持を検証。sector checksum全種の一般検証を追加したとの主張はしない。

## 独立Continue

全Save/RTC131088bytesとparty600bytesを保存前後/coldで照合。手持ち/情報/能力/技の4UIは全PPM byte一致。リープンLv9、EXP450、次Lvまで110、HP26/26、攻撃16/防御13/特攻17/特防14/素早さ18、PP35/30/25。保存位置は自宅map4/0(8,5)、RP0。戦闘後の旧field=false/flags4/outcome4は書換えず、field callback/lock/完了画面/cold flags0を併用する。

## 原本と実行境界

新区間363入力31080frames・独立Continue34入力2808frames、74画面、30直接目視anchor、76新検査PASS。開発native2/76検査と正式native2/76検査を分離。終端回収は保存原本を読むだけでnative/test再実行0。ROM/runner/既受入source/active baselineを変更せず、旧Save8生成316/cold34やそれ以前の受入nativeを明示再実行しない。次は後継Save9から先だけ。実行中の観測待機不足は待機延長で回収し、キー再送やprocess再起動は行わなかった。

正式source `be27b66e1486c28cdf9e2c40009359f2072881da`、run `36408354430`。終端は別のAPI回収で確認する。

## Actions終端確認済み

全11step成功。artifact `10963436148`、completion `fd76df97fda7227d1a1e5360f7cbe5c0b238526d`。全74画面/保存原本/76検査原本/commit textを照合。native/test再実行0。次は後継Save9 training.srmからのみ。
