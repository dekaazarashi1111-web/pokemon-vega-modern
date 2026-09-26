# Issue19: CFRU初回呼出しの表混在を修復

状態 `PASS_REPAIRED_CFRU_FIRST_CALL_ENTRY`。実測run35853901025、source `190a25a6032827d4a060d6d93c98db98da9eb9be`。
候補 `8946438bc37fda468c53e41378a6f82fac8f0b1af7ac6785ef07ca708c2714a1`。親 `6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2`。

## 実装と原因

実操作で最初の技だけ未接続CFRU入口から旧表を読み、次回からPLR1を読むことを命令単位で確認。
バタフリーLv12は原本[77,78,79]に対し旧/新混在では[77,79]になる。原本や期待値は変更しない。
既存CFRU通常習得入口 `0x09114038` の8bytesだけを既存通常adapter `0x09377729` へのThumb tail jumpへ置換。
保存ROMは `scripts/pr16_learnset_battle.py` の既存restoreで復元し、このscriptの `apply(parent)` を適用してcheckpoint候補hashを照合する。
新ROM/saveの追跡、全ARM再build、新規allocation、global table root/技表、active baselineの変更はない。

## 検証と範囲

新境界試験26、新native11、成功11/11、今回fresh core22。
以前の受入8件はfirst-call入口が変わるため変更影響があり、今回8件を新候補で再検証。
無関係な受入済みBag23/戦闘/egg8/代表画面/旧host/旧ARM/Wikiは再実行0。元の31境界試験は保存結果を継承。
通常Bagアメ、空き枠/置換/拒否/summary取消/既習得/閾値未満、2進化、同level3行/既習得後の継続/連続拒否を対象。
3区間の7API書込barrier、通常Save、新core Continueで100bytes・PP・道具消費を検査。
初期個体/道具/進行はfixtureなので、自然生成の初期技、戦闘EXP由来level-up、全ownerの受入へ拡張しない。

Actions終端確認: `True`。原本とrecipeは `content/modernization/pr16_learnset_entry_repair_evidence/35853901025`。
旧失敗3回と旧8成功を上書きせず保持。正本 `content/modernization/pr16_learnset_entry_repair_checkpoint.json`。

## 次

Issue19: このentry repair候補を保存parentへapplyして使用する。成功した通常アメlevel-up/進化11caseは再実行せず、自然生成の初期技と戦闘EXP由来level-upの未受入経路へ。Bag23/既存戦闘/条件付きegg8/代表画面/旧4hook/旧host/ARM/Wiki/PLA1/PLC2は影響なし・再実行しない。全owner/Issue19/release/active baseline切替は未完。
