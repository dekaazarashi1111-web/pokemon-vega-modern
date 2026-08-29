# USER-20260829-STAGE59-IPAD-ROM-SAVE-PLACEMENT — Stage59 ROMと標準QAセーブをiPadへ配置する

- Status: `DONE`
- Lane: `qa/save/ipad/release-ops`
- Depends on: `USER-20260829-STAGE59-WILD-IDENTITY-NPC-REGRESSION-REPAIR`、`USER-20260828-STAGE58-IPAD-ROM-SAVE-PLACEMENT`
- Queue ID: `USER-20260829-STAGE59-IPAD-ROM-SAVE-PLACEMENT`
- Baseline: Stage59 / ROM SHA-256 `8ed4c9597fa73e9b30afd940d3855f99c4759297d9f48e584eaf9df8c3a303da`

## 目的

Stage59 ROMと、同ROM自身の通常save APIで新規生成した標準Lv.100攻撃型6体セーブをiPad版RetroArch／mGBAへ安全に配置する。既存Stage58以前のROM／save、savestateを上書きせず、端末固有情報をtracked成果へ残さない。

## 受入条件

- [x] `docs/IPAD_RETROARCH_MGBA_SAVE_PLACEMENT.md`の正本手順を配置前に確認する。
- [x] `config/test_ready_save.json`をStage59 exact ROMと同一basenameへ更新し、ROM自身の通常APIで131,072-byte saveを独立2 process生成する。
- [x] full save、slot 0／1 fresh-load、自然Continue、Codex受付、進行flag、badge、Lv.100攻撃型6体をmGBAでPASSする。
- [x] RetroArchを通常終了し、残存process 0を確認してから書き込む。
- [x] active application containerとlive `retroarch.cfg`からROM directory、`savefile_directory`、sort設定、mGBA save directoryを都度一意に解決する。
- [x] ROMとsaveを一時名で転送し、iPad側size／SHA-256確認後に同一basenameへ原子的に確定する。
- [x] 同名既存成果が異なる場合は日時付きで保全し、既存Stage58 ROM／saveを不変に保つ。
- [x] iPadからROM／saveをread-backしてsourceとbyte一致、一時ファイル0を確認する。
- [x] 端末IP、credential、container UUID、端末固有絶対pathをtracked成果へ記録しない。
- [x] focused test、task graph、private guard、diff check、ログ／version／状態更新、完了commitをPASSする。

## 完了証跡

- ROMは`59_wild_identity_npc_regression_repair.gba`、33,554,432 bytes、SHA-256 `8ed4c9597fa73e9b30afd940d3855f99c4759297d9f48e584eaf9df8c3a303da`。
- saveは`59_wild_identity_npc_regression_repair.srm`、131,072 bytes、SHA-256 `f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb`。Stage59 ROM自身から独立2 process生成し、full／slot 0／slot 1／自然ContinueをPASSした。
- RetroArch process 0、active metadata、live設定、mGBA save directoryを再解決した。同名既存Stage59成果は0件で退避0。iPad側確定後のread-backはROM／saveともsourceとbyte一致、一時ファイル0。
- iPad上のStage58セーブは以前の配置時identityから進行済みだったため、現在値をsession-localに固定して配置前後不変を確認した。既存Stage58 ROM／saveは変更していない。
