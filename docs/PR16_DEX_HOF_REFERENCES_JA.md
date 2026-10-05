# 残参照の有限型根と共有delta

## 範囲

現候補0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583（32MiB）の旧egg15118byte領域に向く全874見かけ参照を継承する。前段の619分類/255未知と4,063,919byte証拠を改作・複製せず、固定size/SHAのbaselineから新25件だけを共有witness付きdeltaとして記録する。完了値は専用checkpointと終端Actionsを正とする。

対象は次の25件。

- JP Trainer structのname末尾3byteと最初のitem下位byteを跨ぐ15件。original743行とStage31/32/33の各1367行、Stage35の4284行を固定serializer・全table/row/header・最新actual ownerへ束縛する。C宣言のname[6]と型alignmentからitems+10/party+28を使い、残っているUS版offsetコメントは根拠にしない。
- T16自己記述archiveのzlib stream内2件。全owner、56byte header、TOC+body SHA、22fileの連続被覆・各圧縮終端・全展開size/SHAを確認する。TOC/paddingを圧縮dataへ含めない。
- Stage74の1件。固定source ScriptのCALLNATIVE根から、PUSH→BL→BL→LDRの12byteを個別解読する。0x0953A203開始4byteは後半BLとLDR命令に跨る。型領域は必要な6byteだけ。literal poolや関数全体をcode認定せず、後続別関数hookにより歴史的512byte窓が異なる事実も保持する。
- JP song4根によるPCM7件。HOF明示ID98、source move60/39の短いanimation prefixから182/160、既routeで観測したmap[3,24]のMapHeader+16から294だけを追加する。JP song/map表長をUS版や未確定IDから推定しない。

これらは歴史的型・静的consumerの分類。実ゲーム到達・演奏・全runtime読取範囲の受入ではない。

## T09上位wordを未知として残す理由

species348のrow+8は、第3u32に見かけBLがある。現wrapperの上位8byte zero検査が読むのはPLC2 imageから返るviewであり、旧T09表ではない。旧tutor<64条件、redirected入口、wrapper全体、PLC2 root/readerとactual ownerを現候補へ束縛し、この別表consumerをT09の型証拠へ流用しない。

## 共有参照証拠

- baseline: `content/modernization/pr16_dex_hof_typed_recovery_evidence/egg-typed-audit.json`
- delta: `content/modernization/pr16_dex_hof_reference_evidence/reference-delta.json`
- checkpoint: `content/modernization/pr16_dex_hof_reference_checkpoint.json`
- materializer: `scripts/pr16_dex_hof_reference_delta.py`

baselineは末尾LFを含む全size/SHAで照合。変更行は元のaddress/target/kind/size/SHA・順序を保持し、旧acceptedを変更できない。witnessは一意ID参照と型ごとの正確な幾何範囲、canonical evidence/proof SHA、closed schema、2MB上限で制約する。自己hashだけを信頼せず、record時は独立measurement.delta_identityでdelta全bytesを照合する。全874行は計算時だけmaterializeし、artifactへ再複製しない。

追加曲は既126曲を含む130曲を新しいcross-song役割安全性scopeで一回だけモデル検証する。既曲を新たに受入したと数えない。保存証拠には採用assetへ結び付かなかった全VOICE/keymap/失敗read等が揃っていないため、保存窓だけで競合保護を再現しない。旧sample identity全件保持、新readと旧accepted hitの非衝突、新旧全曲のsample/command競合拒否を要求する。

## Actionsと公開契約

`pr16-dex-hof-references.yml`はsource guard、新規拒否tests、既存private入力からの現候補read用再構成1回、全115owner/874hit束縛、測定、記録、固定再開MD/JSON・両ログ、非force push、全byte/LF読戻しを行う。旧全ROM inventory、heap/native、正式ROM/Save101更新は0。

producer/guard/upload/consumerのpath・artifact名は一致を必須にする。guard成功時だけ専用flat directoryをuploadする。hidden/symlink/未知filename/未知拡張子/binary/空textを拒否。各file4MB未満、delta2MB以下、全量12MB未満を測定後とcommit前の実snapshot bytes、upload前に検査する。公開はsource・最小address-size-SHA・textのみ。

## 次の境界

残230の未知、間接参照・旧egg退役完全性が未完。全未知0でもdonor利用は別の明示ゲートが必要。donorは未使用。全115 ROM owner、52save subowner、保存側残804byteを維持する。

HOF32sector Ccontrollerの実owner配置、全S61E/MDX writer/loader/Link exact-source/no-main/INITIAL、mode/早期31/species9bit、全保存入口のheap-ready・同期非再入・全出口Freeが必要。heap13352byteは保存退避53300byteを跨いで保持しない。その後、正式候補切替、trainer131後半、最終シオウ通常回復・保存・独立cold Continueへ進む。雑魚戦ごとの保存は再導入しない。

既知QOL source不一致の一般CI失敗、action_required/job0、Stage79成功cache/native0は本scopeの成否と分離する。merge/release/baseline切替は行わない。
