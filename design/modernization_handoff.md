# Modernization引継ぎ

最終更新: 2026-09-09

この文書は`USER-MODERNIZATION-P01`からP08までの累積候補、検証済み境界、未実装境界を示す入口である。機械可読の候補identityは`config/modernization_candidate.json`、入力原本は`config/modernization_inputs.json`、現行プレイ基準は`config/active_play_baseline.json`を正とする。

## 現在位置

- 現行プレイ基準はStage62のまま。開発中の最大StageをiPad、通常save、Codex対戦へ自動採用しない。
- P01はDONE。Stage63はEgg 412／Caterpie 649の意味逆転をstable keyで修復し、ROM SHA-256は`6642602d33e1e074c20afebfc649846f0aaf106c2455f2ca212a4f427ec74fbd`。
- P02はStage64のRayquaza 2-byte修正に加え、Stage66上のin-memory overlayで6種のlevel＋所持道具分岐順を60 bytes修復した。実consumerの成立／不成立／道具消費を独立2 processでPASSした。Stage71累積ROMの全受入は2回とも通常UIの製品判定前にハーネス側で停止したため、production runtimeを`UNJUDGED`、全受入をpendingに保った。次回は既知正常saveをprocess別に私有コピーし、通常Continueでinput-ready fieldへ到達後だけfixtureを置くハーネスを使う。追加mGBAはStage72後の累積runへ集約する。
- P03はStage66/67 bulk、Stage73 consumer runtime、Stage74 direct supplyを継承し、Stage75 Own Tempo Rockruff checkpointまで進んだ。Stage74でmachine 26,279＋tutor 369の26,648経路をfamily分離archiveへ接続して直接供給残を0にし、Stage75で0744.01の欠落owner 38経路を内部条件フォームSpecies 1670へ解決した。Stage75 ROM SHA-256は`a179c024294f4f1bbf34eb603af255f6896265d9d8523344719b349f8a4495c3`、CRC32は`1511F429`。この継承chainはStage76のP08 selected candidateへ統合済みである。
- P04の取得系checkpointはStage69まで進んだ。Stage68は45 Mega Stoneを全16 BPの専用店へ接続し、exact-ROM gateをPASS。Stage69は既存ID 1029のえいえんのはなフラエッテをLv.50で配布する。Stage69 ROM SHA-256は`6532002dabd3197ee6b8ded8b153a495d3241acf062fc931210987093172cb95`、CRC32は`4849DD0F`。
- P04のSpecies固定表checkpointはStage70、Mega対応checkpointはStage71まで進んだ。Stage70でMega用49形態をSpecies ID 1621〜1669へ追加し、28固定表・49組の画像素材・Species上限consumer、318行のAbility固定4表を接続した。Stage71で49 forward＋49 reverseをevolution表へ追加し、既存Mega 80行を保持した。Stage71 ROM SHA-256は`dbcc1194511f234c7d34c196082d59bfc0cb6aca6bb3b9c0f911bc8add4230bb`、CRC32は`426A7A7F`。Stage76までの継承chainとしてP08へ統合済みである。
- P05のAbility ROM checkpointはStage77まで進んだ。Stage72のAbility 312〜317／29 battle hookとStage76の安全な3 edgeを継承し、Battle Circusの全特性無効時だけ29 hookをStage72 original trampolineへ迂回させた。通常時はStage72 wrapperを維持し、Gastro Acid／Neutralizing Gas／Mold Breakerの既存抑制も変更しない。Stage77 ROM SHA-256は`245133a4740dda9faa0663d321505ee793293d64b0b318d601fd91933b84973f`、CRC32は`F1CE0EAC`。Eelevate専用switch AIとmGBAは未実行で、P08 selected candidateは次の統合checkpointまでStage76を維持する。
- P04〜P08は依然として未完了。Stage75でOwn Tempo Rockruff 0744.01、Stage76でP05の安全な3 edge、Stage77でBattle Circus特性無効境界は解決済みだが、Eelevate専用switch AI、P02通常UI／Floette full・fresh reloadを含む最終累積mGBAが残る。P01以外をDONEと扱わない。

## P03 Stage67の採用境界

