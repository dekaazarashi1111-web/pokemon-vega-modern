# import_review.md

## 結論

受領した設計資料は次の優先順位で使う。

1. `Pokemon-Vega_MOVE-DISTRIBUTION-V4_IMPLEMENTATION-READY.zip`: T22の全習得表・form・野生初期技に関するactive実装入力。
2. `Pokemon-Vega_RESEARCH-ECONOMY-V1_IMPLEMENTATION-READY.zip`: T23の研究通貨・活動・rank・shop・saveに関するactive実装入力。
3. `Pokemon-Vega_REWARD-ENCOUNTERS-V2_IMPLEMENTATION-READY.zip`: T24のtyped credit・pending再戦・報酬遭遇に関するactive実装入力。
4. `Pokemon-Vega_FACTORY-HIGH-MODES-V2_IMPLEMENTATION-READY.zip`: T25の24 Factory mode・rental・opponent・rewardに関するactive実装入力。
5. `Pokemon-Vega_EVENT-DESIGN_IMPLEMENTATION-READY.zip`: T20で実装済みの物語・event入力。Stage 37への統合来歴として保持する。
6. `vega_modern_codex_playbook`: 再現ビルド基盤、T00〜T18のDAG、検証雛形。
7. `vega_cfru_integration_audit`: パッチ競合の一次証跡と監査ツール。
8. `VEGA_CFRU_DPE_ベガ本編トレーナー再設計_V4`: Vega本編の編成、技、道具、IV下限、AI段階に関するactive実装入力。
9. `VEGA_CFRU_DPE_統合設計_V2_二地方生態版`: トーホク＋カントーの完成像・進行・生態・イベントに関するactive review資料。
10. `VEGA_CFRU_DPE_技調整設計_V3`: 技効果、ベガ独自技再調整に関するactive review資料。習得配布の現行正本はT22入力を優先する。
11. `VEGA_CFRU_DPE_統合設計` V1: V2の来歴確認専用。新規判断には使わない。

## ChatGPT Pro返却4設計の位置付け

- 4 ZIPすべてでCRC、path traversal、symlink、暗号化、実行形式、ROM/save/patch混入を検査し、異常0。
- Move Distribution V4は395,446 bytes、SHA-256 `4022cd6e1358f58dffc5ebc38b756166f0a1072f948af6934298f65bd82678b2`、11ファイル。level-up 28,274、egg 8,219、TM/tutor 2,799、form 509、wild/source 1,206、fingerprint `d0e014e49beb339668ce3531b8fe6871c793a063f2bff1c8d2b97898f81d02a9`。
- Research Economy V1は21,503 bytes、SHA-256 `0cd2a68535f5543da919a6502a21321adb826dbff37d356b0cacfc697c7367de`、12ファイル。activity 6、currency 1、rank 7、shop 23、NPC 9、dialogue 35、batch 7、fingerprint `2ea4497307af6aece808fd9a98158561c7c87e83cd4748b2e6d3ab8c4aa27a8b`。
- Reward Encounters V2は19,169 bytes、SHA-256 `b293c9f9c65eaf7acf4a6c5707163460b095d761283dc821d920801b38262195`、10ファイル。service 4、pool 24、credit source 10、dialogue 56、batch 5、fingerprint `823664fd0f53a88014f361ba592838084ad660101a724e416f3ddffb507a42df`。
- Factory High Modes V2は30,203 bytes、SHA-256 `7e79616dea664f670b8985fe89d23e066df2751225b5a8ee078035b4bb2b9830`、13ファイル。mode 24、requirement 28、rental 248、profile 55、reward 16、dialogue 28、batch 7、fingerprint `c48d69f2a64cda65f2a97a2382ddb8bb4dbc66437302a87e3da669428dc20fe1`。
- 全4本とも公式validatorでstatus PASS、warnings/errors/open questions 0。validatorがReward tierの期待集合を価格値の個数として比較していた不具合は、各tier 1件の集合比較へ修正し、正常系と重複/欠落系の回帰testを追加した。
- 設計時の技術catalogはStage 37基準なので、意味仕様とstable keyを採用し、address、save offset、map host、allocator spanは各タスクの直前Stageから必ず再解決する。
- 統合順は `T22 Move -> T23 Research -> T24 Reward -> T25 Factory` に固定する。Moveは野生・rentalの基盤、ResearchはReward credit source、RewardはFactory milestone hookを所有するため、同一branchで4件を並列実装しない。

