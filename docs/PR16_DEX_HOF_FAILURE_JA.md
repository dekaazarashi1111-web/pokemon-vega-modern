# PR16 HOF保存失敗の局所通知

正式ROM/Save101を保持し、現Union候補からHOF通知だけを修復する。全保存modeや共通SaveFailed全callerの受入ではない。

実HOF taskは保存返値を捨て、直後にSE_SAVEを鳴らして32frame後に演出へ進む。失敗すると旧SaveFailedがtiles16KiB/video-stateを拡張owner上へ退避し、さらにgDecompressionBufferのHOF二sector payloadを表示scratchで上書きする。自動retryのHandleSavingData(mode3)は殿堂入り回数を再度増やす。tiles移設だけでは閉じない。

## 局所契約

- mode3かつQOL経由の署名済みHOF callerだけ、inner結果/実damaged maskを見て旧SaveFailedを起動せず失敗を返す。maskを消さない。stale sector31のみはmain成功時に外側の実write/readbackへ渡す。
- 外側QOLも終わったgSaveAttemptStatusが1の時だけ、元SE_SAVE/32frame/演出を保持する。
- 非1は既存HOF window0へ既存2行エラーを表示する。新規Aまで待ち、Bや方向だけでは解除しない。A後は元のStartDisplayingMonsへ進む。InitTeamSaveDataやTrySaveDataへ戻らず、再append・自動retry・回数再増分をしない。
- 初回保存のstat10増分を戻さない。main commit後に外側だけ失敗した場合のRAM/Flash不一致を作らない。初回のHOF二sector/main/外側は原子transactionとして受け入れない。
- 新mutable ownerなし。元task frame、r4–r11、SP、他task、HOF payload、全拡張ownerを保持する。同期描画callだけSPを8byte整列する。

## 検証と境界

隔離試験は元HOF taskと実QOL/inner ARM chainを使い、保存driver/描画のみstubにする。12失敗/成功形、16task、3stale attempt、2SP条件、署名scope陰性を分離する。隔離PASSは実HOF画面・殿堂入り・Flash保存成功を意味しない。

UI検証を行う場合はSave101私有copyの有限入口fixtureを全byte記録し、故障解除以外は通常入力を使う。元HOF payload、拡張20248byte、保存回数、attempt、音、旧SaveFailed/wipe/retry非到達、別process coldを確認する。自然リーグ到達、全HOF種族の9bit ABI、初回mode3の原子性へ広げない。

残件はmode4/5/default/全caller、共通SaveFailedの安全契約、stale selector authority wipe、早期sector31故障/単bank原子性、残typed consumer。正式切替はowner計画に照らした必要証拠が揃うまで保留し、承認不足と読み替えない。最終milestoneはシオウPokecenter通常回復/Save/独立coldContinue。雑魚ごとのSaveを復活させない。
