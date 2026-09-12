# PR16 通常供給の再開点 — 2026-09-12

## 現在の正本

`content/modernization/p08_remaining_work.json` と、各分野の acceptance/receipt を正本とする。古いPR本文・過去の失敗runだけから再実行を開始しない。

- P03 fixed-form: `pr16_fixed_form_acceptance.json` / `pr16_fixed_form_acceptance_receipt.json`。同一候補の正式5ケース完了、固有physical gap閉鎖済み。
- P05/Circus owner: `pr16_p05_supply_owner_findings.json` / `pr16_p05_supply_owner_receipt.json`。誤ったF0解読とraw403A探索を繰り返さない。
- BP受付対照: `pr16_bp_native_controls_acceptance.json` / `pr16_bp_native_controls_receipt.json`。native取消1ケース完了。BP獲得そのものは未受入。
- 保存確認run: `pr16_fixed_form_closeout_run.json`、`pr16_p05_supply_owner_retention_run.json`、`pr16_bp_controls_checkpoint_run.json`。

この一連の作業によるROM変更は0。使用候補はSHA-256 `e630f7f199194fb4b531ff3a561da866902aea200770a832aec5c276e1636267`、33554432bytes、CRC32 `BFB089F9`。後続の修正が入ればsuccessorと変更影響台帳を別に作り、旧成功JSONのcandidateを書き換えない。

## 重複実行を防ぐチェックポイント

| 証拠 | 実行run | この段階での実行件数 | 扱い |
|---|---:|---:|---|
| fixed-form 5ケース原本集約 | 34700181342 | 新規emulator0 | 既存5成功process/11coresを再検証して閉鎖 |
| P05/Circus owner静的診断 | 34701044310 | emulator0 | exact ROMと66sourceの静的証拠 |
| owner原本保存 | 34701887665 | emulator0 | Git index/HEAD読戻し済み |
| BP最初の前処理 | 34702872369 | emulator0 | 誤ったdirect-entry仮定をfail-closedで拒否。failureのまま保存 |
| BP実受付→取消 | 34703571879 | 新規1process/1core | `reception-cancel-unchanged` 成功 |
| BP原本保存 | 34703998596 | 新規emulator0 | 8focused tests、Git index/HEAD読戻し済み |

同じ受付取消の再実行は、関連ROM範囲や観測契約の変更がある場合の回帰に限る。BPのレンタル・勝利・報酬・敗北・繰返し・保存・実消費は、この取消1ケースで代替しない。

## BP: 実受付に到達し、取消対照は成功

実NPCはmap96/5、local ID2、座標(20,19)。初期fixture位置は(20,20)。最初の入口はFactoryへの直接callnativeではなく、後発のCodex受付である。

```text
native NPC interaction
  0x093CDA80: 「Codexたいせんを しますか？ いいえで ファクトリーへ」
  native「いいえ」
  0x093CDA9C: goto 0x093C9390
  0x093C9390: lock / faceplayer / FactoryHighModesV2_FieldReception / waitstate
  実tier menu: トライアル / スタンダード / やめる
  native Bで取消
  idle fieldへ復帰
```

run34703571879/job103579472279、実行HEAD `7ebf7b34396ce70e0484be2e74514647b5e7ac56`。492観測frames、party600bytes・Bag・BP0・Save counter2→2不変、警告0。観測開始後の7host-write APIはすべて拒否試験済み。native stdin/result/process、67source、生成C、receipt全memberを照合し、fixture/Codex yes-no/tier/復帰の4画面を目視確認した。

通常Saveは0回、保存後fresh Continueは未実行、BP獲得は0。開始map/進行/party/空Factory ledgerはfixtureであり、通常進行からの到達を証明しない。

成功原本artifact10300567380、600246bytes、SHA-256 `e32b0e2b976d80c0ff46e45d78f265dd2f3d11e3f4a88bbb82da809a522c7a1b`。Git上の保存先は `content/modernization/pr16_bp_native_controls_evidence/34703571879/original.zip`。前処理failure34702872369も別ディレクトリで保持している。

