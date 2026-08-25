# iPad RetroArch / mGBA `.srm` 配置メモ

## 正本ルール

- `.srm`をROMの横へ置かない。iPad版RetroArchの有効な`retroarch.cfg`から、その時点の`savefile_directory`を毎回読み取る。
- 現在の実機設定は`sort_savefiles_enable = true`、`sort_savefiles_by_content_enable = false`で、実際のmGBA save directoryの末尾は`mGBA/`である。
- save名はGBAファイルのbasenameと完全一致させる。例:
  - ROM: `53_world_runtime_e2e_repair.gba`
  - save: `53_world_runtime_e2e_repair.srm`
- iOSのApplication container UUID、端末IP、credential、絶対pathは固定値として記録しない。アプリ更新・再インストールで変わり得るため、container metadataと`retroarch.cfg`から都度解決する。

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

## Stage54の配置待ち対応

- ROM: `54_world_runtime_e2e_repair.gba`
- ROM SHA-256: `b130c03b0a10b80e1d10ef962d8fa6fb2f70c6529155119a3673a9a338e34c03`
- 互換save: `54_world_runtime_e2e_repair.srm`
- save size／SHA-256: 131,072 bytes／`406bc49cf298eed9a15ad83d5ff8161512d95a4815d8db486ee88ccbce0d15d2`
- Stage53を上書きしない。RetroArch停止と有効container／`savefile_directory`を再確認してから、ROMとsaveをStage54の別basenameで新規配置する。
- 2026-08-25時点ではローカル20 fixture PASSまで。iPad配置・実プレイ承認は未実施。

## 失敗判定

- ROM横に同名`.srm`があるだけでは合格にしない。
- 新規ゲームが始まった状態でRetroArchを閉じる前に、正規saveを上書きしない。
- ファイルの存在だけで合格にせず、size、SHA-256、basename、実save directoryを全て照合する。
