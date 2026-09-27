# PR16 通常NewGameからの自然進行

## 作業中の境界

開始HEADは `a088b40b023a4f6471538ddb5885e42c6d76529a`。固定再開MD/JSONが指定する次工程は、通常NewGame/ストーリーから研究活動・研究所への自然到達である。既存のbadge/map/party/屋外warp fixtureは自然到達に読み替えない。

現在は専用のキー入力protocol runnerを実装中。位置、party、RP、保存counter、全Flash/party/台帳hash、同一frameの画面、全入力を記録する。7個のhost write APIを最初のゲームframe前に拒否へ置換し、fixture・直接native call・CPU register変更・進行注入を実行しない。

## 原本の再利用

- 自然稼得RP支出・最終shop UI候補 `e1efb1009c6e6b0ec4967bf7b20562d2330bbd933f64f7f7863cdad56eb1f842` を保存recipeのbyte差分だけから復元する。ARM再コンパイルや旧build/native matrixは実行しない。
- 固定mGBA runtime artifact `10898620034` と親candidate artifact `10898510128` をarchive SHA-256と展開後identityで検証する。
- 通常NewGame原本 `36250444503` のartifact `10907984892` にはセーブ本体がない。旧初回Save/独立Continue2回の受入テストを再実行せず、未完の進行へ到達するために消去Flashから既存233区間を前提入力として使う。これを新規NewGame受入件数に加算しない。
- 古いNewGame runnerは表示受入を含まない。今回の最初の診断ではvideo接続がreset後だったため2枚が黒画面となった。保存0、party0、自然到達未受入の診断原本として保持し、video bufferを最初のreset前へ接続する専用openerへ修正する。ゲームROMの欠陥と断定しない。

## 禁止事項と次の処理

成功した未完区間のsaveと全input traceを保持して続きへ進む。同じ成功稼得/購入/旧数値/標準リスト/入口/BP/P08を変更影響なしに実行しない。新しい独立oracle、注入拒否検査、表示確認、変更箇所だけの検証を追加する。受入範囲と残件は完了checkpointへ記録し、固定再開JSONからMDをrenderする。merge/release/active baseline変更は行わない。

本commitはWIPで、自然到達完了や新規native受入を主張しない。
