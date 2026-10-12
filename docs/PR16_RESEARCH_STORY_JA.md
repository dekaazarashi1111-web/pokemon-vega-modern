# PR16 通常NewGameからの自然進行

## 今回の限定受入

通常NewGame→自宅→屋外誘導→ヒイラギ研究所(map4/3)→リープン選択→通常Save→独立Continueを限定受入。研究活動の研究所(map96系)への通常ストーリー到達は未完。次は保存済みstarter.srmのContinueから実ストーリーを続ける。初期化/スターター/旧RP稼得支出/UI/BP/P08を再実行しない。

正本: `content/modernization/pr16_research_story_checkpoint.json`。候補 `e1efb1009c6e6b0ec4967bf7b20562d2330bbd933f64f7f7863cdad56eb1f842`、ROM変更0。正式測定はrun `36320959294` の2独立process/core。source `653d59e897c8ac366a68888b2c9128595b9b34de`。Actionsのrun・job・全必須stepの成功終端を外部照合済み。全体完成ではない。

## 実入力と継続点

消去Flashから既存233区間を前提入力として使用し、未観測だった自宅退出、屋外NPCの研究所への誘導、スターター選択を追った。合計421入力/30656frames、通常Save1回でcounter0→1。map4/3 (8,5)、party1、RP0。実画面18枚をローカル開発原本と独立実測で完全一致確認し、別coreのContinue後にも実画面とparty600bytes/全Flash128KiB/場所/残高/counterを照合した。研究活動のRP研究所と序盤のヒイラギ研究所は別である。

## 重複防止とartifact

`pr16-research-story-checkpoint` に通常生成のstarter.srm、固定runner、checkpoint.json、実画面を保持する。固定runtimeはartifact10898620034、候補は保存recipeから復元する。checkpointのsave/executable/full candidate SHAを照合し、`continue-story` modeへ渡す。通常NewGame原本にはsave本体がなかったため今回の開発に前提入力が必要だったが、今後はこのSaveを使用しnew-game-storyを再実行しない。ROM/save/runner/画面はGit trackedに入れない。

## 検証・境界

新59oracle/拒否検査の原本とsource bindingをActionsで再利用。7host-write拒否も前回の同一実装/原本を再利用し再起動0。正式host compile1、native2。ARM compile/link0、ROM変更0、旧受入ケース再実行0。ローカル開発は非描画診断1と自然進行確認1で、正式受入件数には加算しない。非描画診断は最初のreset後にvideoを接続したrunnerの欠陥で、専用openerをreset前接続へ修正。ゲーム本体変更ではない。新oracleは黒画面/未対screen/未知call/注入/余分なRP/差し替えsave/過大受入を拒否する。

一般CI action_required/歴史的private guardをsuccessへ読み替えない。merge/release/active baseline変更なし。

## 保存先の確定と次の直接入力

成功run `36320959294` / job `108624554711`、artifact `10932059074` (`pr16-research-story-checkpoint`)。ZIPは1345883bytes / SHA-256 `057f3c5630d1951a529bfba7e36318578b943049419eceffaf0601f77eb1f84b`、有効期限はmetadataのexpires_atを再確認する。全体原本は `content/modernization/pr16_research_story_terminal.json`。

通常生成 `starter.srm` は131088bytes（Flash128KiBとRTC付加16bytes）、SHA-256 `113f04e9e5222360687e28868fb78f394650aa5c85b357675737544d49ad346b`。元saveを保全し作業コピーだけをrunnerへ渡す。artifactの `checkpoint.json` がsave/runner/candidate/runtime/dataのidentityを束縛する。

```text
<fixed-runtime>/ld.so --library-path <fixed-runtime>/lib <checkpoint>/runner <candidate> <working-copy-of-starter.srm> continue-story 113f04e9e5222360687e28868fb78f394650aa5c85b357675737544d49ad346b
```

stdinは `key <mask> <frames>`、`observe <連番>`、`save`、最後に `quit`。maskは0/1/2/8/16/32/64/128、framesは1〜600。観測0はContinue後に自動出力されるので追加観測は1から。固定入力の再生ではなく未完ストーリーの先へ進む。ROM/save本体のtracked追加は禁止。
