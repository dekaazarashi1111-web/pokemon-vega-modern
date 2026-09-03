# iPad RetroArch / mGBA `.srm` 配置メモ

## 正本ルール

- `.srm`をROMの横へ置かない。iPad版RetroArchの有効な`retroarch.cfg`から、その時点の`savefile_directory`を毎回読み取る。
- 現在の実機設定は`sort_savefiles_enable = true`、`sort_savefiles_by_content_enable = false`で、実際のmGBA save directoryの末尾は`mGBA/`である。
- save名はGBAファイルのbasenameと完全一致させる。例:
  - ROM: `53_world_runtime_e2e_repair.gba`
  - save: `53_world_runtime_e2e_repair.srm`
- iOSのApplication container UUID、端末IP、credential、絶対pathは固定値として記録しない。アプリ更新・再インストールで変わり得るため、container metadataと`retroarch.cfg`から都度解決する。

## Stage56以降の標準テスト用セーブ

- 新しいstageを軽く確認するiPad配置では、特別な指定がない限り`config/test_ready_save.json`の標準profileを使う。
- `make test-ready-save`でblank flashからROM自身の通常save APIを2回通し、full save、slot 0／1単独、自然ContinueをmGBAで検証する。生成済み`.srm`をhex editorやhost側checksum再計算で加工しない。
- 標準profileはCodex対戦受付前、博士のポケモン／図鑑／ランニングシューズ取得済み、badge 8件設定による全Lv.服従とする。手持ちはミュウツー先頭、カイオーガ、グラードン、レックウザ、ゼルネアス、ムゲンダイナのLv.100攻撃型6体で、全24技を攻撃技、各個体の1技以上を複数対象技とする。
- 新しいstageではconfigのROM identityとbasenameを更新して同じgeneratorを再実行する。旧stageの`.srm`をbasename変更だけで使い回さない。
- 実機プレイと人手承認はtask／release gateに含めない。配置を依頼された時だけ、下記の停止・退避・原子的転送・read-backを行う。

## 配置手順

1. RetroArchを終了し、processが停止したことを確認する。起動中に置くと、メモリ上の新規ゲームsaveで正規`.srm`が再上書きされる。
2. 有効なRetroArch application containerをmetadataから一意に特定する。
3. container内の有効な`retroarch.cfg`を一意に特定し、`savefile_directory`とsave sort設定を読む。
4. 実際にmGBAが使用中のsave directory末尾が`mGBA/`であることを確認する。ROM directoryを転送先にしない。
5. 転送先を`<ROM basename>.srm`とする。既存saveが異なる場合は削除せず、同じdirectoryへ`.pre-restore-<timestamp>`付きで退避する。
6. 一時ファイルへcopyし、131,072 bytesと期待SHA-256を確認してから原子的に正規名へ移す。
7. 正規`.srm`をiPad側でread-backし、一時ファイル0、source save不変を確認する。

## Stage53の確認済み対応

- `53_world_runtime_e2e_repair.gba` → mGBA save directoryの`53_world_runtime_e2e_repair.srm`
- 正常save size: 131,072 bytes
- 正常save SHA-256: `406bc49cf298eed9a15ad83d5ff8161512d95a4815d8db486ee88ccbce0d15d2`
- 2026-08-25に新規ゲーム側のStage53 saveを復旧可能な名前へ退避し、上記正常saveを配置済み。

## Stage54の確認済み対応

- ROM: `54_world_runtime_e2e_repair.gba`
- ROM SHA-256: `b130c03b0a10b80e1d10ef962d8fa6fb2f70c6529155119a3673a9a338e34c03`
- 互換save: `54_world_runtime_e2e_repair.srm`
- save size／SHA-256: 131,072 bytes／`406bc49cf298eed9a15ad83d5ff8161512d95a4815d8db486ee88ccbce0d15d2`
- Stage53を上書きせず、RetroArch停止と有効container／`savefile_directory`を再確認して、ROMとsaveをStage54の別basenameで配置済み。
- 2026-08-25にiPad側でROM／saveのsizeとSHA-256をread-back一致、一時ファイル0、既存Stage53不変を確認した。実プレイ承認は未実施。

## Stage55の確認済み対応

- ROM: `55_world_runtime_visible_feedback_repair.gba`
- ROM SHA-256: `b0a825cb7d3886419e4122f2de54a069fdf8e7a5fe41a9fef0bc3235e68cbcf8`
- 互換save: `55_world_runtime_visible_feedback_repair.srm`
- save size／SHA-256: 131,072 bytes／`406bc49cf298eed9a15ad83d5ff8161512d95a4815d8db486ee88ccbce0d15d2`
- 2026-08-25にWi-Fi SSHでlive `retroarch.cfg`と実mGBA save directoryを再解決し、RetroArch停止中に一時名から原子的に配置した。
- iPadからROM／saveをread-backしてsourceとbyte一致、一時ファイル0、既存Stage54 ROM／saveのSHA-256不変を確認した。実プレイ承認は未実施。

