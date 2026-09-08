# Modernization引継ぎ

最終更新: 2026-09-08

この文書は`USER-MODERNIZATION-P01`からP08までの累積候補、検証済み境界、未実装境界を示す入口である。機械可読の候補identityは`config/modernization_candidate.json`、入力原本は`config/modernization_inputs.json`、現行プレイ基準は`config/active_play_baseline.json`を正とする。

## 現在位置

- 現行プレイ基準はStage62のまま。開発中の最大StageをiPad、通常save、Codex対戦へ自動採用しない。
- P01はDONE。Stage63はEgg 412／Caterpie 649の意味逆転をstable keyで修復し、ROM SHA-256は`6642602d33e1e074c20afebfc649846f0aaf106c2455f2ca212a4f427ec74fbd`。
- P02はStage64のRayquaza 2-byte修正に加え、Stage66上のin-memory overlayで6種のlevel＋所持道具分岐順を60 bytes修復した。実consumerの成立／不成立／道具消費を独立2 processでPASSしたが、通常UI cancel、bag、scene後特性/form、save/reloadを含む全受入は未完了。
- P03はStage66 bulkを継承し、Stage67 consumer checkpointまで進んだ。Stage67 ROM SHA-256は`13e4ecb6f2bc72eeb5d7ffb5b5e5a7a2ae2876391bf37ec93cb6548587265111`、CRC32は`D94758FF`。core checkpoint commitは`b4bdb67fcb9c49414661b2c591e0b1d9464aeafe`。
- P04の取得系checkpointはStage69まで進んだ。Stage68は45 Mega Stoneを全16 BPの専用店へ接続し、exact-ROM gateをPASS。Stage69は既存ID 1029のえいえんのはなフラエッテをLv.50で配布する。Stage69 ROM SHA-256は`6532002dabd3197ee6b8ded8b153a495d3241acf062fc931210987093172cb95`、CRC32は`4849DD0F`。
- P04のSpecies固定表checkpointはStage70、Mega対応checkpointはStage71まで進んだ。Stage70でMega用49形態をSpecies ID 1621〜1669へ追加し、28固定表・49組の画像素材・Species上限consumer、318行のAbility固定4表を接続した。Stage71で49 forward＋49 reverseをevolution表へ追加し、既存Mega 80行を保持した。Stage71 ROM SHA-256は`dbcc1194511f234c7d34c196082d59bfc0cb6aca6bb3b9c0f911bc8add4230bb`、CRC32は`426A7A7F`。P08のselected candidateへは未統合である。
- P04〜P08は依然として未完了。Stage71は49 Megaの順逆表と既存engine契約までのcheckpointで、新Ability効果と最終累積mGBAはrelease readyではない。P01以外をDONEと扱わない。

## P03 Stage67の採用境界

提出された118,528経路と全1,300対象をstream検証した。サイドチェンジ159経路を明示非採用としたruntime選択集合は118,369経路で、実consumerへ安全に結べる51,151経路を累積実装した。

- Stage66継承: level-up 18,515＋既存machine slot 29,033の47,548経路。
- Stage67追加: evolution 341、既存tutor slot 740、通常egg 2,522の計3,603経路。egg consumerに残っていた第2旧rootと旧走査上限も同時修復した。
- 選択済み保留67,218: machine 26,279、tutor 369、egg条件／alias衝突41、shared egg 5,023、pre-evolution carry 35,141、reminder 295、form change 70。
- サイドチェンジ159経路は未実装残件ではなく`NON_ADOPTED`。Move 1063を割り当てず、既存技への近似置換もしない。将来採用時は別decisionで全経路を再選択する。
- P02 overlayから46,455 bytes変更、4,343 spans、宣言外変更0。Stage66からはP02の60 bytesを含む46,515 bytes差分。追加payload後の`future_tail`末尾残量は62,510 bytes。
- mGBAはStage67で追加した全evolution 341、tutor positive 740＋negative 290、normal egg 2,522を独立2 processで実consumer実行した。scheduler、breeding、4枠満杯、save/reloadは未検証なのでP03完了ではない。

## P04の素材・取得経路・容量

