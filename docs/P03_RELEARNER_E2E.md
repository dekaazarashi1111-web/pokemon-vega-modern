# P03 通常思い出し・タマゴ技の実操作／保存検証

対象は Stage82 候補 `e9dcb375168c92cb4390aaf390b8278dbf08867dd7dc3b834561799ae021710d`。製品ROMを変更するパッチではなく、従来のマシン／教え技・繁殖・容量境界とは別の未検証経路を通す試験です。

## 対象46ケース

| 経路 | 件数 | 確認条件 |
| --- | ---: | --- |
| 通常思い出し | 17 | 満杯4枠の各入替、空き枠3配置、拒否・一覧キャンセル・入替画面キャンセル、習得レベル未満、既習得除外、専用reminder表4例、殿堂入り後 |
| タマゴ技 | 29 | exact-egg対象7種の先頭・末尾、全4枠の入替、既習得除外、拒否・キャンセル、ハーブ＋空き枠3配置、ハーブ非消費、DH未達・ハーブなし・満杯の拒否、候補なし |

通常思い出しの専用表は、キノガッサのキノコのほうし、メタグロスのだいばくはつ、ナッシーのせいちょう、ピクシーのミストフィールドを含みます。タマゴ技のexact-egg対象はケンタロス、ラプラス、ピンプク、ルリリ、リーシャン、ウソハチ、ゴンベです。種族・技IDは既存manifestと候補ROMの対応のままで、新規採用や配布変更ではありません。

各ケースで通常バッグ→わざメモリー→手持ち→一覧／入替画面を入力で進めます。拒否ケースでは対応する既存の日本語メッセージを完全一致で観測し、習得画面へ入っていないことも確認します。全ケースに通常Startメニュー保存、元core破棄、新規coreの通常Continueがあります。

PPアップの2ビット×4枠を検査し、入替先だけの効果を消去し、他枠は保持します。技ID・現在PP・PPアップ量・レベル・種族・解禁フラグ・ハーブ個数を確認します。保存前後と新規Continue後の手持ち個体100バイト全体も比較し、PID・個体データなどの未指定部分の破壊を検出します。ハーブは既存仕様どおりバッグの所持数を検査し、所持アイテムへの置換はしません。

## 期待値と観測の分離

`tests/fixtures/p03_relearner_cases.json` は固定候補ROMの既存表から作った明示的な期待値です。通常のレベル技はROMルート `0x0804346C`、専用reminderとexact-egg/sharedの表は `generated/runtime/modernization_p03_stage73_consumer_runtime_symbols.json` によります。候補の生成関数を実行して、その出力を期待値として再利用する方法は使いません。

実際の一覧で候補数、全候補ID、選択個体番号、項目と技名のポインタ・文字列、キャンセル項目を照合します。既知技と重複の除外も確認します。今回の7種はexact-eggとshared表の重複を除去する経路であり、その他の種族のshared-only供給を網羅したという意味ではありません。

準備段階では個体・技・PPアップ量・道具・解禁フラグを設定します。UI・保存・新規Continueの各観測区間で、7種類のmCore書込みAPIを失敗終了に置換します。観測中は入力とフレーム進行のみです。区間後の状態照合は既存のGetMonData等で行い、次の観測前に再び書込みを禁止します。自然な捕獲・解禁・道具取得の検証とは区別します。

## 実行

```sh
python3 -m unittest discover -s tests -p test_modernization_p03_relearner_e2e.py -v
python3 scripts/run_modernization_p03_relearner_e2e.py --jobs 2
```

省略時は既存の厳密な生成器でStage80→81→82を再現します。`--rom /path/to/stage82.gba` は同じ固定SHA-256のROMに限って受け付けます。元ROM・seed・ソース・プレイ基準は変更しません。出力先は `.local` 以下の専用ディレクトリだけです。`--output-directory .local` 自体はseed保護のため拒否します。

固定環境では次を使用します。

```sh
bash infra/setup_github_actions.sh --check
python3 scripts/run_modernization_p03_relearner_e2e.py --require-fixed-toolchain --jobs 2
```

専用workflowは通常CIを上書きせず、ソース変更時またはworkflow_dispatchで実行します。GitHub既定の固定toolchainを実際に検査し、独自include/library overrideも拒否します。固定検査なしの実行結果は、成功しても `LOCAL_DIAGNOSTIC` です。固定検査を通しても `FIXED_TOOLCHAIN_EXECUTION_NOT_YET_P08_ACCEPTED` であり、P08への原本統合・受入とは別です。

stdout・stderr・終了コード・タイムアウト／起動失敗を各ケースごとに保存します。全46ケースが正しい結果と経路で終了した場合だけ `result.json` を作成します。開始時に古いPASSを無効化し、不正JSON・重複キー・bool型終了コード・警告・経路順序の欠落・別ケースの結果流用を拒否します。合成JSONの回帰テストを実ROMの成功件数へ加算しません。

## 受入上の範囲

これは通常思い出し・代表タマゴ技のUIと保存経路の検証です。技忘れ、その他の習得・フォーム・進化経路、全種族の供給、archive economyの正式採用、P05の自然な取得・Battle Circus入場、P06/P07、最終リリースを完了扱いにしません。Stage62の実プレイ基準と実プレイセーブ、過去の成功原本、PRのDraft状態、`release_ready=false` は変更しません。


## 2026-09-10 — USER-P03-RELEARNER / 固定環境46経路の原本受入

Actions run 34446029812、source HEAD 3c894515d6d73a21fde48228853eef38501933ef、GCC 13.3.0 / mGBA 0.10.2で通常思い出し17件とタマゴ技29件の全46件をPASS。新規46プロセス・92 core、キャッシュ0。全ケースで通常保存、新規coreの通常Continue、個体100byte・技・PP・PP Up・解禁フラグ・ハーブを検証。ホスト書込7 APIの実拒否も確認した。

原本175ファイルのZIP（93814 bytes、SHA-256 ba584a0a5e393a08f1b7a3202945faa4c3e129f91a0d35f2ace6c78f56a960ed）、Actions run/jobs/artifactの取得原本、26入力ソースhashを照合し、56 runtime契約テストと24原本改変テストの計80件をPASS。受入先は content/modernization/p08_p03_relearner_acceptance.json、証跡先は content/modernization/p08_relearner_evidence/34446029812/。検査のみのコマンドが証跡内容・mtimeを変更しないことも確認した。本統合は新規mGBA実行0件。

試験開始前の個体・道具・フラグは隔離fixtureであり自然入手の受入ではない。Stage82 ROMは変更0byte、Stage62基準と実プレイsaveは不変。全P03/P05・最終releaseを昇格しない。並行P06/P07の採用状況はこの試験から判定せず別管理とする。既存全index guardのROM/save・過去path違反は残し、今回の差分indexで同じguardをPASS、全体の違反出力が親と変わらないことを確認してcommit/pushする。

Integration run: 34446703839; integration source: 43a9a22fac95538d17a36cc7ced5ace62c80a81a.
