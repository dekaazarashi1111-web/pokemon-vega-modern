# P03 技忘れの実操作・保存受入


## 2026-09-10 — USER-MODERNIZATION-P03-P05 / 技忘れ12経路とStage84空き技PP修正

Stage83の通常Bag→わざメモリー→技忘れで、末尾MOVE_NONEのPPが35になる不具合を実再現。Stage84はID 0のcanonical PP 35→0の1byteだけを修正した。実技の全行、P06採用2種3項目、保存ABI、Stage62基準は不変。旧Stage83で同じPP残留を検出する対照1件も通した。

実行HEAD 8846cd86de22af35b41eb358b9ed30e4c825750c、Actions 34459625383、GCC 13.3.0 / mGBA 0.10.2で12経路PASS。4枠削除、PP Up警告拒否、最終確認拒否、画面取消、最後の1技拒否、2フォーム制約、秘伝技削除、Keldeoの姿復帰を、通常保存・新規core Continueまで検証。12新規プロセス・24core・キャッシュ0、ホスト書込7 API拒否、保存後100byte個体一致。準備個体・位置・道具はfixtureなので自然入手の受入ではない。

原本78ファイルのZIP、Actions run/jobs/artifact原本、20入力source hashを照合し、content/modernization/p08_p03_forgetting_acceptance.jsonへ接続。新総括はcontent/modernization/p08_remaining_work.json。旧p08_current_acceptance.jsonはStage81起点の履歴として保持し、現在の残件数には使わない。繁殖8件・容量3件・Mega6+36件・思い出し46件を未着手へ戻さず、P06採用2件を反映する。異なる候補の成功を単一最終候補全体の受入とはしない。

P05の現行facility_modes.csvはFactory/Mirageの20モードで、Circus入場モードは同採用表に無い。表外の入口まで不存在とは断定しない。実際の受付・入場から特性抑制までの検証は未完了。P03のその他の進化・フォーム習得・タマゴ供給・economy正式確定、P06工程受入、P07既存資料照合・採用・実装、単一最終候補と配布判定も残る。

本統合は新規mGBA実行0件。PRはDraftのまま、マージ・配布・プレイ基準変更なし。全体guardの既存ROM/save・過去path違反は未解消であり、差分guardと区別する。通常CIの設定は別の権限付き変更として追加する。

Integration run: 34461845380; source: 5783414f58fcfd1c222e26cd3cc1280eea8d0b2e.