提出された118,528経路と全1,300対象をstream検証した。サイドチェンジ159経路を明示非採用としたruntime選択集合は118,369経路で、実consumerへ安全に結べる51,151経路を累積実装した。

- Stage66継承: level-up 18,515＋既存machine slot 29,033の47,548経路。
- Stage67追加: evolution 341、既存tutor slot 740、通常egg 2,522の計3,603経路。egg consumerに残っていた第2旧rootと旧走査上限も同時修復した。
- 選択済み保留67,218: machine 26,279、tutor 369、egg条件／alias衝突41、shared egg 5,023、pre-evolution carry 35,141、reminder 295、form change 70。
- サイドチェンジ159経路は未実装残件ではなく`NON_ADOPTED`。Move 1063を割り当てず、既存技への近似置換もしない。将来採用時は別decisionで全経路を再選択する。
- P02 overlayから46,455 bytes変更、4,343 spans、宣言外変更0。Stage66からはP02の60 bytesを含む46,515 bytes差分。追加payload後の`future_tail`末尾残量は62,510 bytes。
- mGBAはStage67で追加した全evolution 341、tutor positive 740＋negative 290、normal egg 2,522を独立2 processで実consumer実行した。scheduler、breeding、4枠満杯、save/reloadは未検証なのでP03完了ではない。
- Stage73は上記5群40,570経路のconsumer境界をROMへ接続した。新規materializationはalias／incense衝突7種のexact egg 40、shared egg 5,023、reminder 295、ロトム5 form moveの計5,363。既存owner照合はPichu＋Light BallのVolt Tackle 1、pre-evolution 4技保持35,141、generic form保持61、固定form transition 4の計35,207。通常／共有技候補は40枠内で最大28／19、drop 0で、Browt／Pombon／Gecqua、Side Change、意味を潰すconsumer転記はいずれも0。残るmachine 26,279／tutor 369は供給未実装のためP03完了とは数えない。
- Stage74は残るmachine 26,279／tutor 369を、殿堂入りflag `0x082C`後にBagのわざメモリーから使える無料の暫定archiveへ接続した。machineは40件単位の最大4ページ、tutorは最大12件の1ページで、既知技filter、4枠交換／cancel、空ページ再選択、全終了時mode resetを既存UIと共用する。固定TM／教え技slotやlevel／eggへの転記は0、family同一Move ID 10件も別表のまま、Side ChangeとBrowt／Pombon／Gecquaは0。全118,369選択経路と現行`BuildLearnableMoveset`を照合し、退化後にも合法な4,014 path／2,223 target-moveをUI非公開の削除防止表へ追加した。これは新規供給や経路勘定に含めず、全1,621種で最大238/429、overflow 0。累積runtime materialized 83,162、accounted 118,369、直接供給残0だが、Rockruff 38経路と最終mGBAが残るためP03完了とは数えない。
- Stage75はOwn Tempo Rockruffを通常追加Speciesではなく図鑑非加算の内部条件フォーム1670としてappendした。Abilityは3slotともマイペース20、National Dex 744、collection class 4／weight 0。通常1142の黄昏進化行を消し、1670だけがLv.25以上・17〜19時に1263へ進化する。野生1142の成功生成後にpersonality由来の決定的1/8だけを1670へ変換し、追加RNGを消費しない。繁殖は1263／1670だけを1670へ解決し、他Speciesは既存処理へexact delegateする。24 Species表／310 pointer／19 count consumerを1行拡張し、既存1142／1263とsave layoutは移行なしで保持した。0744.00の60 routeをidentity ownerとしてexact cloneし、38 carry pathは既存slot 21＋Stage74 archive 17へ解決、missing owner 0、accounting delta 0。Side ChangeとBrowt／Pombon／Gecquaは0、`full_p03_done=false`を維持し、最終mGBA前にP03完了とは数えない。

## P04の素材・取得経路・容量

