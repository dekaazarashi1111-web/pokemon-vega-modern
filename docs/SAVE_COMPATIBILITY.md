# Save compatibility — v1.3.4

## 推奨

新規ゲームを推奨します。patch適用前に元ROM、battery save、emulator設定を別の場所へbackupし、
新旧ROMで同じsaveを同時に開かないでください。

## 対応範囲

- 新規save: 対応。2,048-byte version 1 ledgerを初期化する。
- 検証可能な旧Vega battery save: 条件付き対応。既存sector signature/checksumが正しく、
  ledger未作成の場合だけ一度migrationする。
- 本releaseの通常save/load/reset: 対応。トーホクとカントーの進行、QOL、Factory、
  pending encounterをversioned ledgerへ保存する。
- v1.2.0 battery save: 対応。stage 20以後にserialized fieldを追加していないため、ゲーム内saveを
  v1.3.4でそのまま読み込める。先にv1.2.0側でゲーム内saveを完了してからROMを切り替える。
- emulator savestate: version間の互換対象外。ゲーム内saveから再起動する。
- 他hack、英語版、FireRed Rev.1、不明な拡張save: 非対応。

未知magic/version、size不一致、ledger checksum不一致、非zero予約領域はfail-closedで拒否する。
Vega badge/HM/story flagは既存領域に残し、Kanto認定章・地方anchor・League・共有捕獲stateとは
分離する。migration前の高位flagはwhitelistだけを移し、bitmapや変数を一括copyしない。

## 電源断と施設復旧

Factoryは参加前party 6体を完全snapshotし、BP・連勝・一回報酬を同じtransactionへ保存する。
勝敗、棄権、退出、reset、suspend、blackoutの全経路でpartyを復旧する。施設外捕獲NPCは
空き容量確認後に個体と支払い状態を先に確定し、reset後も同じ個体から再開する。捕獲完了時だけ
pendingを消す。Mirageの仮想item/stateはFactoryと共有しない。

v1.3.4のFactory Trialは2,048-byte ledgerをCFRU-JPのsector 31 payloadへ直接確定する。
ROM実行時の2 KiB rollback像はEWRAM `0x0203E400..0x0203EC00`へ置き、GBAの小さい
call stackへ積まない。入場前partyは6×100 byteで、完走・敗北・辞退・selection cancel・
保存後復旧のいずれも同じ像から一度だけ戻す。

## v1.3.4 QOLの保存境界

- HM01〜HM08のフィールド能力はバッグ所持から毎回導出し、新しいflagやsave fieldを持たない。
- わざメモリーの通常／タマゴ技modeはEWRAM `0x0203EC00`の1 byteだけを使い、終了、cancel、
  resetで0へ戻す。Flashへserializeしない。
- 1個目のバッジ報酬を通過済みでわざメモリーを持たない既存saveは、シオウの技管理NPCが
  Item 347を1個だけ補う。キノコやものまねハーブを消費したという履歴は追加しない。
- v1.2.0以前のemulator savestateは非互換。v1.3.4起動前にゲーム内saveへ戻す。

saveが拒否された場合は書き込みを繰り返さず、backupへ戻して新規saveを開始してください。