## Stage56の確認済み対応

- ROM: `56_collection_supply_v1.gba`
- ROM SHA-256: `9309c073798dc363174458ebcb75bf3f1e86d475dcd129b74875d5a6bb875778`
- 標準save: `56_collection_supply_v1.srm`
- save size／SHA-256: 131,072 bytes／`3192100245672e13baa2d4398d115c2288758e901033e7b4c9830124164f90df`
- 2026-08-27にRetroArch停止、active container metadata、live `retroarch.cfg`、mGBA save directoryを再解決し、一時名からROM／saveを原子的に配置した。
- 同日にLv.100攻撃型6体profileへ更新し、旧save（SHA-256 `bdc4eea8dacf093734be6fcaa26eb55351126bbe39654d156f61829a3b90a5f7`）を日時付きで保全してから同名saveを原子的に置換した。
- iPadから更新saveをread-backしてsourceとbyte一致、既存Stage55不変、一時ファイル0を確認した。実機プレイ／人手承認は未実施で、完了条件にも含めていない。

## Stage57の確認済み対応

- ROM: `57_comprehensive_debug_repair.gba`
- ROM SHA-256: `546136a6baa26efd7a70c2b6826bf902c4841a4a1113cb53bfdc44c77971663d`
- 標準save: `57_comprehensive_debug_repair.srm`
- save size／SHA-256: 131,072 bytes／`3192100245672e13baa2d4398d115c2288758e901033e7b4c9830124164f90df`
- 2026-08-28にStage57 exact ROM自身の通常save APIで標準Lv.100攻撃型6体saveを独立2 process生成し、full save、slot 0／1、自然Continue、Codex受付をPASSした。
- RetroArchを通常終了してprocess 0を確認し、active container metadataとlive `retroarch.cfg`からROM directoryと実mGBA save directoryを再解決した。一時名転送、iPad側size／SHA確認、同一directory内の原子的確定を行った。
- iPadからROM／saveを新規ローカル領域へread-backしてsourceとbyte一致した。既存Stage57同名成果はなかったため退避0、remote一時ファイル0、既存Stage56 ROM／saveは不変。実機プレイ／人手承認は未実施。

## Stage58の確認済み対応

- ROM: `58_qol_world_convenience_debug.gba`
- ROM SHA-256: `501c3fdda825abfb167bc62da63c189671fa2f026d7b866001fbfbac36700a0c`
- 標準save: `58_qol_world_convenience_debug.srm`
- save size／SHA-256: 131,072 bytes／`f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb`
- 2026-08-28にStage58 exact ROM自身の通常save APIで標準Lv.100攻撃型6体saveを独立2 process生成し、full save、slot 0／1、自然Continue、Codex受付をPASSした。
- RetroArch process 0、active container metadata、live `retroarch.cfg`、実mGBA save directoryを再解決し、一時名転送、iPad側size／SHA照合、同一directory内の原子的確定を行った。
- iPadからROM／saveを新規ローカル領域へread-backしてsourceとbyte一致した。既存Stage58同名成果はなかったため退避0、remote一時ファイル0、既存Stage57 ROM／saveは不変。実機プレイ／人手承認は未実施。

## Stage59の確認済み対応

- ROM: `59_wild_identity_npc_regression_repair.gba`
- ROM SHA-256: `8ed4c9597fa73e9b30afd940d3855f99c4759297d9f48e584eaf9df8c3a303da`
- 標準save: `59_wild_identity_npc_regression_repair.srm`
- save size／SHA-256: 131,072 bytes／`f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb`
- 2026-08-29にStage59 exact ROM自身の通常save APIで標準Lv.100攻撃型6体saveを独立2 process生成し、full save、slot 0／1、自然Continue、Codex受付をPASSした。
- RetroArch停止とlive設定を再解決し、ROM／同名saveを一時名から原子的に配置した。iPad上のStage58セーブは以前の配置後に進行済みだったため、現在値を保全基準として配置前後不変を確認した。
- iPadからROM／saveをread-backしてsourceとbyte一致、remote一時ファイル0、既存Stage58 ROM／save不変を確認した。実機プレイ／人手承認は未実施。

## Stage60の確認済み対応

