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

## 失敗判定

- ROM横に同名`.srm`があるだけでは合格にしない。
- 新規ゲームが始まった状態でRetroArchを閉じる前に、正規saveを上書きしない。
- ファイルの存在だけで合格にせず、size、SHA-256、basename、実save directoryを全て照合する。