- 追加予約はMega用Species/Form 49件（1621〜1669）、Item 45件（999〜1043）、Ability 6件（312〜317）。通常SpeciesとMoveの追加は0件で、現行Move最大ID 1062を維持する。Item 45件はStage68、Species/Form 49件とAbility固定表はStage70 ROMへ反映済み。Ability効果はStage72まで仮文言・差し替え可能キーのままとする。
- Mega 49件とMega Stone 45件は固定commitの外部sourceからprivate-use stagingへ再現可能に変換した。49/49 species palette、45/45 stone asset、670 payload files、426,648 bytes、asset-set SHA-256 `462fed5d292582f44a29007e2da488829973c57b1964f86fa12e6da41c6e749c`。
- Tatsugiri Droopy／Stretchyは同じupstream共通Mega paletteが正本であり、欠落扱いを解消した。
- Winds/WavesのBrowt／Pombon／Gecquaはユーザー指定により現行採用対象から外した。3/3とも`NON_ADOPTED_USER_SCOPE`としてID予約、容量予約、素材生成、runtime接続を0件にし、公式由来の候補来歴だけを将来再採用用に保持する。
- フラエッテ（えいえんのはな）のメガシンカ前形態は追加IDではなく、既存Species ID 1029／`FORM_KEY_FLOETTE_ETERNAL`を使う。Stage69でmap `96/5` local 15のNPCからMega Ring所持時にLv.50を1save1回配布する経路を追加した。手持ちとPC受取、form flag `0x14CD`、National 670の既存collection bit 850はexact ROMでPASS。全満・rollback・fresh reloadはhost PASSのみで、exact release gateはpending。
- Stage68はmap `96/5` local 14に既存Factory BPと分離した専用店員を追加。45石全て16 BP、Mega Ring 580で解禁、`0x14A0..0x14CC`の個別flagで1save1回購入とする。Item表を999→1044行へ拡張し、CFRUの12 consumerで1043受理／1044拒否を保証した。exact mGBAは代表3石、保存・fresh reload・二重購入拒否、BP不足／bag満杯無変更をPASS。
- Stage70は1形態の縦切り後に49形態を展開し、front／back／palette／shiny／iconを含む28固定表を再配置した。既存Species 0〜1620とFloette Eternal 1029は全対象表でbyte一致。evolution表は`0x094FE8E0`、1,670×128 bytes、39ポインターconsumerとし、新49行はStage71所有のzero予約。Ability descriptionの`root >> 2`派生参照3コピーと312上限3コピーも318行へ再接続した。
- Stage71は同じevolution表へ49件のbase＋専用Mega Stoneの順方向行と49件のMega→base逆方向行を追加した。既存Mega 80行はbyte保持し、98行の許可784 bytes中383 bytesだけを変更、許可外変更0。Stage70 allocation #73の全850,544-byte slice hashだけを更新し、非対象73 allocationのledgerとROM sliceは不変、overlap 0。
- Mega可否は既存実装の`project mechanic policy → mode別keystone → exact stone → usage mark`順を維持する。通常戦はMega mode設定後もMega Ring 580が必要、Frontier／Linkは既存Ring例外を使う。通常の同一ownerは1戦闘1回、交代ではMegaを維持、ひんしでは`TryFormRevert`によりbaseへ戻るがusage doneを維持するため蘇生後の再Megaは不可。Mega Brawlとproject側side-used gateの厳密な相互作用は、Stage72後の最終mGBA 1回へ保留する。
- 外部source rootにlicense fileがないため、生成素材は`userfile/generated/modernization_p04_assets`のGit管理外・個人private利用限定。GitHub private environment bundleからも明示除外する。
- Move固定表を増やさない34固定表の拡張見積りは616,521→636,378 bytes（+19,857、aligned bundle 636,392）。`integration_modules`残1,124,296 bytesだが、Item 1024以降の10-bit consumer、公開event 88→89 bit、legacy Ability u8、save item bitmap 125→131 bytes、全表relink/migrationは未実装。
- 容量manifestのP04本体試算はStage65基準。Stage67の追加はP04の`integration_modules`候補と非重複で、`future_tail`末尾残量は62,510 bytes。