## 実装可能イベント設計の位置付け

- ZIP: 71,084 bytes、SHA-256 `576847447f0c659c3db639179aa1fa71057b909d8eff5b408ba725ee285fee8e`。
- 6ファイル、展開後755,156 bytes。CRC、path traversal、symlink、暗号化を検査し、異常0。
- Stage 35生成catalog付き公式validatorでstatus PASS、warnings/errors/open questions 0、submission SHA-256 `776d8c911ad3c2705ffdaf840d1b6cdbefe816cf000accdf3ea47a45991c4fec`。
- 28 arc、80 state、14 actor、63 placement、160 condition、7 reward、76 event、7 batch、326 dialogue、98 coverage rowを含む。
- 物語とevent意味はactive実装正本とする。ただし生成catalogはStage 35基準のため、numeric address、host availability、object budget、QOL serviceはT19完了済みStage 36で再解決してから実装する。

## 本編トレーナー再設計V4の位置付け

- ZIP: 333,031 bytes、SHA-256 `0655648e4d54bd29c49a13deeae997cbf5465f717d7f1513540bc20fdefdbac8`。
- 展開21ファイル。同梱`SHA256SUMS.txt`の20対象は20/20 PASS、内部検査21/21 PASS。
- 戦闘master 141戦、party master 610体。数値Trainer IDは含まないため、名前、役割、既存編成、
  map上の既存NPCを用いて明示対応し、一般・再戦は元level/class/double属性から決定的に対応する。
- Species/Move/Itemはcanonical manifestへ厳密joinする。フォーム表記とVega前段階だけを
  `config/trainer_rebalance_v4.json` の明示aliasで解決し、部分一致は使わない。
- V4 AI rank 1〜5は別AIとして実装せず、固定CFRU-JPの既存フラグへ
  `1→AI_BASIC / 2–3→AI_SEMI_SMART / 4–5→AI_FULL_SMART` と対応する。
- 通常Trainer ABIで表現できるSpecies、level、held item、4技、IV下限、trainer item、AIを
  ROMへ反映する。性格・特性・EV・個別gimmick triggerは台帳に保持し、CFRU生成規則を変えない。
- 追加event/Trainer IDを持たない21戦は既存戦へ推測接続せずcatalog-onlyとする。

## 技調整V3の位置付け

- ZIP: 159,635 bytes、SHA-256 `51fdf3aa25f49dc0586d2d824117995261527a3ae306d621aa718d273939ce37`。
- 展開14ファイル。同梱`SHA256SUMS.txt`の13対象は13/13 PASS。
- 技効果現代化61技、ベガ独自技再調整70技、TM・教え技184枠を含む。
- T04では実ROMから抽出した技ID・battle recordへ技名で厳密joinし、数値調整と必要なeffect adapter契約を生成する。曖昧一致は採用しない。
- 種族別習得表、フォーム継承、TM互換、野生初期4技は、最終統合IDとROM抽出結果が必要なためT04で直接適用せず、後続タスクへ引き渡す。

完成目標は、FireRed日本版Rev.0からVegaを再生成し、公開ソースのDPE-JP/CFRU-JPをVega互換で移植し、元FireRedのカントー本土を新規名前空間へ復元して、トーホクと自由往復できる32 MiB ROMを再現ビルドすることである。最終配布物はROMを含まない単一差分パッチとする。

## V2の完全性と位置付け

- ZIP: 465,121 bytes、SHA-256 `fb7c542a50aaec7ae25af70cdb100f4c71effb5e9ddc4f09c6365f79fa76cd06`。
- 展開49ファイル。`manifest.json` 47件と `MANIFEST.sha256` 47件は相互一致し、size/hash 47/47 PASS。
- 付属設計検査は59/59 PASS。ただし検査コードは同梱されず、件数・空欄・参照整合中心であり、ROM動作、hook、SaveBlock、マップ接続を保証しない。
- package statusは `design-specification-only`。V2のCSVをそのままgenerator入力へ昇格しない。
- V2記載のDPE基準 `520937c...` は来歴として扱い、実装はD-005の最新固定pin `10ff98c...` を正とする。

