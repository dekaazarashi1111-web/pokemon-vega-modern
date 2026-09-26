# PR16 共有研究保存delegateの限定影響検証

Task: `USER-20260926-RESEARCH-SAVE-IMPACT`

入口は `CHATGPT_RESUME.md` と固定再開MD/JSON。本文はこの作業の範囲・証拠・次の未完を説明する。正式BP/P08 checkpoint、active baseline、特殊野生の既受入原本を置き換えない。

## 発見と実装

初期HEAD `be751c120cea6bdaa58a6fa5240ab40a942e1cf6` の次作業は、共有研究保存delegate修正の他取引への限定影響検証だった。旧保存先0x09377695（load）から0x09377661（save）への既存修正を固定recipeで復元し、候補23d58409のearn/spend/rank/recoveryを調べた。

研究経済の既存test modeは外部Bag/Flashサービスを模擬するため、今回の実サービス検証へ流用しない。新runnerは通常schedulerから実取引を1回呼び、実Flashのprepare/commit、故障注入またはcommit前電源断、別coreでの通常Continueを2回観測する。fixtureとABI引数の設定は明示し、CPU観測中の7host書込みAPIを拒否する。通常取引UIそのものの受入ではない。

この検証で別の実不具合を発見した。研究 `FN_CHECK_BAG_SPACE` が `CheckBagHasItem(0x08099949)` を指し、未所持アイテムをBag満杯として拒否していた。実際にitem991とitem4で所有確認=0、容量確認=1なのに取引結果15だった。正しい `CheckBagHasSpace(0x08099A09)` は既存数+要求数<=999、未所持時は空きslotを調べる。本体hash、Thumb命令と両callsite、通常mGBA結果を照合した。

`pr16_research_bag_delegate.py` は共有literal `0x13BF530` の `49990908` を `099a0908` へ2byteだけ変更する。全ROMのoutside差分0と全rollbackを確認し、canonical Cの1macroも同じdelegateへ更新する。新ARM compileは不要。所持アイテムをfixtureへ足して誤接続を隠す方法は採らない。

- 既存保存修正親: `0205af9bd2d92b1b3303195ab0cc84e5ea0f3de390ade15d9f8ce42a6dcdd1a0`
- 保存修正済み親: `23d584095f7bc0691e1582da447d6cd9a389d8698e061ea2de9f6eac03b63f48`
- Bag修正後候補: `4aee03e8ec0135efa52d8d2b41edf61637ddc65e4be9f1a0b60a2e1c23dbefe7`
- いずれも33554432 bytes。製品SHAやactive baselineではない。

## 証拠と受入境界

| 対象 | 候補 | 成功原本 | 範囲 |
| --- | --- | --- | --- |
| existing earn / simple earn | 23d58409 | run36229142708、各4件 | 成功、prepare失敗、commit失敗、commit前中断 |
| spend / rank | 4aee03e8 | run36229762846、各4件 | 同じ4境界、実BagとFlashを使用 |
| spend / rank 容量拒否 | 4aee03e8 | run36229762846、各1件 | native AddBagItemで999個のfixtureを作り、取引は結果15・保存0・無変更で拒否 |

候補4aee03e8でearn8件を再実行したとは記録しない。変更は容量helperのliteralだけで、CreditActivity/recover_pending/persist_phaseと野生捕獲の実行bodyは同一。earnの適用はこの差分証明に限定し、実行候補identityを保持する。受入済み特殊野生2件は再実行しない。

18件の各成功原本にはfixture→returned/cut→fresh Continue→2回目fresh Continueの4観測、全64byte研究owner、正規化した全Bag、対象外アイテム、手持ち600byteのhashと人数、保存counter、実save/load呼出し数を保存する。既存報酬のpendingは復旧時に1度だけ反映し、simple/spend/rankの未確定予約は解除する。2回目Continueで再加算・再支給・追加保存がないことを確認する。

元run36229142708はearn8件成功・spend/rank8件失敗を持つ **failureのまま** 保存する。元の失敗を成功runへ改称しない。さらにrun36228964902はartifactリダイレクトにAuthorizationを転送した取得不備で、native開始前に停止したfailure。HTTPSリダイレクトで認証を分離して修正した。権限不足ではなかった。

固定原本artifact:

- earnを含む元測定: artifact10902306338 / 26921 bytes / SHA-256 `992fca1b848c54977c6301d4f267e3a834b16359e6af8f5bced23c9d339c3105`
- 修正後spend/rank: artifact10901613823 / 29835 bytes / SHA-256 `945e2b9b2dc70479761618a8702f3a1f873fad8d05fe1bd2374fb57e67b879f6`

固定mGBA artifactとseedは読み取り専用の入力として使用し、ROM/saveの原本や生成物をtracked textへ入れない。公開証拠にはsynthetic ownerとhash、終了コード、source/run bindingだけを残す。ローカルのfixture/IRQ/scheduler診断も別途行っており、18件の正式原本数やActions実行数に混ぜない。

## 残件・過大主張の禁止

通常研究取引UI、全catalog、save新規初期化/V1移行、phase0そのものの失敗注入は未受入。次はこの共有保存経路の未検証範囲を限定して扱う。既受入18件を理由なく再実行しない。map3/19の除外130行は未確定のまま保持し、Issue19全体の完了・merge・draft解除・release・active baseline切替を主張しない。

原本の最終受入、canonical source反映、固定引継ぎMD/JSON、両ログ、Actions終端receiptは `content/modernization/pr16_research_save_impact_checkpoint.json` に束縛して記録する。checkpointの `actions_completion_confirmed` がtrueになるまでは終端未確定として扱う。
