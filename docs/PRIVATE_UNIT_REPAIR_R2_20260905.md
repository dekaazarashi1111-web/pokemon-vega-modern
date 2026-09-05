# Private全unit環境の修復（R2・作業中）

Task: `USER-20260905-PRIVATE-FULL-UNIT-R2`

基点は開始時再取得したmain `3139b2997eea28d544e7ef9cbe6db16edf7a7781`。既存の同名ブランチ/PR #2を上書きせず、`chatgpt/fix-private-full-unit-20260905-r2` / Draft PR #3を作成した。既存Stage60監査タスクのIN_PROGRESSは変更していない。

## 生ログの独立確認

元run `33967241290` / job `101309429531`を、監査run `33975817811`が認証付きAPIで再取得した。直接connector取得のUTF-8デコードエラーとは別の経路で、gzip/plain両方を厳密に扱う。

観測値は1594 tests、1230.020s、17 failures、41 errors、29 skips、capstone 0件。厳密なunittest見出し58件とskip見出し29件も集計と一致。元byte SHA-256は `8eefbe29075cc80f9c14dd22852d13922ac1837a0d1b0b479e71b79fba6620be`。任意の例外本文、subtest値、絶対path、生ログ本文は出力しない。source-validation run `33975817577`もPASS。

## 第1修正群の根拠（最終all未検証）

PR #2に存在していたWIPのうち、取得したsource artifactの外側SHA-256と全member SHA-256を検証し、ソースを再確認した以下の変更だけを採用する。旧WIPのworkflow、自動commit機構、診断script、修正計画は採用しない。旧PRをmergeしたものではない。

- SandboxPathTestsはfindmnt/wslpathの境界をmockし、実際のtemp symlinkで親リンク拒否を検証する。実装のDrvFS/9p/UNC/非ASCII/長さ/ACL保護を緩めない。追加のext4拒否も検証する。
- packetのGit祖先確認は独立したtemp Git履歴で検証する。正の祖先、shallowで証明不能、存在しない固定commitの負例を持つ。実装の祖先検証は変更しない。
- CLI抽出テストは無視対象のユーザーproject.tomlを要求せず、追跡済みproject.example.tomlと固定reference/charmapをtemp rootへ配置する。
- population validatorは欠落/壊れた物理map inventoryを未捕捉例外ではなく検証エラーとして返す。不備を成功へ変えず、負例を追加する。manifest単体fixtureはpopulation依存を明示的に分離する。
- ARM compile probeは現行Cソース95–102行の必須rematch aliasマクロを供給する。値は既存compile fixtureとbuilderの同じABIに従う。#error、警告エラー化、生成物検証は残す。
- stateful-menuのCリンクは既存mGBA RFU peripheral実装を追加する。機能をstub化しない。
- normal-save COWの完全契約とcritical-release向け9キー要約は別の正当な宣言。完全契約一致と要約の正確なキー集合/各値の一致を両方検証する。
- Wiki正本の検索indexは4248行。species1621、move1063、ability312、item999、story12、map47、battle77、fixed_capture117。追跡済みindexのSHA-256は `91869efc87e6981ab9ded7b09cb7ed82ee5ca747234a6e6c0dca2d75476b076f`。旧3995という総数だけでなく、種別件数・生成元ID集合・重複禁止・全リンクの存在を検証する。
- release builderの正本はVERSION 1.4.0、Stage26 acquisition package。Stage25 QOLとStage26 acquisitionの異なるROM identityを混同せず、各fixtureを各入力/出力へ結び付ける。これは現行プレイROM/CLIをStage26へ変更する意味ではない。
- Stage60 save fixtureは既存生成元、既存provenance、固定save hashを維持し、2つの独立mGBAプロセスで決定的に生成する。既存saveの不一致・symlinkは拒否し、上書きしない。save byteや生成reportはGitへ入れない。

ローカルの純粋unit選択20件はPASS。監査15件と新しい結果集計器7件もPASS。vendor/ROMを必要とするunitは、source-onlyの手元環境を根拠にPASS扱いしない。新規private-focused workflowはexact PR HEADをcheckoutし、従来のPrivate Release 4 ZIP外側/member検証をそのまま使用する。任意の実行出力は破棄し、許可した失敗識別子/ソース行番号と実数だけをartifactへ出す。

## 未完了

58件の全修復、toolchainのpackage/ABI検証への移行、古いStage09/Stage61生成証跡、private registry入力、全unit skip全件の解消/正当性分類、最終full-unit/allは未完了。現在のWIPを完了commitや全PASSとして扱わない。Stage62 ROMの実行前後hashを照合するが、それだけでStage62 check/mGBAを実施済みとはしない。

mainのissue_comment制御は変更していない。PRイベントの追加workflowとmain制御の実証は区別する。リポジトリのpublic化、main直接commit/merge、端末操作、ゲーム/ROM/saveのcommitは行わない。