- ROM: `60_wild_species_root_repair.gba`
- ROM SHA-256: `3f9983eb099c2ca7205c14047460c8b2ed73a6180bd2a131a09c74af9d359ff1`
- 標準save: `60_wild_species_root_repair.srm`
- save size／SHA-256: 131,072 bytes／`f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb`
- 2026-08-29にStage60 exact ROM自身の通常save APIで標準Lv.100攻撃型6体saveを独立2 process生成し、full save、slot 0／1、自然Continue、Codex受付をPASSした。
- active container metadataとlive `retroarch.cfg`から配置先を再解決した。転送後にRetroArchの再起動をprocess gateで検知して正規確定を中断し、再停止とprocess 0確認後に同じ処理内でROM／saveを一時名から原子的に確定した。
- iPadからROM／saveをread-backしてsourceとbyte一致、remote一時ファイル0、既存Stage59 ROM／save不変を確認した。同名既存Stage60成果はなく退避0。実機プレイ／人手承認は未実施。

## Stage61候補ROMの確認済み対応

- ROM: `61_critical_release_candidate.gba`
- 現行ROM SHA-256: `734541807df91ca6f82211b57e0a56e6af6c1c70ec46b9f89cd6a89b3f701f3b`
- 2026-09-03に固定host key付きWi-Fi SSHでactive container metadataとlive `retroarch.cfg`を再解決し、RetroArch process 0を確認して修正済みROMだけを一時名から原子的に配置した。旧ROM `e736acd0...3669`は日時付きで退避した。
- iPad側33,554,432 bytes／SHA-256を照合し、端末からのread-backをsourceとbyte一致させた。mGBA save directory全57件のmanifestは配置前後不変で、同名saveを含むsaveの生成・転送・変更は0。既存Stage60 ROM不変、remote一時ファイル0、RetroArch process 0を確認した。
- 同日、Vega既存trainer会話復元・外来生態率調整後の現行ROM `4c2cda81...538b`へ再更新した。旧ROM `5d1f3230...8f3e`を日時付きで退避し、iPadからのread-backをsourceとbyte一致させた。save directory全57件は前後不変、同名save未変更、remote一時ファイル0、RetroArch process 0を確認した。
- 同日、Codex runtime cold-boot入口を復旧した現行ROM `60b83b8c...5aff0e`へ再更新した。旧ROM `4c2cda81...538b`を日時付きで保全し、iPadからのread-backをsourceとbyte一致させた。save directory全57件は前後不変、同名save未変更、remote一時ファイル0、RetroArch process 0を確認した。
- 同日、TM120＋HM8／教え技64のruntime接続と、わざメモリー／せいたいレーダーのfield復帰を修正した現行ROM `44e951e2...ae4e`へ再更新した。旧ROMを日時付きで保全し、iPad側33,554,432 bytes／同一SHAとread-back byte一致を確認した。save directory全57件は前後不変、同名save未変更、既存Stage60不変、remote一時ファイル0、RetroArch process 0を確認した。
- 同日、戦闘後に残るbattle type値でわざメモリーが誤って使用不可になる問題を修正した現行ROM `73454180...01f3b`へ再更新した。旧ROMを日時付きで保全し、iPad側33,554,432 bytes／同一SHAとread-back byte一致を確認した。save directory全57件は前後不変、同名save未変更、既存Stage60不変、remote一時ファイル0、RetroArch process 0を確認した。

## Stage62候補ROMの確認済み対応

- ROM: `62_npc_placement_integrity_repair.gba`
- ROM SHA-256: `d97a0d4a6cd6f8f77a1503a5ac6d473b0e94c4892e3d5a94098497ce35cb6e6f`
- 2026-09-04にactive container metadataとlive `retroarch.cfg`から配置先を再解決し、RetroArch process 0を確認してStage61とは別名でROMだけを一時名から原子的に新規配置した。同名既存ROMはなく退避0。
- iPad側33,554,432 bytes／SHA-256を照合し、端末からのread-backをsourceとbyte一致させた。mGBA save directory全57件は配置前後のmanifestが一致し、同名saveの生成・転送・変更は0。既存Stage61 ROM不変、remote一時ファイル0、RetroArch process 0を確認した。
- 同日、ユーザー指定によりiPad上の最新Stage61通常プレイsaveをStage62 basenameへ引き継いだ。131,072 bytes、SHA-256 `f4e978f4bb5af630ca923c5f55687333a9d69f45391a5ca9a2b57546d42bb044`。Stage62起動時に作られていた同名saveは日時付きで退避し、一時名から原子的に配置した。
- Stage61 save原本とその他の保護対象save全57件は前後不変。Stage62正規saveを端末からread-backしてStage61原本とbyte一致させ、remote一時ファイル0、RetroArch process 0、Stage62 ROM identity不変を確認した。

## 失敗判定

- ROM横に同名`.srm`があるだけでは合格にしない。
- 新規ゲームが始まった状態でRetroArchを閉じる前に、正規saveを上書きしない。
- ファイルの存在だけで合格にせず、size、SHA-256、basename、実save directoryを全て照合する。
