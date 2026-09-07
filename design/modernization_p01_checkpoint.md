# USER-MODERNIZATION-P01 実行checkpoint（2026-09-08）

## 状態

**BLOCKED / 未完了。P02・P03は未開始。通常mergeの条件を満たしていない。**

同工程のDraft PR #14 / `chatgpt/user-modernization-p01-20260908` を継続した。開始mainは `f2d3ed3546f07b4d4aa34ff61de9b9135b19bac2`、継承したP01 HEADは `98081d0ac4bbac38dd99407a2e10ed665165f45f`。他のPRと既存Stage60 IN_PROGRESSは変更しない。

## この実行で反映・確認できたもの

`1a8cb71622850f35e5f62cb2d551cd8f3bcea7a0` で入力台帳、累積候補台帳、限定採用用の正規化ID投影を追加した。このHEADのsource-validation run `34147040199` は成功した。これは既存のP01 validator・再現テストとカタログ生成のsource検証であり、新しい投影契約の全consumer接続、ROM検証、工程全体PASSを意味しない。

Libraryから原本を読み、実測した。

| 入力 | size | SHA-256 | 扱い |
|---|---:|---|---|
| 技習得品質改善版 v1.3.0 (3) | 82683251 | `80b678320c08203e7b39236e5c123f5c2f2f0c729e7f4e5101bed88c84158adb` | ユーザー受領hash一致。ROMではなく習得候補資料。 |
| ID固定・原作復元監査資料 (2) | 67698 | `448608de12a431bef8eaaaf2dc3024743bfd77ad7925e5fb6ae01b6086cfac08` | (3)もbyte同一。復元・進化候補の一括採用はしない。 |

原本ZIP、ROM、saveはGitへ追加していない。Gitへ追加したのはkey/ID・対象集合のdigest・参照先の限定投影だけである。正規化投影は原本照合のための契約であり、現時点では全項目をActions consumerへ接続し終えていない。

## 確認済み不具合

1. `scripts/build_stage61_wiki.py:643` は取得表を `canonical_id` だけで辞書化し、keyの意味を検査しない。manifestのCaterpie649 / Egg412と、旧取得表のCaterpie412 / Egg649を結合すると、同じ件数・ID集合のまま区分が逆転する。既存P01 validatorと現行カタログはこれをkeyで再解決するが、**旧Wiki builderへの現行用接続はまだ未反映**。
2. `vendor/vega_acquisition/generated/acquisition_collection_defs.c` の行412は `{412u, 386u, 1u, 1u, 1u, 0u}`、行649は `{649u, 65535u, 0u, 0u, 0u, 0u}`。headerの順はcanonical_id / ledger_bit_index / completion_weight / route_required / target_class / reserved。`scripts/build_acquisition_events.py:_compile_runtime` がこのC表をコンパイルする接続まで確認した。**現行Stage62 ROMに同じ値が残るかは未検証**であり、ROM不具合と同一視しない。

## 資料不整合

技習得ZIPの1621件決定表ではCaterpie649が `INTERNAL_EXCLUDED, apply=False`、Egg412が `REQUIRED_BASE, apply=False`。Caterpieは全国番号10、reference `swordshield:0010.00` を持つ。Caterpieだけを採用対象へ戻すと対象は1299から1300へ増える。その他のFalse集合は維持する。これは原本解析値であり、1300件のROM反映・Actions受入済みという意味ではない。

Move crosswalkは既存対応806件と未実装候補1件。`MOVE_KEY_ALLYSWITCH` の1063は原作参照ID502とは別物であり、現行Move manifestの0..1062へ直接混入させない。監査資料の205種比較、特性190種・種族値21種・タイプ7種などは候補のまま。

## 意図した独自仕様・保全

Vega独自種、独自進化、ソロ向け進化置換、既存のフォーム除外は本工程で一括変更しない。collection_keyとledger bitの意味を維持し、bitを詰め直さない。過去Stageのconfig/builder/test/Wiki/原本は不変とする。

開発の親は `config/active_play_baseline.json` に明示採用されたStage62。size 33554432 / SHA-256 `d97a0d4a6cd6f8f77a1503a5ac6d473b0e94c4892e3d5a94098497ce35cb6e6f` / CRC32 `73E4FB73` は既存記録の継承で、この実行でROM bytesを再測定したものではない。Stage61 ZIPを親ROMとして採用せず、最大Stage番号を自動採用しない。ROM/save書換とプレイ基準切替は行っていない。

## 容量のsource確認と未確認

manifestはSpecies1621 / Move1063 / Ability312 / Item999 / Type25。既存ID再利用を許可しない。species_surfaceの進化は16slot/種、128byte/種。TM/HM互換bitは16byte/種で、既存Stage61記録は120TM+8HM=128slot。教え技は記録上64slot、表のbit幅は128だが、残り64bitを実consumerへ無条件に追加できるとは扱わない。

取得台帳headerは1216bit / 152byte、完成対象1206。全bitの使用実測は未完了。save_layoutの明示的未使用予約は `reserved_dex_migration` 15byte と `reserved_v2_tail` 129byte。alignment pad、退役領域、未記載RAMの隙間を空き扱いしない。BoxPokemon80byte / party100byte / 14箱×30枠の既存ABIは変更していない。

ROMのallocatable envelopeは integration_modules `0x01200000..0x01600000` と future_tail `0x01F50000..0x02000000`。これは割当可能な外枠であって空き容量ではない。**現行のallocationと同一ROMを使う使用量・進化空slot・消費者pointer実測は未完了**。

## 操作の実応答・環境

- GitHub read / tree作成 / commit / non-force branch更新は実際に成功した。GitHubを読み取り専用とは扱わない。
- 巨大Wiki sourceの `/vega-find` と `/vega-read` はPRコメントbridgeで成功し、旧数値joinと呼び出しを取得できた。
- 原本・ROMの取得先を確認したところrepositoryはpublic、環境資材Releaseは `draft=false`、公開済みだった。名称がPrivateでも非公開ではない。新しい私有資材を公開保管先へ置かず、資材bytesも取得していない。
- 追加実装の更新要求1件はツールから「リクエストの安全性を確認できなかったため、このツールの呼び出しは OpenAI によってブロックされました。」と返された。理由の詳細はない。**その更新はbranchへ反映しておらず、成功・実行済みとして記録しない**。同じ拒否内容を別経路で迂回していない。
- チャット実行環境のGitHub raw取得もDNS解決エラーだった。個人PCを探索していない。ビルド・テストはActionsを使用する。

## 再開順序（P01の範囲内）

1. 最新PR HEAD・main・CIを再取得する。入力台帳とStage62親hashを維持する。
2. 正規化契約を全Species/Move/Ability/Item/Formの現行consumerへ接続し、同数のkey入替・旧ID・除外フォーム混同・内部枠混入を失敗させる。契約の全採用を示す未検証フラグを追加しない。
3. 固定Wikiを上書きしない現行用生成経路を実装する。取得C表の訂正は元collection_key→bitを維持する別生成物とし、既存ROM/saveに適用しない。
4. 非公開であると実確認できる入力保管・runner復元経路を確立し、同じStage62 bytesでROM側の残存とconsumer接続を測定する。必要なROM修正はclean ROM起点・配置・validator・決定的生成・mGBA・差分往復のgateを追加してから行う。
5. focused/gatesを最終HEADでPASSさせ、run/versionログと候補台帳を更新する。全受入未達ならBLOCKEDのまま。P02進化条件整理とP03原作習得全反映は別工程として未開始を維持する。
