# USER-20260829-STAGE60-IPAD-ROM-SAVE-PLACEMENT — Stage60 ROMと標準QAセーブをiPadへ配置する

- Status: `DONE`
- Lane: `qa/save/ipad/release-ops`
- Depends on: `USER-20260829-STAGE59-WILD-SPECIES-ROOT-REPAIR`、`USER-20260829-STAGE59-IPAD-ROM-SAVE-PLACEMENT`
- Queue ID: `USER-20260829-STAGE60-IPAD-ROM-SAVE-PLACEMENT`
- Baseline: Stage60 / ROM SHA-256 `3f9983eb099c2ca7205c14047460c8b2ed73a6180bd2a131a09c74af9d359ff1`

## 目的

Stage60 ROMと、同ROM自身の通常save APIで新規生成した標準Lv.100攻撃型6体セーブをiPad版RetroArch／mGBAへ安全に配置する。既存Stage59以前のROM／save、savestateを上書きせず、端末固有情報をtracked成果へ残さない。

## 受入条件

- [x] `docs/IPAD_RETROARCH_MGBA_SAVE_PLACEMENT.md`の正本手順を配置前に確認する。
- [x] `config/test_ready_save.json`をStage60 exact ROMと同一basenameへ更新し、ROM自身の通常APIで131,072-byte saveを独立2 process生成する。
- [x] full save、slot 0／1 fresh-load、自然Continue、Codex受付、進行flag、badge、Lv.100攻撃型6体をmGBAでPASSする。
- [x] RetroArchを通常終了し、残存process 0を確認してから書き込む。
- [x] active application containerとlive `retroarch.cfg`からROM directory、`savefile_directory`、sort設定、mGBA save directoryを都度一意に解決する。
- [x] ROMとsaveを一時名で転送し、iPad側size／SHA-256確認後に同一basenameへ原子的に確定する。
- [x] 同名既存成果が異なる場合は日時付きで保全し、既存Stage59 ROM／saveを不変に保つ。
- [x] iPadからROM／saveをread-backしてsourceとbyte一致、一時ファイル0を確認する。
- [x] 端末IP、credential、container UUID、端末固有絶対pathをtracked成果へ記録しない。
- [x] focused test、task graph、private guard、diff check、ログ／version／状態更新、完了commitをPASSする。

## 完了証跡

- ROMは`60_wild_species_root_repair.gba`、33,554,432 bytes、SHA-256 `3f9983eb099c2ca7205c14047460c8b2ed73a6180bd2a131a09c74af9d359ff1`。
- saveは`60_wild_species_root_repair.srm`、131,072 bytes、SHA-256 `f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb`。Stage60 ROM自身から独立2 process生成し、full／slot 0／slot 1／自然ContinueをPASSした。
- RetroArch process 0、active metadata、live設定、mGBA save directoryを再解決した。同名既存Stage60成果は0件で退避0。転送後の再起動1回は正規確定前のprocess gateで拒否し、再停止後に原子的に確定した。
- iPad側確定後のread-backはROM／saveともsourceとbyte一致、一時ファイル0。既存Stage59 ROM／saveは配置前後で不変だった。
