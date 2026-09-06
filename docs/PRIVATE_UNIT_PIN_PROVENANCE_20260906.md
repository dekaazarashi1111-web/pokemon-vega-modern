# 2026-09-06 固定sourceと生成fixtureの修復根拠

Task: USER-20260905-PRIVATE-FULL-UNIT-R2

## わざメモリーsource pin

2026-09-03の採択済みcommit `283c945b7e3cacc151252fb17339158b02a0adcf` はfield itemの復帰経路を修正し、`b61207f10a29c2ace6ea58f99e631d65e618f880` は戦闘後も残るbattle flagsをfield-useの可否に誤用する問題を修正した。今回ゲームCやROMは変更しない。

現行 `overlays/move_memory/move_memory.c` のSHA-256は `369f46588477ec7a2a581ec938ccbbab42992ec7cde444ca5920889f5639e1c3`。ContextAllowedFromStateのコメントとbattle_type_flags不使用化だけを逆適用すると、従来pin `ccf816ba5a7fff11a2f370cb90f55846444ccccec5b65fe53f6f8cfbc051b3a5` に完全一致する。

現行 `scripts/build_move_memory.py` のSHA-256は `374dcfc9e40d36f9fd3019c0191d52e278e495760fad666f445fb57d99d30817`。field復帰を説明する3行と生成/検証のitem type 2を4へ逆適用すると、従来pin `579976cacf8b75638e1c053db68ecfe1d4a5a804c8773e5bab11b8658f074c13` に完全一致する。ほかの意味論変更はない。

cyclic decision、party move oracle、mGBA validationの3consumerを同じcurrent sourceへ固定する。2つの逆適用provenance testと従来のsource改竄拒否・実ROM CFG検証を併用する。単に観測値へhashを書き換えるのではなく、変更の全体を既知の二つの修正に限定している。これ自体はstrict全件監査の完了を意味しない。

## T05

旧testは `893768...` cache pathが存在しないと18件をskipした。現行config/id_spaces.jsonの固定baseline pathとROM SHA-256を使用すると17件が成功し、1件はpublished artifactsのsource fingerprintで失敗した。fingerprintにはtest自身が含まれるため、source/test更新後に過去Releaseの生成物とbyte一致する前提は成立しない。

read-only check試験は、固定Vega/CFRU/DPE入力と同じcurrent sourceを独立workspaceへコピーし、実generatorで13成果を生成してから実checkを呼ぶ。全artifact byte一致、check前後hash不変、故意のheader破損の拒否、および元Release成果の不変を検査する。元ROM/saveを上書きせず、入力不足skipを追加しない。

## 最新full-unit基準

run34002188828、HEAD a6e38142faa5b3a9e7578850625aaeb0722a81cbの新規comment full-unitは1721 tests、12 failures、29 errors、28 skipsだった。生ログから全テストIDを取得した。証跡collector run34002313552は検証対象HEADとcollector HEADを別々に記録する。最終全unit/allの完了結果ではない。
