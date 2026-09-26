# 特殊野生: 通常操作検証

特殊野生通常UI: STOPPED_SPECIAL_WILD_UI_WITH_NATIVE_EVIDENCE。成功=[]、失敗={'fishing': {'message': 'native process failed', 'returncode': 1, 'timed_out': False}, 'hidden': {'message': 'native process failed', 'returncode': 1, 'timed_out': False}}。開始fixture/実取得は区別。

Issue19: 特殊野生の通常UI checkpointの失敗原本を確認し、未成功caseだけ修復する。生態レーダーはROM生成ID348でありcatalogのITEM_KEY_SCANNER278とは別。捕獲/通常Save/fresh Continueの全条件が揃うまで昇格しない。保存候補0205af9b・前準備・直接7process/8call・旧受入は再実行しない。map3/19除外130行は変更しない。

生態レーダーID348の通常隠しメニューと、すごいつりざお264が対象。前準備のcatalog scanner278は通常隠しUIのownerではない。前準備原本は不変。

初期map/lead/item/unlock/research/RNGだけfixture。観測区間は7host APIを遮断し、CPU読取りとキーだけを使う。特殊setter/4slot/PP/捕獲100byte/保存200byte・全inventoryを照合する。

最新run `36219826803` / source `52daffc8fae043674bc0405df8fe296c1fcfbd61` / failure `None`。

原本: `content/modernization/pr16_special_wild_ui_checkpoint.json`。全Actions完了は同run実行中の自己証明をしない。release/Issue19/baseline切替なし。
