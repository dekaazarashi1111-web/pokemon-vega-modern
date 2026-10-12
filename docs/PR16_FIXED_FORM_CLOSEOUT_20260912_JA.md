# PR16 fixed-form 5ケースの原本集約 — 2026-09-12

## 正本と完了ゲート

現在の受入判定は `content/modernization/pr16_fixed_form_acceptance.json` と対応する `pr16_fixed_form_acceptance_receipt.json` を正本とする。原本照合・Git index/HEAD読戻し・正式JSON/P08同期が成功するまでは、この文書だけでgapを閉じない。

`python3 scripts/pr16_fixed_form_closeout.py --check` が `PASS_FIVE_CASE_CLOSEOUT` を返す場合、同一候補に紐づく以下5ケースのphysical acceptanceが成立する。これはP03 fixed-formの有限契約の完了であり、最終配布候補へのP08移送やreleaseの完了ではない。

候補: SHA-256 `e630f7f199194fb4b531ff3a561da866902aea200770a832aec5c276e1636267`、33554432 bytes、CRC32 `BFB089F9`。今回の集約はROMを変更しない。

## 再実行せず保持する5ケース

| ケース | 原本run / job | 境界 |
|---|---|---|
| necrozma-decline-unchanged | 34694218218 / 103554787890 | FORM 245/246の両行でnative取消、party bytes完全不変、Save2→2 |
| zacian-crowned-battle-roundtrip | 34695512247 / 103558198010 | Rusted装備→自然遭遇→Crowned/技768→技使用→base/Iron Head405復帰→実装備置換→次戦への非漏洩→Save2→3→fresh Continue |
| zamazenta-crowned-battle-roundtrip | 34695512247 / 103558198010 | Rusted装備→自然遭遇→Crowned/技769→技使用→base/Iron Head405復帰→実装備置換→次戦への非漏洩→Save2→3→fresh Continue |
| necrozma-dusk-mane-four-slot-roundtrip | 34698120000 / 103565021381 | 実N-Solarizer→相方→実4枠選択→技690→Save/Continue→解除→技枠圧縮→相方完全復元→実party UI→再Save/Continue |
| necrozma-dawn-wings-four-slot-roundtrip | 34698120000 / 103565021381 | 実N-Lunarizer→相方→実4枠選択→技669→Save/Continue→解除→技枠圧縮→相方完全復元→実party UI→再Save/Continue |

最新Necrozma成功の実行HEADは `a552361a250ff1a01afb4f328c5bfef8a329775e`。既存runは2026-09-12 14:04 UTCに成功済みだった。再開時点のPR本文と3/5 JSONだけを見て古い失敗を繰り返さず、成功原本から進める。

選択した成功は5独立process、合計11 fresh cores。原本3run全体の試行は9processであり、最初のrunの他4ケースは失敗のまま保存する。全履歴を網羅する件数とは主張しない。**集約・原本保存・再照合による新規emulator実行は0。**

## Necrozmaのnative ownerを混同しない

FORMサービス245/246は種族遷移の入口である。一方、4枠で固有技を選び、相方を退避し、解除時に戻すownerはN-Solarizer697/N-Lunarizer698である。合体2ケースは `entry_kind=NATIVE_FUSION_ITEM`、`form_service_selection_claimed=false` を維持する。既存FORM取消は別入口の対照であり、Nアイテム自体の取消・不成立を実行したと読み替えない。

4枠の実技選択でPhoton Geyser733を忘れ、固有技690または669を入れる。解除時は固有技を削除し、残る技・PP・PP Bonusを圧縮する。native ownerにないPhoton Geyser自動復元を製品へ追加しない。

合体後の1回目Save/コア破棄/fresh Continueで200 party bytesを検査する。解除時は相方100 bytesの完全一致を確認する。nativeのparty-count cacheは実Pokemonメニューを開くことで2→3へ更新されるため、controllerはRAMへcountを書かず、Start→Pokemonの実UIを通す。2回目Save/新コアContinueで300 party bytesとcount3の一致を検査する。各ケースのSave counterは2→4、manual saves2、fresh cores3。

## 原本の保持

原本ZIPは `content/modernization/pr16_fixed_form_acceptance_evidence/<run>/original.zip`。各runの `actions.json` と集約receiptを併読する。

| run | ZIP bytes | SHA-256 |
|---|---:|---|
| 34694218218 | 802643 | 45fbc581ec17cf7e0504d2c8d3150072e44a9099e4deed04da759d8b3a6328c7 |
| 34695512247 | 854855 | 0d31881c45e05e9aa4b3c122663ce3bfd7605ff4287299a602c48232dc893cc8 |
| 34698120000 | 1055169 | 3a2b3faa1ef98e2ddfde2ca1ef32bbcdc90e92469e53b6016d9700a286344c64 |

latest artifact10299506555の旧expiryは2026-12-11T14:02:42Z。保存工程はouter ZIP digest、nested source、receipt全member、stdout/stderr/process、7 host-write rejection、実行HEADのGit sourceを検証する。ROM/save/private input archiveは許可しない。

ZIPはignore対象なので、検査済みexact pathだけを `git add -f` する。indexとHEADの `git show` から再読して原本byte一致を確認する。過去の3/5正本は最新runディレクトリへcreate-onlyで保存し、原本側の `p03_fixed_form_gap_closed=false` は改変しない。5/5という新しい集約結果だけがgap閉鎖を主張する。

## 検査コマンド

```sh
python3 -m unittest tests.test_pr16_fixed_form_closeout -v
python3 scripts/pr16_fixed_form_closeout.py --check
```

最初の原本移送・正本同期は `.github/workflows/pr16-fixed-form-closeout.yml` に限定する。これはsource/evidence-onlyであり、mGBA、ROM再生成、private release input復元を実行しない。re-run時も既存原本・同じ正本を照合し、同じログを重複追記しない。古いHEADからのpush、履歴改変、baseline変更は許可しない。

## 残作業

このgapが閉じた後のformal physical gapはP05通常リング取得・BP獲得・policy選択の3件とCircus受付の1件。さらにP08のFINAL_NATIVE_ACCEPTANCEとRELEASE_DECISIONが残る。

開始時の進行・party・場所・Nアイテム/Rusted装備/Bagはfixtureであり、通常供給を証明しない。generic FORM/Rotom等の既存成功を保持する。P07も親候補でcomplete/固有gap0のままで、最終SHAへの移送だけを残す。fixed-form成功を理由に `full_p03_acceptance`、`release_ready`、`active_baseline_changed` をtrueにしない。draft解除・merge・release・baseline切替はownerの別判断。
