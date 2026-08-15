# Save compatibility — v1.4.0

## 推奨

新規ゲームを推奨します。patch適用前に元ROM、battery save、emulator設定を別の場所へbackupし、
新旧ROMで同じsaveを同時に開かないでください。

## 対応範囲

- 新規save: 対応。2,048-byte version 1 ledgerを初期化する。
- 検証可能な旧Vega battery save: 条件付き対応。既存sector signature/checksumが正しく、
  ledger未作成の場合だけ一度migrationする。
- 本releaseの通常save/load/reset: 対応。トーホクとカントーの進行、QOL、Factory、
  pending encounterをversioned ledgerへ保存する。
- v1.2.0〜v1.3.9 battery save: 対応。ゲーム内saveをv1.4.0で読み込むと、既存2 KiB台帳の
  予約領域へ取得台帳を一度だけ初期化する。先に旧版側でゲーム内saveを完了してからROMを切り替える。
- emulator savestate: version間の互換対象外。ゲーム内saveから再起動する。
- 他hack、英語版、FireRed Rev.1、不明な拡張save: 非対応。

v1.3.7の不具合版でキャタピーを**捕獲して保存した場合だけ**、切替前にそのROMで当該個体を
逃がしてゲーム内saveを作り直す。遭遇しただけ、または捕獲せず終了した場合は対応不要。
不具合版がキャタピーへ誤ってタマゴ予約ID 412を保存していたため、その1種類だけ自動移行しない。

未知magic/version、size不一致、ledger checksum不一致、非zero予約領域はfail-closedで拒否する。
Vega badge/HM/story flagは既存領域に残し、Kanto認定章・地方anchor・League・共有捕獲stateとは
分離する。migration前の高位flagはwhitelistだけを移し、bitmapや変数を一括copyしない。

## 電源断と施設復旧

Factoryは参加前party 6体を完全snapshotし、BP・連勝・一回報酬を同じtransactionへ保存する。
勝敗、棄権、退出、reset、suspend、blackoutの全経路でpartyを復旧する。施設外捕獲NPCは
空き容量確認後に個体と支払い状態を先に確定し、reset後も同じ個体から再開する。捕獲完了時だけ
pendingを消す。Mirageの仮想item/stateはFactoryと共有しない。

v1.3.9のFactory Trialは2,048-byte ledgerをCFRU-JPのsector 31 payloadへ直接確定する。
ROM実行時の2 KiB rollback像はEWRAM `0x0203E400..0x0203EC00`へ置き、GBAの小さい
call stackへ積まない。入場前partyは6×100 byteで、完走・敗北・辞退・selection cancel・
保存後復旧のいずれも同じ像から一度だけ戻す。

## v1.3.9 QOLの保存境界

- HM01〜HM08のフィールド能力はバッグ所持から毎回導出し、新しいflagやsave fieldを持たない。
- わざメモリーの通常／タマゴ技modeはEWRAM `0x0203EC00`の1 byteだけを使い、終了、cancel、
  resetで0へ戻す。Flashへserializeしない。
- 1個目のバッジ報酬を通過済みでわざメモリーを持たない既存saveは、シオウの技管理NPCが
  Item 347を1個だけ補う。キノコやものまねハーブを消費したという履歴は追加しない。
- 外来生態modeは既存CFRU拡張Var `0x51FF`へ0（RTC自動）〜4（隠れ探索）で保存する。
  新しいFlash sectorやledger fieldは追加しない。不正値はRTC自動へ戻す。
- 1個目のバッジ報酬を通過済みでせいたいレーダーを持たない既存saveは、同じシオウNPCが
  Item 348を1個だけ補う。
- 旧版のemulator savestateは非互換。v1.4.0起動前にゲーム内saveへ戻す。

## v1.4.0 取得台帳

- 既存2,048 byte台帳の予約領域へ、4 byte境界で240 byteの`VACQ` version 1 blockを置く。
  後続のFactory・遭遇・Raid・QOL field offsetは変更しない。
- v1.3.9以前の当該領域は全zeroだけをlegacyとして受理し、初回取得イベント利用時に初期化して
  outer/inner CRCを更新し、sector 31へ直接確定する。未知magic/version/size/CRCは拒否する。
- 取得済みbit、捕獲戦・ギフト・タマゴ・化石のpending transactionを同時に保存する。
  捕獲は捕獲確認後だけcommitし、撃破・逃走・resetではpendingを解消して再挑戦可能にする。
- タマゴは受取時に取得済みbitを確定するが、Speciesの図鑑登録は孵化script完了時だけ行う。
  未孵化のままsave/loadしても図鑑登録されず、孵化後の登録は通常saveと取得台帳の双方へ残る。
- 手持ち満杯時は既存14箱のPC領域へ送り、全収納満杯時は個体・道具・claimを変更しない。
  保存失敗時は渡した個体または消費した道具をrollbackし、再開可能なpendingを保持する。
- 個体・手持ち・PC・図鑑は標準save slot、取得台帳はsector 31へ保存する。標準save/load後に
  sector 31を再読込して台帳を復元し、両領域を跨ぐtransactionの途中状態を残さない。

## v1.3.4から切り替える場合

提供された `vega-modern-kanto-v1.3.4-verified.srm` は通常のbattery saveとして検査でき、
v1.4.0でも利用できる。Delta環境やこのbattery saveが、表示Type・通知ループの原因ではない。
v1.3.4では戦闘中の技画面でLを押すとFR由来の旧HELPが先に開き、CFRUの一時戦闘領域を
上書きするROM統合不具合があった。v1.3.9では戦闘中だけ旧HELPを抑止し、CFRU技詳細へLを渡す。

1. v1.3.4でゲーム内saveを作り、battery saveを別名でbackupする。
2. v1.4.0へ切り替え、savestateではなくゲーム内saveからRestartする。
3. 表示破損や通知ループが起きた後に作られたAuto/General/Locked stateは再利用しない。
4. 症状が残る場合だけ当該stateを削除し、battery saveまたはNew Gameから開始する。

Deltaの再installや全state削除は通常不要で、アプリ全体の再installは他gameの保存データを
失う可能性がある。別emulatorへ移す場合もsavestateはimportせず、battery saveまたは
New Gameから開始する。Deltaでの音声不具合は今回の戦闘HELP競合とは別問題である。

2026-08-15に追加受領した `vega-modern-kanto-v1.3.5-verified 2.srm` は
131,072 byteがすべて `FF`で、battery saveのsectorやプレイデータを含まない。
このファイルから進行を復元したり、個別の戦闘UI状態を再現したりすることはできない。
実際にゲーム内セーブを行った後の `.srm` か、New Gameを使用する。

saveが拒否された場合は書き込みを繰り返さず、backupへ戻して新規saveを開始してください。
