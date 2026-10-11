# 通常成長・道具消費・保存継続の限定checkpoint

## 今回の区切り

`potion.srm` の受入済み道路地点から続けた新規区間。野生戦の37経験値と別トレーナーの相手1体からの33経験値により、リープンがLv5からLv6へ成長した。キズぐすり1個を通常バッグから使い、使用画面でHP9→19を確認した。新規トレーナー戦は2回とも敗北であり、勝利として数えない。通常の自宅復帰・母親回復を経て、Lv6、経験値204、HP21/21、道具ポケット空、RP0、party1のまま自宅前でSave counter3→4を保存した。

新しい町や研究活動施設へ到達したという受入ではない。全体story、配布、全learnsetの受入、新しい技の習得、merge、active baseline切替を含まない。候補ROM、runner、既受入の解析器は変更していない。

## 元の正式checkpoint

親は `content/modernization/pr16_research_story_route_checkpoint.json`。run `36330546824`、source `228d31f3e3ab74dbfc089b63a75478c0d5fde1eb`、artifact `10934928662` の全11必須step成功と保存済み原本を照合した。旧301入力は再実行せず、保存地点map3/19 (26,17)から新しい入力だけを続けた。

候補は33554432bytes / SHA-256 `e1efb1009c6e6b0ec4967bf7b20562d2330bbd933f64f7f7863cdad56eb1f842`。固定runnerは73792bytes / SHA-256 `67096f8c8a487c03957da071d0190f74542480fb051cf8e8934e1b05adee9a61`。runtime/data artifactは `10898620034` / `10898510128`。元Save/RTCは131088bytes / SHA-256 `8e924f8f058007f204db4319304f064f5b3232256b2e41a3706f88d4e2105110`。

## 今回保存した新規原本

`content/modernization/pr16_research_story_growth_development/` に操作原本、全stdout/stderr、118新検査の成功原本、目視した意味アンカーと画面集合の照合記録を保存する。進行367入力/37210frames/85画面、独立Continue38入力/2736frames/7画面。独立ContinueのSaveは0回。通常Saveは進行側に1回だけ。全92画面は本物の240×160 PPMで、空白画面は0。画像・ROM・Save・runnerそのものはtrackedへ入れず、正式Actionsのartifactに保持する。

内容の意味は実画面と同frameの状態へ束縛した。特に経験値37、キズぐすり使用後の回復、相手1体撃破後の経験値33、Lv6への上昇、次の相手が残っている画面、2回の敗北を区別する。自宅回復後と独立Continue後の手持ち・能力・空バッグの3画面は全byteのSHA-256が一致した。能力画面は経験値204、次のレベルまで32、HP21/21を表示する。観測protocolに存在しないHP/EXP/道具数を架空のRAM観測fieldとして追加していない。

入力の途中にあった行き止まり、待機、敗北、野生からの逃走は削除していない。開発は巻戻しなしの進行core1と保存後の独立core1。正式測定は未受入のこの新区間を別coreで一度だけ再現し、全stdout/Save/画面を開発原本と比較する。正式測定後はその原本を回収し、成功した367入力をもう一度測定しない。118新検査は初回全件成功し、source/evidenceが一致する限りActionsで再起動しない。

## 実装の検証境界

専用oracleは `scripts/pr16_research_story_growth.py`、新検査は `tests/test_pr16_research_story_growth.py`。閉じたkey/observe/save/quit protocolと実行前入力logを対応づける。親Save/candidate/runner/run/artifact、85+7観測、通常Save3→4、同frame実画面、全party600bytes、全Flash128KiB、研究ledger、位置・向き・RP・counterを検査する。

118検査は実原本の陽性を前提とし、トレーナー敗北の勝利扱い、相手1体撃破を戦闘全体勝利とする改変、施設warp、道具/成長/能力画面差替え、coldの保存不一致、追加Save、キー改変、多重キー、JSON重複、boolと整数の別名、終端欠落、host write/fixtureの偽装を個別に拒否する。単なる全記録hash不一致だけを負例の根拠にしない。

今回のcheckpointは必要な再開情報に絞り、過去2690件以上の保護bindingを重複コピーしない。正式source HEADの固定状態JSONとその全byte identity・path件数を参照し、Actions内では全保護ファイルを照合する。検証を省略するための省略ではない。

## 次の再開位置

正式終端確認後の後継名は `growth.srm`。131088bytes / SHA-256 `f36faf0e82cf1c57c8a2c2a5e4bcf30ea6a53432b4d7828c79f1ee2f67cdd8d9`。map3/0 (4,27)、live (11,34)、下向き、自宅前のidle。counter4、Lv6、経験値204、HP21/21、party1、RP0、キズぐすり0。

