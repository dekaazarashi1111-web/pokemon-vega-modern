# USER-MODERNIZATION-P01 ID意味・対象区分・共通処理監査

2026-09-08。以前のsource-only BLOCKED checkpointの残件を実装・実測した記録。状態の正本は `design/tasks_next.md`。P02/P03は未開始であり、この監査は全ゲームの無期限デバッグや進化仕様の一括採用ではない。

## 確認済み不具合と修復

固定Stage61 Wiki builderは旧取得表のcanonical_idだけでjoinするため、キャタピー649と内部タマゴ412の区分が逆転する。過去Wiki・vendor原本・Stage builderは変更しない。現行入口は `scripts/build_modernization_catalog.py` → `scripts/build_modernization_targets.py`。前段の現在sourceとのbyte一致、全key集合、全国番号・form_key、元対象集合digestを検査してからJSON/CSV/Wiki用索引を生成する。

ROM側は別に調べた。Stage62 SHA `d97a0d4a6cd6f8f77a1503a5ac6d473b0e94c4892e3d5a94098497ce35cb6e6f` 内、offset19760432の1621×8-byte収集C表に旧割当が一つだけ存在した。既存の実C save処理と、同じ実ROMの `VegaAcqSaveMigrate` を呼ぶmGBAで、キャタピー649のbit386登録欠落と内部タマゴ412への誤登録を再現した。単なるROM内byte検索をruntime証拠としたわけではない。

`build_p01_collection_table.py`はspecies_keyから現行IDへ解決し、collection_key→bit/属性の対応を完全に保持する。412/649の非ID列のみを交換する。既存ID、全1216bitの番号、152-byte bitmap、240-byte内側save block、valid saveの全byte、原本C表を保持した。旧saveにあるbit386の過去の由来は推測せず、既存bitを消去・再構成しない。

`build_p01_rom.py`はclean ROM→既存hash固定Stage62 BPS→manifest訂正表の順に別候補を生成する。候補は33554432 bytes、SHA `6642602d33e1e074c20afebfc649846f0aaf106c2455f2ca212a4f427ec74fbd`、CRC32 `FB09EF2D`。変更10 bytes、宣言はoffset19763728/19765624の各8-byte行、宣言外0、新規ROM/RAM/save allocation0。2回のclean起点再生成、Stage62→候補89-byte BPS、候補→Stage62 84-byte BPS、clean→候補BPSの往復を検証した。

実測run: https://github.com/dekaazarashi1111-web/pokemon-vega-modern/actions/runs/34174073406 （HEAD efc2662dc6d1cc59732da13411b5569ea8525577）。旧ROM/候補それぞれ独立2process×3case。実ARMの移行・CRC確定・CRC検証を使い、候補で修復、valid save全240-byte不変。これはdirect-call回帰で、通常プレイ全導線のE2Eを名乗らない。通常プレイ基準と実機saveを切り替えない。

## 対象集合と関連表

全Species1621、Move1063、Ability312、Item999、Type25のkey/ID全単射を検査。Species/Formの意味は全国番号・form_key・公式種フラグと全対象集合まで照合する。進化要求553組、Form388組（除外method115）、Item供給999組を照合した。

原作習得対象は1299→1300key。追加はキャタピーだけで、内部タマゴ・内部枠・戦闘専用枠・除外7任意フォームを維持する。1300種に技表を反映した意味ではない。既存技806対をkey/IDで照合、ALLY SWITCH候補1063は現行0..1062の外で未実装のまま。復元資料205種の提案、特性/種族値/進化の変更は未採用。特性参照は数値＋名前を照合するが、記号keyが未指定の提案をruntime採用しない。

生成モデルのMove1063、Ability312、Item999、Type25は現行manifestと全key/ID対一致、旧ID・未解決key0。タマゴ技streamは1388種族marker/8831技/20440bytes、marker重複・範囲・技key/ID・終端を照合した。タマゴ技のない種への自動追加はしない。run: https://github.com/dekaazarashi1111-web/pokemon-vega-modern/actions/runs/34174354489 （HEAD ad1f9b0d114da9ad31bb8a2922baf3ffa1cef8a3）。

## 配置と容量の実測

