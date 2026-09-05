# Private全unit修復 — USER-20260905-PRIVATE-FULL-UNIT

## 状態

直接USER依頼の調査・修正中。完了ではない。基点mainは作業開始時に再取得した `3139b2997eea28d544e7ef9cbe6db16edf7a7781`。Draft PR #2、作業branch `chatgpt/fix-private-full-unit-20260905` に限定する。既存 `USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT` のIN_PROGRESSは変更しない。

## 原失敗の再確認

run 33967241290 / job 101309429531の生ログは1594 tests / failures 17 / errors 41 / skipped 29、1230.020秒。capstone検索は0件。依存関係の推測追加は行わない。

## 最初の修正根拠

- WSL sandbox unitは製品のDrvFS/9p・非UNC・symlink・path長guardを変更せず、OS command境界をmockする。実symlinkはportableなTemporaryDirectory内で作る。negative testは対象エラーメッセージも確認する。
- Stage61のrematch alias追加後にcompile probe側が必須macroを渡していなかった。既存test_stage61_codex_runtime_bootstrapの合成配置と製品builderのmacro定義に合わせる。製品Cの#errorは維持する。
- stateful-menu mGBA testは、製品runnerが既にlinkしているtools/mgba_stage61_rfu_peripheral.cを漏らしていた。実RFU翻訳単位をlinkし、stubは作らない。
- Wikiの検索生成元はspecies 1621/move 1063/ability 312/item 999に、story 12/map 47/battle 77/fixed_capture 117を加えた4248件。追記された253件はtracked Wikiのstory_progression.json、major_battles.json、fixed_capture_encounters.jsonおよびbuild_stage61_wiki.pyの生成ループに存在する。全kindの件数、元ID集合、一意性、既存link/anchor検証を行う。
- normal-save COWはfull契約に加えてCRITICAL_RELEASE_SAVE_AND_CONTINUE要約が追加されている。full辞書の厳密一致を維持し、要約の9キーも全て正本値と照合する。
- build_release.pyは歴史的なv1.4.0 Stage26 acquisition packageの生成器である。旧testだけがv1.3.9 Stage25最終出力を期待していた。Stage25はStage26のinputとしてQOL chainを検証し、Stage26の2035ケース・2process・出力SHAとの結合を維持する。これを現行プレイ基準Stage61や修復候補Stage62へ勝手に同一化しない。

## このcheckpointの検証

ソースsnapshotによるLinuxローカル実行: SandboxPathTests 8件 + Stage61NormalSaveCowMetadataContractTest 3件 = 11件、failures/errors/skips各0件。
初期source-validation run 33971476631はPASS。ただし当該runは最初の調査workflow追加commitの検証であり、その後の修正や全unitの成功を示すものではない。

## 調査の境界

巨大testファイルも実ファイルの差分としてcommitするため、変更前後のSHA-256と一意な置換contextを持つreview済みplanを使用する。専用workflowはprivate・owner・PR #2・同一repo・作業branch・exact HEADを確認し、そのbranchにのみfast-forwardで実ファイルをcommitする。mainへpushしない。テスト読込時のmonkeypatch、失敗抑止、hash検証無効化ではない。

focused診断は4個の既存Private Release ZIPを外側/member hash検証後に復元する。ROM/saveをartifactへ出さず、秘密情報を除いたmetadataと実テスト集計だけを1日保持する。失敗は非zeroで返す。main上のissue_comment制御定義は変更しておらず、PR上の別workflowと区別する。
