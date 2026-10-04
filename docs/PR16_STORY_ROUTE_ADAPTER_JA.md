# Save101後継 live route adapter

所有者指定の意味ある到達点は506→519→シオウPokecenterの通常回復・Save・fresh Continue。通常戦ごとのSaveは作らず、未知owner/UIは未保存診断停止する。

## 時計の限定owner

固定ROM main loop 0x0800049E→0x0837BE9C→0x093BE9F8→0x08054130。SaveBlock2 offsets0x0E/0x0Fはhours、0x10はminutes、0x11はseconds、0x12はVBlanks。1秒60tick、各fieldのrange、単調性、観測frame予算＋位相差最大1tickを検査。0x13以降や残り全byteを時計扱いしない。飽和999:59:59:59は別ownerが必要なので停止。

実際のhookはseconds59→0ごとにResearchEconomy_MinuteTickも実行する。ledger offset0x746のminute、60minute rollover時だけday serial・daily counters・daily shop・simple claimsを正確に更新し、外側FNV1a checksumを再計算する。全2048byteを予測像と比較する。RP、lifetime、once、story flagを可変のまま許可しない。Save/RTCは不変を要求する。

## 歩行と現在trainer

same-map通常1tile/旋回について、位置、4021 modulo128、4022 modulo5、暗号化GAME_STAT_STEPS（cap0xFFFFFF）、周期時だけfriendshipの0/+1、残る全SaveBlock1/party/save2/拡張領域を検査する。friendship乱数は結果の有界ownerを照合し、個々の分岐PC採取とは呼ばない。

trainer131/128/1065は現在24consumerのtable0x09329070から各4体、物理flag1411/1408/1416を解決。rewardは旧vanilla経路がhookで置換されているため、0x091191CCの実敵party末尾levelと実class/fallbackを優先。通常single/moneyMultiplier1の候補額は448/1700/504。class42は現在tableにないため、実calculatorの先頭class倍率25へのfallbackを明示する。未観測の倍率・賞金を受入済みにしない。

全215歩のterrain、両mapのland tableも固定ROMから照合。native戦闘UI、postbattle dex/統計owner、map transition、nurse会話は引続き解決対象。本stageは新route readerと厳格guardを実装し、最初の未対応eventを同一frameで診断する。未知eventへのA fallbackはない。診断を施設到達・戦闘勝利・保存達成と呼ばない。

既存49試験/native probeは再利用。新41host試験と保存済みprobe2観測に対する時計adapter照合は別記録。旧observer/runner/受入証拠を書き換えない。ROM/入力Save/runtime/新runnerは再配布しない。
