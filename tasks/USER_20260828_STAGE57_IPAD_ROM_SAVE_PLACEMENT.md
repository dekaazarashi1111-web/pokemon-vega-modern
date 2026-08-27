# USER-20260828-STAGE57-IPAD-ROM-SAVE-PLACEMENT — Stage57 ROMと標準QAセーブをiPadへ配置する

- Status: `DONE`
- Lane: `qa/save/ipad/release-ops`
- Depends on: `USER-20260827-STAGE56-COMPREHENSIVE-DEBUG-REPAIR`、`USER-20260827-STAGE56-OVERPOWERED-QA-PARTY`
- Queue ID: `USER-20260828-STAGE57-IPAD-ROM-SAVE-PLACEMENT`
- Baseline: Stage57 / ROM SHA-256 `546136a6baa26efd7a70c2b6826bf902c4841a4a1113cb53bfdc44c77971663d`

## 目的

Stage57 ROMと、同ROM自身の通常save APIで新規生成した標準Lv.100攻撃型6体セーブをiPad版RetroArch／mGBAへ安全に配置する。既存Stage56以前のROM／save、savestateを上書きせず、端末固有情報をtracked成果へ残さない。

## 受入条件

- [x] `docs/IPAD_RETROARCH_MGBA_SAVE_PLACEMENT.md`の正本手順を配置前に確認する。
- [x] `config/test_ready_save.json`をStage57 exact ROMと同一basenameへ更新し、ROM自身の通常APIで131,072-byte saveを独立2 process生成する。
- [x] full save、slot 0／1 fresh-load、自然Continue、Codex受付、進行flag、badge、Lv.100攻撃型6体をmGBAでPASSする。
- [x] RetroArchを通常終了し、残存process 0を確認してから書き込む。
- [x] active application containerとlive `retroarch.cfg`からROM directory、`savefile_directory`、sort設定、mGBA save directoryを都度一意に解決する。
- [x] ROMとsaveを一時名で転送し、iPad側size／SHA-256確認後に同一basenameへ原子的に確定する。
- [x] 同名既存成果が異なる場合は日時付きで保全し、既存Stage56 ROM／saveを不変に保つ。
- [x] iPadからROM／saveをread-backしてsourceとbyte一致、一時ファイル0を確認する。
- [x] 端末IP、credential、container UUID、端末固有絶対pathをtracked成果へ記録しない。
- [x] focused test、task graph、private guard、diff check、ログ／version／状態更新、完了commitをPASSする。

## 完了証跡

- ROMは`57_comprehensive_debug_repair.gba`、33,554,432 bytes、SHA-256 `546136a6baa26efd7a70c2b6826bf902c4841a4a1113cb53bfdc44c77971663d`。
- saveは`57_comprehensive_debug_repair.srm`、131,072 bytes、SHA-256 `3192100245672e13baa2d4398d115c2288758e901033e7b4c9830124164f90df`。Stage57 ROM自身から独立2 process生成し、full／slot 0／slot 1／自然ContinueをPASSした。
- RetroArchを通常終了してprocess 0を確認し、live設定から実ROM／mGBA save directoryを再解決した。同名既存Stage57は0件だったため退避0。iPad側確定後のread-backは両方sourceとbyte一致、一時ファイル0。
- 既存Stage56 ROM／saveは配置前後でbyte不変。端末固有情報とprivate save内容はtracked成果へ保存していない。
