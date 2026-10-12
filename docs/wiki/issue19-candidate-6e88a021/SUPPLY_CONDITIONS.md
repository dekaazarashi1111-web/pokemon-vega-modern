# 実装表・原本条件・未受入範囲

候補 SHA-256 `6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2` / 33554432 bytes / CRC32 `00F31AF7`。

[Wiki入口](README.md)

基準行は公式1299件とVega181種の保存原本、および明示owner binding/Floette差分から投影しました。原本の再採取はしていません。

machine/tutorの適合bitは入手可能性を意味しません。追加archiveは殿堂入りflag0x082Cが必要です。machineは**既習得4技を除く前に40行ずつ**区切り、mode3..6、tutor追加はmode7です。mode0/1は既存経路へ委譲、mode2はprobeです。特殊Tutor152..160は通常slot0..63ではなく、従来の個別条件を保持します。

**直接ROM4hook/28owner/独立2processの受入を継承していますが、このWiki生成はnative再受入ではありません。** Bag通常入口、殿堂入り前後、ページ選択/取消、習得選択、戦闘、通常Save/fresh Continue、Floette12追加技の実供給は未完です。初期fixtureやsource/span照合を通常操作へ読み替えません。

進化前/姿変更からの持越し参照は直接習得表ではありません。非直接Vegaタマゴ2394行も直接・共有付与へ変換しません。Side Change159経路103種は非採用原本を保持しactiveから除外します。placeholder0、owner_approved_overlay0です。

このWikiは**Issue19の技習得に限定した調整用スナップショット**です。種族値・特性・技効果・道具供給・Issue18残監査は旧Wiki/各正本を参照し、このWikiで再受入したとは扱いません。製品全体、clean-ROM2生成、release、baseline切替、mergeは未承認です。
