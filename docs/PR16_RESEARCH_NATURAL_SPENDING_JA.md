# PR16 自然稼得RPのショップ支出

## 現在の限定受入

`PASS_NATURALLY_EARNED_RP_SPENDING_AND_SHOP_UI_SCOPED`

自然稼得10RP→5個交換→残高0→独立Continueは限定受入。71byte shop UI後処理と最終12画面も受入。次は通常NewGame/ストーリー進行から研究活動・研究所へ到達する未完境界。既存badge/map/party/屋外warp fixtureを自然到達へ昇格しない。成功した稼得/支出save・数値2境界・標準リスト・旧4入口・旧稼得/BP/P08は変更影響なしに再実行しない。

正本checkpoint: `content/modernization/pr16_research_natural_spending_checkpoint.json`。原本: `content/modernization/pr16_research_natural_spending_evidence`。

Task: `USER-20260927-RESEARCH-NATURAL-SPENDING`

## 保存済みsource checkpoint（以下は途中経過）

標準リストは509cea8で限定受入済み。本作業はその後の別境界。最終候補は32MiB `e1efb1009c6e6b0ec4967bf7b20562d2330bbd933f64f7f7863cdad56eb1f842`。

旧canonicalの記述から想定したpixel getter参照は、実ROMでは0x38即値へ置換済みでdead literalだった。この既存配置を維持する。変更は生きたframe描画/inputの2参照、上端余白1tile、0x09F4B000の64byte Thumbだけ。宣言76byte内71byte差分、全ROM rollback一致、新EWRAM0。会話用の幅広枠はClearStdWindowAndFrameでなくClearDialogWindowAndFrameで消し、window0の所有は保持する。価格/商品/数量/保存・研究owner/数値/標準リストは不変。

ローカルの固定Actions runtimeで、0RP fixtureから実Rock Smashの10RPを一度だけ稼得し、終了saveを保持した。最初の支出観測はpixel前提違いで停止し、後続はUI上の残枠を検出。成功した支出原本は10→0RP/モンスターボール5個/自動保存2/別core Continueを示す。最終64byte修正では保持済み稼得・支出saveを用い、4ページ・確認取消・0RP再訪のUI-only検査だけを行い、新しい稼得/購入/保存は0。最終12画面を視認し、枠の欠け・会話残留の解消を確認した。

このcommitは実装source checkpointであり、原本の独立検証器・拒否試験・固定引継ぎ・両ログの正式記録は続行中。source/native/UIの原本は後続の専用evidenceにまとめる。旧失敗をsuccessに読み替えない。

## 範囲を広げない

badge/map/partyは起動前fixture。支出時には稼得済みsaveの全ledger/Bag/party/Flashを固定し、場所だけ研究所屋外へ移すfixtureを用いた。barrier以降は物理キーだけだが、採掘地点から研究所への自然移動・通常ストーリー到達は未受入。RP注入・手動保存・旧受入matrixの再実行はない。merge/release/active baseline変更は行わない。

## 検証と記録

固定Actions artifactのruntimeをローカルで使用した実測であり、Actions上のnative実測ではない。GitHubには原本stdout/stderr/実行identity/生成C全bytes/画面hashと直接視認所見を保存。PPM/ROM/save/runnerはtrackedに含めない。稼得1process、支出開発3process（観測前提停止1を含む）、最終UI-only1process。最後の表示修正は成功した支出候補の1byteだけで、保持済み10RP/0RP saveを開き、追加稼得/購入/保存0で12画面を確認。23patch試験原本を再利用し、独立oracle/拒否120件を記録Actionsで検証。Actionsの終端は外部からの次の読取で確定し、一般CI action_requiredをsuccessへ変更しない。
