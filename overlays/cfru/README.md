# CFRU battle runtime policy overlay

`runtime.h` / `runtime.c` は、T06 の battle-side policy を上流 CFRU の固定
RAM address や libc から切り離した C ABI です。ROM hook と CFRU 構造体への
binding はこの層の外で行います。

`config/battle_core.json` の語彙との対応は次のとおりです。

- AI: `AI_BASIC=1`, `AI_SEMI_SMART=3`, `AI_FULL_SMART=5` だけを受理します。
- mechanic: `STANDARD`, `MEGA`, `Z_MOVE`, `DYNAMAX`, `TERASTAL`,
  `RAID_HIGH_DIFFICULTY` は battle ごとに相互排他です。各 side は一度だけ
  使用でき、強制 Dynamax は `RAID_HIGH_DIFFICULTY` の boss side だけです。
  cleanup は mode、使用済みbit、強制bitを全消去します。
- stat inputs: mint は保存natureを変更せず実効natureだけを差し替え、王冠bit
  の実効IVは31、ability slotは0/1/2、EXP Shareは未参加個体への受給入力です。
- EXP Candy: API は選択された1個体しか受け取らず、level thresholdを一段ずつ
  通過します。加算はcapまでの差分で行うためoverflowせず、既にcapまたは
  効果量0なら道具を消費しません。
- trainer build: level/nature/ability/itemと、IV/EV/moveの各slotをoptional maskで
  上書きします。指定が不正ならatomicに失敗し、未指定値は元のVega値です。
- facility: `SINGLE_3V3`, `DOUBLE_4V4`, `NPC_PARTNER_MULTI` と `RANDOM`,
  `LITTLE`, `MONOTYPE`, `UNRESTRICTED`, `OU`, `UBER`, `CAMOMONS`, `GS` を受理し、
  EXP/EV/なつき/孵化歩数/捕獲/賞金/恒久item変更を全て遮断します。
- Mirage: held itemの変更・消費・交換はbattle-localです。勝利、敗北、逃走、
  降参、捕獲、abort、errorの全出口で元の永続itemへ戻します。
- Raid: boss、最大3 partner、最大5 shield、turn limit、終了理由、捕獲可否を
  battle-local stateとして保持します。boss撃破後にだけ一度捕獲できます。

この実装は動的確保、標準ライブラリ、固定ROM/RAM addressを使用しません。
host検証は `python3 -m unittest tests.test_cfru_runtime` で行います。
