# Storyの到達点・継続・診断停止

実行方針の正本は `PR16_STORY_ACCELERATED_ACCEPTANCE_PLAN_JA.md`。Save25〜100の生成手順の「最初の雑魚戦で保存」は各区間の履歴として保持するが、以後の一般方針へコピーしない。受入済native/成功unitの無変更再走はしない。

主要badge、重要施設、明示story event、region/warp接続、殿堂入り、endingを開始位置・到着条件・owner・資源下限とともに宣言する。Save101は解放後の西地域接続3/2→3/24であり意味のある保存点。未解明の壁や診断frontierをmilestone達成と呼ばない。

`scripts/pr16_story_milestones.py` は対応済type/固定owner/許可callbackとUI/正規outcome/同地点field復帰/story effect/実測HPとPPを満たす通常戦をcompact ledgerへ追加し、宣言済milestoneへの継続を返す。勝利だけで保存しない。選択回数からPPを推測せず実観測を使う。新規host検査は複数戦継続とfail-closed分岐を対象とする。

入力adapterはrouteごとにbindingする。party hashだけから任意の戦闘後HP/PPやownerを推測しない。不足なら診断停止する。今回Save101は非草地5歩の地域接続でbattle adapterは未登録、予期しない戦闘には入力しない。汎用state machineのhost検査を連続戦native受入へ昇格しない。

未知callback/event/warp/story effect、未対応UI、観測不一致、資源不足、有限予算超過はDIAGNOSTIC_STOP_NOT_MILESTONE。最後の正式Saveからの新規失敗区間を保存し、原因とownerを解決してから進む。無入力待機を含め、未知状態からの盲目的決定を許可しない。

Save100以前のRAM差/physical2056未解決、一般CIの既知QOL source不一致、final HEAD action_requiredは未完のまま。全国図鑑は通常4072=9→10→研究所special367/var11。その後の別progressionで自然EXP/進化/Lucky Egg/12境界/Lv100soak。flag注入/進化gate回避/新balance/releaseは行わない。