| 対象 | 現行と測定結果 | 将来追加時の制約 |
|---|---|---|
| Species/Form | 1621行、Form388行を含む。manifest ID0..1620連続 | 内部枠・別姿を空きIDとして再利用しない。追加には表・consumer境界の生成変更が必要 |
| Move | 1063行、ID0..1062。原作参照806対一致 | ID1063の提案を既存技に混入させない。単なるu16上限を実装容量としない |
| Ability/Item/Type | 312/999/25行。生成モデルとkey/ID一致 | BaseStats全1621種のAbility3・Item2・Type2参照を実ROMで照合。型幅だけで追加可能とはしない |
| 進化 | 16枠/種、856使用、1種最大9、未使用25080枠、終端後の有効行0 | 空きは種族ごと。全種共通の新種容量ではない |
| レベル技 | raw28874行、1種最大34 | 3-byteレコードとpointer/終端を維持。表示側の0技除外後28859との差は不具合件数にしない |
| TM/HM | TM120+HM8=128枠、16bytes/種、60214互換 | 既存bit枠は満杯。新枠を無条件に追加しない |
| 教え技 | active64枠、21883互換。bitmapは128bit/種 | 未使用側64bitには計20151bitが立つ。空き64枠として使用すると旧bitが誤採用されるためP03以降の明示再生成が必要 |
| 収集save | 1216bit/152bytes、全bit0..1215使用。内側block240bytes | bit再indexをしない。本工程は既存valid saveを変更しない |
| ROM integration_modules | 枠4194304、使用2433478、未割当1760826、最大連続1760688bytes | 未割当spanのROM byteは全FF。中央allocatorによる将来の明示割当が必要 |
| ROM future_tail | 枠720896、使用565806、未割当155090、最大連続155076bytes | 同上。空きの確認を自動採用・上流更新・ROM拡張の承認としない |
| RAM/save | config/ram_layout.csv・save_layout.csvは不変。Box80/Party100、既存独立ownerを保持 | 台帳にないRAMを空き扱いしない。T08内のreserved15/129bytesも別owner採用まで保持 |

容量実測run: https://github.com/dekaazarashi1111-web/pokemon-vega-modern/actions/runs/34173283267 （HEAD 0b9fd7a70d50670a6baa289e2c2e78aa225c6182）。親Stage62と候補は収集表の10byte以外が同一であり、ここに挙げた表・配置の測定範囲に候補差分はない。

## 検証環境の不具合

`/vega-test stage62-check 5ab5b1f406175fa4fb98884ae924e291f355286b` を実際に起動。run34172072248は権限/取得ではなく、既存tracked `reports/generated/stage61_wiki.json` と環境ZIPの旧版との衝突で復元が失敗した。

`restore_p01_environment.py`が対象reportをGit blob ec3c2e823bf422dcd72ec19951be83128c83651aへ限定し、一時退避・復元後に現在版を戻し旧版も.localへ保存する。既存restoreをforce=Falseで使い、外側/member hash・symlink・他file衝突・secret保護を一切緩めない。現在report SHA c3c263b71d99576d41ba610efbb5a44a7da1ba566108ddbad58c76f91caa022e、旧版e2bcf5e613d5ccc63a1a643f8fc723f8239c75b7ac120cbfa413b4a5b22be5d4を両方保全した。

Stage62 check＋独立2process mGBAの成功はrun34172673504、HEAD a89cd50f4a065a399553619456a4a17dc66de3a3。後続HEADではP01追加file以外の差分がなく、実ROM identity・GitHub上の同一run成功・元実装の不変を再照合できる場合にだけ再利用する。不一致・不明なら同じmGBAを実行する。候補検証への流用は禁止し、候補は専用gateで実行する。

## 入力・再取得と工程境界

元ZIPのsize/hashと限定採用はconfig/modernization_inputs.json。原本はLibraryで不変、Actionsへは限定正規化contract9549bytes/SHA00fa015276eef8506c57caa660ec3093ce137bd0506cb7db5af062cea6b1b265をexact Git checkoutで復元する。元ZIPの自動転送を仮定しない。

ROM構築資材はconfig/github_private_environment.jsonに固定した既存Release4ZIPをephemeral runnerへ取得・hash復元する。repository/Releaseはpublicであり名称のPrivateを非公開根拠にしない。本工程ではROM/save/元ZIP/BPSの新規uploadや公開ログ転記は行わない。候補はソースから再生成する。新しい非公開保管先の整備や現行実機への配布は別操作である。

P02へ: 553要求と856実ROM進化行のkey付き監査を入口に、地域フォーム・独自条件・提案の採否を整理する。P03へ: current_targets.json/CSV、元ZIP、キャタピー追加のみの1300対象、未実装ALLY SWITCHと教え技上位bitの扱いを引き継ぐ。既存の除外フォームを一括有効化しない。P01候補を累積親として採用する場合も、active_play_baseline.jsonのプレイ基準は別依頼までStage62のまま。

未確認は全NPC/全会話のstrict監査、通常プレイ全経路E2E、ユーザー実機saveの状態、未承認の進化/習得/能力仕様。これらを本工程で完了扱いにしない。資料不整合と意図したVega独自仕様を混ぜず、元Stage60 IN_PROGRESS・別PRは保持する。