## V2で採用する二地方設計

- 公式1025種、541進化系統、541系統×2地方＝1,082行の入手導線。
- トーホク49生態地点はVega既存野生枠を直接置換せず、条件付きoverlay、DexNav、時間帯、大量発生へ追加する。
- カントー47生態地点は元FireRedの景観・施設を使い、原作系統35〜60%を残しつつ、Vega中盤から始まる高難度任意ルートと殿堂入り後層に再構成する。
- V2原案は初回殿堂入り後に連絡船を解禁するが、現行仕様ではVega中盤のアーシア島D・Hビル初回攻略後からクチバへ任意渡航できるよう正規化overrideする。一度解禁後はトーホクと常時往復可能にする。
- カントーの8認定章はVegaバッジと分離する。
- NPC再利用26件、重要アイテム置換24件、追加イベント34件、特殊個体125種の共有捕獲状態を設計入力にする。
- カントー原作のstory flag、badge、trainer、item、warp、varは再利用せず `KANTO_*` へ変換する。

V2の「47地点」は生態・進行上の論理地点であり、全建物・階層を含むraw map数ではない。カントー復元の物理scopeはT11でclean BPRJ Rev.0とpokefireredから全資産inventoryを作り、V2キーとのcrosswalkを生成して確定する。ナナシマはV2本体のscope外である。

V2のK-E01、カントー調査パス、チャンピオン前提台詞、必須のLv.70台船上戦は現行仕様と衝突する。T12の正規化で、早期調査招待、進行別台詞、任意・勝敗不問の船上戦へ置換する。V2受領原本は不変のまま保存する。

## V2にも残る意味課題

V2はV1の複数CSVをbyte同一で引き継いでおり、付属59検査が次を検出していない。

1. `進化条件変換マスター.csv` にID以外が同一の余剰23行・21群が残る。
2. 進化表にfrom/toフォームキーがなく、同じ全国番号を使うリージョン進化を区別できない。
3. Vega保護台帳の公式205件は全国番号が `276.0` のような小数文字列で、整数文字列の他CSVと直接joinできない。
4. `じばのコア`、`コケのコア`、`こおりのコア`、`フィールドコア` 等、進化表が参照する救済道具の一部が道具入手マスターにない。
5. フォーム509行は分類方針であり、統合後Form ID・数値flag・具体配置の実装台帳ではない。
6. 技・特性・道具・hookはTEMPLATE中心、Species 1206行は未割当、SaveBlock offsetも未確定。
7. Z／ダイマックス／テラは機能profileで任意P2だが、後半イベントとQAの一部が前提にしている。v1.0必須scopeを別ADRで決める必要がある。
8. V2は新規ゲーム必須を標準とし、旧Vega save移行を試みる現行方針との最終判断が未確定。

T12で型正規化、フォームキー追加、意味重複解消、全参照整合validatorを実装してから `manifests/` / `content/` へ昇格する。

## 競合監査から継続する技術方針

単体監査パッケージの `MANIFEST.sha256` は15/15 PASS。主要事実は次のとおり。

- Vega IPS変更量: 3,782,136 byte。
- Factory UPS変更量: 14,680,526 byte。
- 直接重複: 269 ranges / 775 byte。
- 技名・技データpointer関連: 169 ranges / 533 byte（68.774%）。
- clean ROMによる厳密比較: `SAME_TARGET=191`、`DIFFERENT_TARGET=584`。

したがってFactory UPSは参照専用とし、パッチを重ねず公開ソースからMove、battle、Speciesの順で移植する。

## 資料の優先順位

矛盾時は次の順で判断する。

1. `AGENTS.md` の運用・安全規則。
2. `design/decisions.md` の採択済みADR。
3. `design/tasks_next.md`、`tasks/task_graph.json`、選択タスクの `tasks/T*.md`。
4. `MASTER_PLAN.md` と `docs/` の現行技術方針。
5. `audit_seed/` と生成監査の測定証拠。
6. V2二地方設計のactive review資料。
7. V1来歴資料。

測定証拠が仕様と矛盾する場合は、黙って片方を採らずADRを追加して解決する。
