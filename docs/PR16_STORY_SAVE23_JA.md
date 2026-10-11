# ちえのどうくつ内部warp・Save23 限定受入

`PASS_INTERIOR_WARP_SAVE23_SCOPED_FROM_PRESERVED_FAILED_RUN`。北入口map1/36から内部map1/73・20,3東への通常階段warp、通常Save23、独立Continueのみ。洞窟走破/南出口/新storyイベント、HM05、全国図鑑、自然成長/進化、全storyは未完。

## 原本と失敗の意味

測定source `171a6518751659d66523924b9469045019814fb7`、run `37090970832`、job `111111036767`、artifact `11261539316`。archive全17499395bytesのSHA256 `b5cb150d1fe3271b8dba3791b01fc3a3548f5183cb5c5bc5a6d684a99f8234b4`、全34member/17画面を照合。native2processは正常終了、45/cold13入力・3318/cold1510framesで保存まで完走。初回の最終oracleはflag2056を完全不変と仮定したためfailure。実際の差分2056:1→0とvars4021:23→26/4022:3→1だけを後続oracleで限定照合する。runtime ownerやflagの意味を推測せず未解決のまま保持する。旧runをsuccessへ改作せず、native/入力の再走0。

## 保存と画面の境界

Save23 `728bd39b11ea53bafd31cff5fb50e7f81fe5973c0c5fae559ea22037827832bb`、131088bytes。全Save/RTCが独立Continue後も不変。全party600bytes、全Bag/HM05、12296円、旧Save22bank57344bytes、PC/S61E、全国図鑑magic0/var404e0/flag840=0、story4071=6/4072=1を保持。stock checksum42件とS61E CRC/反転値を照合。全差分7000bytes/1788範囲のhexはartifactだけ。

進行0/1/3/5/7〜14とcold0/1の14anchorを目視。進行7で内部到達、11/12は書込途中、13で「レポートに しっかり かきのこした！」、14で操作可能fieldへ戻る。cold2画面も同位置。新戦闘/捕獲/回復/育成/技習得0。静的14試験と入力controller17試験の原本は再実行せず、新しい原本受入/拒否24試験を追加。

## 再開

story-fastの唯一の開始点はartifact11261539316のstory-fast.srm（Save23、131088bytes、SHA256 728bd39b11ea53bafd31cff5fb50e7f81fe5973c0c5fae559ea22037827832bb）。ちえのどうくつ内部map1/73・20,3東・party4/RP0・12296円・badge1、var4071=6/4072=1。北入口からの階段warp・通常Save23・保存成功文言・独立Continueは限定受入済み。内部の先へ通常入力で進み、次のSave/cold境界で区切る。洞窟走破/南出口/新storyイベントは未完。45/cold13入力、静的14/入力17/原本受入24試験とSave1〜22/旧BP/P08は無影響に再走しない。run37090970832のfailureは保存後oracleの補助flag2056不変仮定が原因であり、成功へ改作しない。2056:1→0と補助var4021/4022の実観測差分だけを限定記録しruntime ownerは未解決。HM05は所持のみで未習得/未使用・原因未解決、同じ拒否入力を反復しない。全国図鑑magic0/grant ownerと分離progression原本Axewを保全し、flag/var注入で解禁しない。正規全国図鑑、自然成長/進化、Lucky Egg/12ケース/Lv100soak、研究施設自然到達、全storyは未完。

記録source `f74ed8efe29f36952c3f9ec864ca6a8f37a47c82`、run `37091670533`。記録自身のpush/upload/post成功は次の外部APIで確認し、自己予測しない。一般CI全成功・release・merge・active baseline切替は主張しない。
