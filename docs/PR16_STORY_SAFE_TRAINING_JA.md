# PR16 Save7後の通常育成・実キーSave8

Save8のtraining.srm作業コピーから先だけ進める。リープンLv8/EXP331、次Lvまで88、HP24/24、PP35/30/25、手持ち1体、RP0、map4/0(8,3)。野生3勝でEXP61獲得、母親で2回回復し通常Save7→8と独立Continueを確認。ボールポケット空のため捕獲0。次は自然な用品入手/手持ち拡充または追加育成を進め、東側道路map3/19から通常ストーリーへ。マオリ勝利/研究施設自然到達/実渡航/全story/releaseは未完。完走316/cold34入力、旧Save7生成270/cold34、既受入nativeを再生しない。

## 実測した区切り

低戦力でマオリへ再突入せず、道路の野生ヤヤコマLv2/スバメLv3/スバメLv4を倒して7+21+33=61EXP獲得。HP10/23の時点とLv8への上昇後に帰宅し、母親の通常回復を2回受けた。捕獲用ボールのポケットは空で、捕獲も手持ち追加も0。これを用品供給完了とはしない。

## 保存と保持

通常キーだけでStart→レポート→確認→上書き→書込中→field復帰、counter7→8。保存完了文言そのものの画面は未採取だが、書込中/前後Flash/14section counterと署名/前回bank保持、独立Continueの全Save/RTC131088bytesを照合。party600bytes中の成長関連11bytesだけ変化し、残り589bytes/個体識別/技/空partyを保持。前回Save7 bank全57344bytesを保持。

## 表示とtelemetryの境界

Lv8の能力/情報/技/手持ち4UIはcoldと全byte一致。EXP331、次Lvまで88、HP24/24、PP35/30/25。レベル上昇中の特攻15と回復後summary16を同じ表示と偽らず、原本のまま残す。戦闘後のfield=false/flags4/outcome1は旧telemetryのまま保持し、callback/lock/実画面/保存/cold flags0を併用。町の初期研究室map4/3へ一度入退室しただけで研究活動施設への自然到達とはしない。

## 再実行禁止と証拠

新規316入力/25208framesと独立34入力/2808frames、全70画面、34目視anchor、93検査PASS。開発native2/検査93と正式native2/検査93を分離。ROM/runner/既受入source不変、compile/fixture/明示した旧native再実行0。Save7生成270/cold34や本区間を再生せず、後継training.srmからのみ続ける。ROM/save/runner/画面は非tracked artifactのみ。

正式source `c108d25ac7b29b77b8984384968d5ca9037daf4e`、run `36374575742`。終端は別のAPI回収で確認する。

## Actions終端確認済み

全11step成功。artifact `10950920338`、completion `8237efa33fab55009c6163d804724723bebcd35c`。全70画面/保存原本/93検査原本/commit textを照合。native/test再実行0。次は後継training.srmからのみ。