## P05〜P08の境界

- P05の新Move要件は0件。Side Change／Ally Switch候補159経路は非採用decisionへ固定し、効果・AI・UI・アニメーション・save・習得を要求しない。技性能の提出済み採用差分は0。
- 新Ability 6件はstable key順ID 312〜317とu16 ABIを固定し、発動／不発／抑制／複数対象／AI／save、Fairy 23／Stellar 24を含む46 caseを独立2 processのhost C runtimeでPASSした。Stage ROM hook、固定表relink、6 Mega form binding、日本語文言、exact-ROM mGBAは未完了。
- 公式特性が不明な対象は、stable replacement key、`TEMPORARY_REPLACEABLE`、非公式表示guardを持つ仮特性14件として保持した。分類保留2件を含め、後から中央bindingだけを差し替えられる。
- P06の提出済み種族調整差分は0、P07の追加習得差分も0。review-only資料を自動採用していない。
- P08は上記checkpointのhash、生成実装、ignored ROM/BPS、evidence sourceを統合監査する。active baseline Stage62、P01のみDONE、P02〜P08未完了、release-ready=falseを維持する。

## 入力・GitHub・権利境界

- 受領ZIPは`userfile/imports/modernization_p01/`の読取専用原本で、Gitへ追加しない。複製番号ではなくsize／SHA-256／内部member identityで照合する。
- 2026-09-08、`private-environment-v1`を置いたrepositoryが誤ってPublicだったことを実APIで確認し、ユーザー指示によりrepository全体をPrivateへ変更した。Release 5資材は削除せず保持した。
- private資材を読む全GitHub workflowは、GitHub APIの`.private == true`をdownload前に必須確認する。repositoryが将来Publicへ戻った場合はfail closedする。
- P04外部素材は既存private Releaseへ追加していない。root license不在のため再配布可能とは扱わない。

## 最小の再検証入口

同一入力hash・同一実装HEADの重い検証は再利用し、変更に直結するcheckだけを選ぶ。

```bash
python3 scripts/build_modernization_mega_shop.py --check
python3 scripts/run_modernization_mega_shop_mgba.py check
python3 scripts/build_modernization_floette_gift.py --check
python3 scripts/build_modernization_p04_assets.py --check --compact
python3 scripts/build_modernization_p04_capacity.py --check --compact
python3 scripts/build_modernization_p04_species_runtime.py --check
python3 -m unittest tests.test_modernization_p04_species_runtime
python3 scripts/build_modernization_p04_mega_runtime.py --check
python3 -m unittest tests.test_modernization_p04_mega_runtime
python3 scripts/build_modernization_p05.py --check
python3 scripts/build_modernization_p05_ability_runtime.py --check --compact
python3 scripts/build_modernization_p07.py --check
python3 scripts/run_modernization_p02_acceptance.py check
python3 scripts/build_modernization_p03_stage67.py check
python3 scripts/run_modernization_p03_stage67_mgba.py check
python3 scripts/build_modernization_p08.py --check
```

Stage67をclean private環境から作り直す必要がある時だけStage67 build／mGBA runを使う。全repository unitと同じ実mGBA chainを毎回重ねない。

## 再開順

1. P02の未検証UIキャンセル・bag・scene後特性/form・save/reloadを実consumerで閉じる。
2. P03の67,218選択済み保留経路をconsumer別に小分けし、供給方針と実ROM testを付けてStage67へ積み上げる。Side Change 159件は対象外のまま保持する。
3. Stage71の49順逆Mega対応を入力に、Ability 6件の効果／AI／UIをStage72 ROMへlinkする。公式特性未判明の形態はreplacement key付き仮特性を使い、中央bindingで後から差し替える。新Move 1063は実装しない。
4. Stage72後の最終累積mGBAで、49 Mega代表、通常／Frontier／Link／Mega Brawl、交代／ひんし／終了と新Ability代表を1セットだけ検証する。
5. 提出済み採用差分が入った場合だけP06/P07を実装し、最後にP08 release gateを再評価する。

どの再開点でも、過去Stage、原本ZIP、既存saveを上書きせず、候補Stageを現行プレイ基準へ自動昇格しない。
