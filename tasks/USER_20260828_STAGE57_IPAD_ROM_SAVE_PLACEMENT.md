# USER-20260828-STAGE57-IPAD-ROM-SAVE-PLACEMENT — Stage57 ROMと標準QAセーブをiPadへ配置する

- Status: `IN_PROGRESS`
- Lane: `qa/save/ipad/release-ops`
- Depends on: `USER-20260827-STAGE56-COMPREHENSIVE-DEBUG-REPAIR`、`USER-20260827-STAGE56-OVERPOWERED-QA-PARTY`
- Queue ID: `USER-20260828-STAGE57-IPAD-ROM-SAVE-PLACEMENT`
- Baseline: Stage57 / ROM SHA-256 `546136a6baa26efd7a70c2b6826bf902c4841a4a1113cb53bfdc44c77971663d`

## 目的

Stage57 ROMと、同ROM自身の通常save APIで新規生成した標準Lv.100攻撃型6体セーブをiPad版RetroArch／mGBAへ安全に配置する。既存Stage56以前のROM／save、savestateを上書きせず、端末固有情報をtracked成果へ残さない。

## 受入条件

- [ ] `docs/IPAD_RETROARCH_MGBA_SAVE_PLACEMENT.md`の正本手順を配置前に確認する。
- [ ] `config/test_ready_save.json`をStage57 exact ROMと同一basenameへ更新し、ROM自身の通常APIで131,072-byte saveを独立2 process生成する。
- [ ] full save、slot 0／1 fresh-load、自然Continue、Codex受付、進行flag、badge、Lv.100攻撃型6体をmGBAでPASSする。
- [ ] RetroArchを通常終了し、残存process 0を確認してから書き込む。
- [ ] active application containerとlive `retroarch.cfg`からROM directory、`savefile_directory`、sort設定、mGBA save directoryを都度一意に解決する。
- [ ] ROMとsaveを一時名で転送し、iPad側size／SHA-256確認後に同一basenameへ原子的に確定する。
- [ ] 同名既存成果が異なる場合は日時付きで保全し、既存Stage56 ROM／saveを不変に保つ。
- [ ] iPadからROM／saveをread-backしてsourceとbyte一致、一時ファイル0を確認する。
- [ ] 端末IP、credential、container UUID、端末固有絶対pathをtracked成果へ記録しない。
- [ ] focused test、task graph、private guard、diff check、ログ／version／状態更新、完了commitをPASSする。