```text
<fixed-runtime>/ld.so --library-path <fixed-runtime>/lib <checkpoint>/runner <fixed-candidate> <working-save> continue-story f36faf0e82cf1c57c8a2c2a5e4bcf30ea6a53432b4d7828c79f1ee2f67cdd8d9
```

`observe 0` は自動Continueで出力される。追加観測は1から。maskは0/1/2/8/16/32/64/128、framesは1〜600、最後に明示 `quit`。新しい進行が保存条件を満たしたときだけ `save`。この保存から先で通常の準備・野生戦・道具購入・未撃破トレーナーへの挑戦・先の町への進行を行う。過去に負けた相手への成長後の新しい挑戦は進行であり得るが、失敗した入力列を盲目的に再生しない。

道路map3/19の (38,8) ではトモヨとの戦闘、(36,17) では別トレーナーとの戦闘が発生した。後者はパモLv4の次にクヌギダマLv8が残っており、今回の勝利判定に含めない。研究施設への自然到達は未完。旧starter/114入力/301入力/367入力を受入目的で再実行せず、旧RP/UI/BP/P08やリリース判断を開始しない。

## CIと作業範囲

旧P03容量CIのsource hash不一致は `content/modernization/pr16_research_story_route_ci_limit.json` の既知履歴。今回の成功を根拠に一般CI全体を成功へ読み替えない。古いvalidatorを緩めたり旧証拠を更新して帳尻を合わせたりしない。固定引継ぎMDは状態JSONから生成し、両ログはappend-only、最終indexのprivate guardは変更範囲だけ。全体の歴史的private guardが成功したとは主張しない。

## Actions独立測定（この時点では終端確認待ち）

野生勝利1回/逃走1回・キズぐすり1個消費・経験値37+33・Lv5→6・HP21/21・通常Save counter3→4と独立Continueの保持を限定受入。新区間のトレーナー敗北2回、勝利0。次はgrowth.srmのmap3/0 (4,27)、経験値204、道具0から通常ストーリーを進める。研究活動施設への自然到達は未完。旧367入力/301入力/114入力/旧starter/RP/UI/BP/P08を再生しない。

source `52554a9b5eafe8743d87df57a4ba8565237fffae`、run `36358726444`。367入力/85画面とcold38入力/7画面、全stdout・全Save/RTCが開発原本と一致。正式native2/開発native2は別会計。118新検査は原本source一致で再利用し、再実行0。

## 外部確認した成功終端

run `36358726444` / job `108731507916` の全11必須stepがcompleted/success。完了commit `30bf3c2f504153affad487ec1fd4bca4bca1c72b`。artifact `10944976226` は 1303767 bytes / SHA-256 `be09450a6179b40ed1282b11a9f152d33dcb1d0863079d3bbe4b344929d0f0fa`。92実画面、3組の同一UI、3コピーのSave/RTC、固定runner、全commit text原本を照合。上の確認待ちは測定時点の履歴で、現在は終端確認済み。原本は `content/modernization/pr16_research_story_growth_terminal.json`。終端処理のnative/compile/unit再実行0。

次は `growth.srm` を作業コピーにして固定candidate/runtime/runnerでContinueする。map3/0 (4,27)、party1/Lv6/HP21/21/EXP204、RP0、counter4、キズぐすり0。367入力を再生しない。トレーナー2名には未勝利であり、研究施設への自然到達も未完。

## 今回のsourceに対する一般CI

source-validation run36358732448 / job108731524613はfailure。固定artifact10945245745の全byteを回収し、25検査中23成功・2ERROR、原因 `ValueError: tested source changed: overlays/qol_production/qol_production.c` を確認した。当該C・旧validator・旧testは開始HEAD27c36f0から変更なし。後続relearner stepはskipped、対応artifact uploadもfailureであり、成功へ読み替えない。環境パスを含む原本は終端artifact内ci-originalsに全byteを保管し、Git内の識別情報と依存不変の証拠は `content/modernization/pr16_research_story_growth_ci/36358732448/limit.json`。既存CIの自動起動結果を回収しただけで、この収集処理のnative/unit再実行0。

初回終端run36358919647は外部証拠確認に成功したが、CI原本内の環境パスを最終private guardが拒否しcommit前に停止した。guardは緩和せず原本をartifact限定へ移し、未加工原本のhashをGitのmanifestで参照するよう修正。詳細は `content/modernization/pr16_research_story_growth_terminal_recovery.json`。成功した成長測定・118検査を再実行しない。