- 追加予約はMega用Species/Form 49件（1621〜1669）、Item 45件（999〜1043）、Ability 6件（312〜317）。通常SpeciesとMoveの追加は0件で、現行Move最大ID 1062を維持する。Item 45件はStage68、Species/Form 49件とAbility固定表はStage70、Mega順逆表はStage71、Ability主要効果はStage72 ROMへ反映済み。公式仕様が後から判明する仮特性はstable keyを保った中央binding差し替えを使う。
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
- 新Ability 6件はstable key順ID 312〜317とu16 ABIを固定し、発動／不発／抑制／複数対象／AI／save、Fairy 23／Stellar 24を含む46 caseを独立2 processのhost C runtimeでPASSした。Stage72では固定表、6 Mega form binding、日本語説明と29 battle hookをROMへ接続した。Stage76ではMega SolのSolar charge時popup、Piercing Drillの予測Protect damage 1/4、Spicy Sprayの味方発火評価を追加した。DetectはProtectへ正規化し、Max Guard／ダイマックス、実Protect二重quarter、planned protection／semi-invulnerable、Present／Future Sight／Doom Desire／Pollen Puffを保守的に除外する。Stage77ではBattle Circus bit 26かつ特性無効bit 31の時だけ全29 hook／33 surfaceをStage72 originalへ委譲し、それ以外はStage72 wrapperへ委譲する。Eelevate専用switch AIは不完全な313→298置換を採らず、exact-ROM mGBAとともに未完了とする。
- 公式特性が不明な対象は、stable replacement key、`TEMPORARY_REPLACEABLE`、非公式表示guardを持つ仮特性14件として保持した。分類保留2件を含め、後から中央bindingだけを差し替えられる。
- P06の提出済み種族調整差分は0、P07の追加習得差分も0。review-only資料を自動採用していない。
- P08はStage76までのcheckpoint hash、生成実装、ignored ROM/BPS、evidence sourceを統合監査済み。Stage74→75→76のincremental BPSとallocator lineageをfail closedで固定した。active baseline Stage62、P01のみDONE、P02〜P08未完了、release-ready=falseを維持する。

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
python3 scripts/run_modernization_p02_stage71_acceptance.py check
python3 -m unittest tests.test_modernization_p02_stage71_acceptance
python3 scripts/build_modernization_p05.py --check
python3 scripts/build_modernization_p05_ability_runtime.py --check --compact
python3 scripts/build_modernization_p05_ability_rom_runtime.py --check
python3 -m unittest tests.test_modernization_p05_ability_rom_runtime
python3 -m unittest tests.test_modernization_p03_stage73_runtime
bash scripts/build_modernization_p03_stage73_runtime.sh check
bash scripts/build_modernization_p03_stage74_supply.sh check
python3 -m unittest tests.test_modernization_rockruff_own_tempo_stage75
python3 tools/modernization_rockruff_own_tempo_stage75.py --check
python3 -m unittest tests.test_modernization_p05_stage76_edges
python3 tools/modernization_p05_stage76_edges.py --check
python3 -m unittest tests.test_modernization_p05_stage77_suppression
python3 tools/modernization_p05_stage77_suppression.py --check
python3 scripts/build_modernization_p07.py --check
python3 scripts/run_modernization_p02_acceptance.py check
python3 scripts/build_modernization_p03_stage67.py check
python3 scripts/run_modernization_p03_stage67_mgba.py check
python3 scripts/build_modernization_p08.py --check
```

Stage67をclean private環境から作り直す必要がある時だけStage67 build／mGBA runを使う。全repository unitと同じ実mGBA chainを毎回重ねない。

## 再開順

1. Stage76を親に、Battle Circusの特性無効ルールを通常戦へ漏らさないStage77 checkpointを統合する。
2. Eelevate専用switch AIはGround／Thousand Arrows／接地／Gravity／Mold Breaker／Ability Shieldを保持できる設計に限って別checkpointで実装する。
3. 49 Mega代表、通常／Frontier／Link／Mega Brawl、交代／ひんし／終了、新Ability代表、P02通常UI、Stage73〜75 egg／Move Memory／ロトム／Rockruff保存、Floette full・fresh reloadを同じmGBAセットで一度だけ検証する。
4. 提出済み採用差分が入った場合だけP06/P07を実装し、最後にP08 release gateを再評価する。

どの再開点でも、過去Stage、原本ZIP、既存saveを上書きせず、候補Stageを現行プレイ基準へ自動昇格しない。