## BP: 次はTrial入口の所有者を修正・確定する

`config/factory_high_modes_v2.json` には次の二つが同時に存在する。

```text
physical_binding.trial_script             0x092CF790
factory_trial_completion_chain.address   0x092CF791
```

現候補のTrial delegateは `0x092CF790` を指す。その現byteは

```text
23 c9 42 3c 09 0f 00 9c f5 2c 09 09 04 6c 02
```

であり、completion chainのcallnative、メッセージ、release/endである。レンタル6候補→3選択→3連戦へ入る受付scriptではない。そこで `rental-cancel-save-continue` を機械的に走らせても、既知の静的誤接続をなぞるだけになるため、今回の要求manifestから外した。レンタルケースのnative失敗を実測したとは主張しない。

次の調査では `scripts/build_facility_runtime.py` の `VEGAF20` payload headerのoffset44にある `script_facility_npc` pointer、Stage41時点の受付root、Factory High導入前のrootを照合する。`config/factory_high_modes_v2.json` の受付hookの旧pointerは `0x0938D4A4`。これは調査候補であり、実ROMのscript連鎖を検証せずそのまま置換してはいけない。

正しいscript入口を確定後、必要な最小ROM変更とsuccessor SHAを記録し、nativeレンタル選択・取消/復元・通常Save/fresh Continueへ進む。その後に実戦の勝利報酬、敗北/取消/未達成、初回/繰返し境界、同じ獲得BPを既存shopで消費する。基本Trialは3勝9BPだが、後発の初回/繰返しreward wrapperを含む実結果で判定する。

## Circus: 旧F0は未知opcodeではない

旧診断の経路は次のように確定した。

```text
map12/7 events0x083809C0
  counts = [3,3,116,108]
  coords pointer = 0x08000000（異常）
  coord18のscript pointer読取り位置 = 0x0800012C
  0x0800012Cはカートリッジheaderのback-sprite table pointer
  → 0x0954ECC4のsprite metadataをscriptとして誤解読
  → 0x0954ECDCのF0で停止
```

そのF0は4番目のsprite pointer `0x086C97F0` の下位byte。連続6件の `<pointer, size=0x0800, tag=0..5>` と照合済み。共有decoderへ新opcode長を足したり、後続byteへ再同期したりしない。6invalid rootsは異常event headerの記録として保持する。**map12/7をCircusと同定したわけではない。**

さらに、upstreamのVarGet(0x403A)はprojectの `scripts/build_battle_core.py` によって `VegaFacilityStateGet(VEGA_FACILITY_STATE_NUMBER)` へ変換される。実際の施設番号3、`BattleSetup_StartTrainerBattle`、`sp072_LoadBattleCircusEffects` のowner連鎖から正規入口を追う。raw403Aだけの探索や直接書込みを入口受入と扱わない。

## Ring / policyとP08

Ring580はwork-variableマクロも含めて調べたが、今回のreachable一致はmap98/69のremoveitemだけ。未発見は不存在の証明ではない。設計正本はSTORY_EVENT / FINAL_LEAGUE_CLEAREDであり、generic shopからは供給しない。native/special/story ownerを追う。以前のaudit helperのline83をNPC giverと見なさない。

policyのtrainer-authored設定やfixtureは通常プレイヤーの選択UIではない。許可/不許可/取消/cold Continue/再選択を正式入口で確認する必要がある。

残るformal physical gapはRing、BP獲得、policy、Circusの4件。P08のFINAL_NATIVE_ACCEPTANCE、RELEASE_DECISIONも未完。generic FORM/Rotom/P07等の完了を保持し、P07は最終候補への移送だけを残す。final候補固定、変更影響回帰、clean-ROM独立二重生成、配布パッチ往復検証は未完。

既存HEADにあったprivate guard違反は別のrelease阻害要因として保持している。今回追加pathの新規違反は0だが、全体guardがPASSしたとは主張しない。古いROM/save/BPS入り証拠を無断削除・改変していない。draft解除、merge、release、baseline切替は行っていない。
