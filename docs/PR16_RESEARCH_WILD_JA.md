# PR16 釣り・生態調査の実RP稼得

PASS_FISHING_ECOLOGY_REAL_EARNING_SCOPED

## 実装・限定受入

候補26dac23c/33554432bytesは不変。研究用の新runner・独立oracle・65検査を実装。釣りは港map3/38 (94,10)で通常BagからSuper Rodを使い、未捕獲種から逃走後、別の実遭遇をMaster Ballで捕獲。生態はmap3/63 (14,11)の通常BagからレーダーHIDDENを選び、逃走後の再使用でも前回のカーソル位置4を読み、不要なDOWNを送らず捕獲へ進む。敵/PID/RNG/捕獲結果/RPはhost注入しない。

RPは0→4/0→10、各daily/lifetimeとnext transactionを全64byte ownerで確認。逃走で台帳/手持ち/Bag/Flash/counterは不変。捕獲では1体増加しMaster Ballが20→19、他の全Bag項目と5party枠は不変。取引自身の保存後に新coreで通常Continueし、2KiB台帳・全party600byte・全Bag・全Flash・counter5を保持。手動Saveは0。開始map/進行/道具/leadはfixtureであり自然到達の証明ではない。

T24 RewardEncountersV2のtyped credit保存1回がT23研究のphase1/phase2保存2回に先行する。generation+1・factory.transaction_id+1・釣りHABITAT credit0又は生態RANDOM credit3の+1を別所有者の正規差分として厳密に検査し、研究外ledger全域を無条件除外しない。

## 原本・失敗・再利用

`content/modernization/pr16_research_wild_local_evidence/development.json` にlocal native5回（成功2/失敗2/外側tool打切り1）とstrict host compile4回を保存。先行Actions36273917599は定義不足でcompile1失敗/native0のまま保持。合計host compile5、ARM0、既受入native再実行0。初回釣り失敗はT24差分を省いた検証側の過剰制約。生態失敗は保持カーソルを無視した入力側不具合。打切り原stdoutは未回収でありPASSへ昇格しない。

成功釣りlocal#2・生態local#5のstdoutはbyte不変で公開。10PPMを目視し、成功原本のhashと一致。65新検査は全行欠落/重複・owner128変異・型・捕獲個体・保存分担・画像・過大主張などを拒否。独立oracleは全ledger4状態×2活動を再構成する。記録時unit/native/compileを再実行せずsource拘束済み原本を再利用。

釣り成功後の変更はecology専用の到達不能分岐とローカル初期化だけ。`ecology-only-source.diff.txt` と `fishing-reuse.json` でfishing側の全到達コードが不変と照合したため、釣りは再実行しない。

## Actionsと再開

Actions記録終端確認: True。`record_run_id` は今回記録runであり実行中に自己successとは記録しない。確認済み前回runは `content/modernization/pr16_research_wild_local_evidence/actions-36276059655.json`。一般CIの既存失敗/保留と限定native PASSを分離する。

釣り0→4RP/生態0→10RPの実稼得・逃走無加算・T24 typed credit併存・取引だけのfresh Continueを限定受入。次はGAME_CORNERの実配当→3RP、通常進行の受付/ショップ接続、残るnative文言。写真/虫取り/採掘/釣り/生態/BP/P08の無変更native再実行は禁止。日内上限・既捕獲種の実経路をこの2caseだけで全受入したと主張しない。
