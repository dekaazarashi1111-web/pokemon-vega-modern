# Issue19: 後継候補の技習得Wiki

候補 `6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2` / 33554432 bytes / CRC32 `00F31AF7`。

新Wiki `docs/wiki/issue19-candidate-6e88a021`。4932 files / 380550774 bytes / 1671 owner / 1063 Move ID / 128389採用経路。tree SHA-256 `b153f51d26db955427ce4f29df341556ee0ea02143394a64b9ae4d8d430f53fe`。旧Wiki4148 filesは不変。

## 検証と記録の分離

run35756623313、source `b8f8585da8c34652dd4fc59fec537f4c2e04df1c` の生成stepは成功。新28+registry8=36試験、独立2生成一致、読取check byte/mtime不変、全採用行の原本hash/consumer span結合を確認。run全体は過去の失敗ログの実行機パスをguardが検出してfailure、push未実行のまま保持する。原本artifact10708767213は改変しない。

当回は採用sourceを変更せず同一treeを1回materializeして失われたrunner出力を復元し、追跡証拠には原本hashと結合した伏字・末尾空白除去viewを保存。36試験/独立2生成/checkは再実行0。新しい公開view10試験と最終guardを検証する。成功treeのtext ZIPもartifactへ保存し、後続で重複生成しない。

## 保持した境界

Side Change159非採用経路103種の履歴を保持しactive0。非学習188 owner、carry35211行、条件付きタマゴを直接付与へ平坦化しない。placeholder0、所有者overlay0。旧ARM/PLA1/PLC2/native/原本採取の再実行0。ROM変更0、BP/P08/baseline不変。これは技習得Wikiだけの受入で、種族値・特性・技効果・物理供給・Issue18の再受入ではない。

正本 `content/modernization/pr16_learnset_wiki_checkpoint.json`。当回publish source `98ee079d413e7099c0f18db09987b71c23839cc5` / run35757877294。run全体の完了は後続の記録限定照合で確定する。

## 次の未完

Issue19: 候補6e88a021のWiki/原本結合は保存checkpointを継承し再生成しない。次は変更影響のBag通常入口、殿堂入り前後、raw40ページ選択/取消、習得選択、戦闘、通常Save/fresh Continue。Floette12追加技の実供給は未受入。旧4hook直接診断/ARM/PLA1/PLC2/旧Wikiを再実行しない。
