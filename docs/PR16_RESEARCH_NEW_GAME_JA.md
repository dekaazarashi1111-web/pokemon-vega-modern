# PR16 通常new-game・初回Save・独立Continue

通常new-gameを消去Flashからキー入力のみで開始し、初回Start Saveと独立Continue2回を受入。counter0→1→1→1、全ledger2048/Bag5pocket/party600/Flash128KiBを照合。

## 実行条件

128KiB全FFのFlashから開始。元private seedはnative入力に使用しない。通常BOOT_TRACE先頭233区間/13490framesと600framesの静止だけを使用し、初期化関数の直接呼出・文字速度変更・進行/party/ledger注入・warp・register/stack fixtureは0。RTC準備はmGBAの付加16bytesだけでFlash全byte不変を照合し、7API書込barrierを最初のゲーム実行前に装着する。旧fixture付きfield trace helperは呼ばない。

実scriptが終了したmap4/0の(10,2)、実player object(17,9)/西向き・移動停止を確認し、最初の通常Start Saveへ進む。starter取得前でparty count0。全台帳はVGS1/V2/2048、孵化mode1、ExpShare0、文字速度0、研究rank1/nextTransaction1/RP0、通常minuteとchecksum以外はsource初期値であることを独立に照合する。初回保存前Flash全FF/counter0、Save後counter1と実Flash変更、独立coreのContinue2回は全128KiB Flash不変・counter1・全Bag/party/ledger/位置保持を要求する。

## 境界

対象は通常new-gameの初回保存境界だけ。スターター取得、実RP稼得、通常進行からショップへの到達、全catalog、日本語画面の目視監査、Issue19全体/P08/releaseは未受入。候補は購入と同じ5d1fc9、ROM変更/ARM compile/link/旧受入再実行0。新C検査52件にはmain一意・注入API呼出禁止とtrace構文/正規化hashを含む。

## 記録

run `36250444503` / source `bb2d74a1aa61d3d6d6b97580513bae49d8a71394` / status `PASS_NORMAL_NEW_GAME_SCOPED` / 終端確認 `True`。manifest `content/modernization/pr16_research_new_game_evidence/36250444503/manifest.json`。失敗原本はattempt_historyに保持し、途中の成功で全体を昇格しない。一般CIのaction_requiredは限定成功とは別である。

## 次工程

次は実RP稼得と通常進行からResearchショップへの接続、全catalog価格/日本語文言の監査。通常new-game1件・購入1件・取消1件、各oracleと旧host/phase0/V1/retryは影響なしに再実行しない。
