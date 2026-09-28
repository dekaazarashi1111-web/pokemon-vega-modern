# PR16 回復後の通常進行・実キーSave7

Save7のstory.srm作業コピーから通常育成/手持ち拡充を進める。Lv7/EXP270、次Lvまで44EXP、HP23/23、技PP35/30/25、RP0、map4/0(8,5)。マオリ戦は敗北であり勝利0。同じ低戦力戦闘や完走270/cold34入力を無策に再生しない。北の伐採木で止まる経路を再探索せず、育成後は東側道路map3/19から自然ストーリー進行。研究施設自然到達/実渡航/全story/releaseは未完。

## 実測した区切り

回復済みSaveから東側道路(53,10)へ通常入力で進行。スバメLv3から逃走後、マオリのパモを倒してEXP25を獲得したがコフキムシLv8に敗北し56円を支払い、通常全滅帰宅した。新しいゲームの勝利/施設到達とはしない。通常回復後に実StartメニューからSave6→7、独立Continueで全Save/RTCと4UIが一致。EXP245→270、party600bytes中の変更はEXP2bytesとbyte41の85→86だけで他597bytes保持。

## 旧telemetryを実ゲーム状態と混同しない

戦闘後に旧battle_flags/outcomeが12/2で残り、field=falseとなる。原本/driverを改変せず、callback2とlock、実メニュー→レポート→確認→上書き→保存完了画面、counterとFlash、coldでのflags/outcome0を照合。補助save命令ではなく通常keyだけを使用した。観測6/30の黒画面は実マップ遷移/戦闘退出であり、受入anchorは空画面を拒否する。

## 証拠と再実行禁止

正式native2、開発native2は別会計。正式53新検査PASS。旧母親81、training194、growth367、route301、starter114入力の再生0。ROM/runner変更・compile・guard再起動0。原本の全SHAと19個の目視anchor、全110画面は固定。ROM/save/runner/画面は非tracked artifactのみ。

正式source `5b378dcae45d7f92307d27ea07ab7041ebce25f5`、run `36370422350`。終端は別のAPI回収で確認する。
