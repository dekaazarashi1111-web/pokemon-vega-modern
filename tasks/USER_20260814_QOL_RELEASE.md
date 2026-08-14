# USER-20260814-QOL-RELEASE — 全QOL変更を統合して再現可能な遊べるreleaseを確定する

- Lane: `platform/qa`
- Depends on: `USER-20260814-HM-FIELD-ACCESS`, `USER-20260814-BATTLE-RULES`, `USER-20260814-BATTLE-UI`, `USER-20260814-MOVE-MEMORY`
- Queue ID: `USER-20260814-QOL-RELEASE`

## 目的

今回追加したHM field能力、現代battle rules/UI、わざメモリーを最終stageと配布patchへ統合し、
固定入力から再現できる早期プレイ可能releaseを確定する。

## 実行

1. 各完了taskの検証済みstage/hashを再利用し、統合前に同じ重いbuildを繰り返さない。
2. 自然new gameから御三家3分岐、HM入手前後、状態異常/急所/天候、UI、わざメモリーを継続saveで通す。
3. 最終ROM、clean BPRJ Rev.0用BPS、決定論ZIP、利用説明、save互換性、known issuesを更新する。
4. ROM/save/元patch/private pathをarchiveへ含めない。
5. 隔離fresh checkoutからの重い全再構築は、この統合taskの最後に1回だけ実行する。

## 受入条件

- [x] 全機能の継続save smokeと既存Factory/Kanto主要回帰がPASSする。
- [x] BPS完全往復、32 MiB/BPRJ header、archive禁止物0を確認する。
- [x] tagged sourceのfresh checkoutからfinal/BPS/ZIPがbyte一致する。
- [x] 日本語release文書が操作、解禁条件、CFRU rule provenance、save互換性と一致する。

## 完了

対象検証とログを更新し、queueをDONEへ変更してrelease tagとタスク単位コミットを作る。pushはしない。
