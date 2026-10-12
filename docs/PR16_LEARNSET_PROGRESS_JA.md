# Issue19: 初期技と通常level-up

旧2入口に加え初期技/通常level-upを新候補e168c06fへ接続。3hook/全差分rollback/P03進化dispatch不変・30試験/全1483owner×100level/318186照合・9代表条件×2processの直接ROM probeを受入。条件consumer/新Wiki/通常操作E2Eは未完。

## 完了境界

候補SHA-256 `e168c06f7707002e976dceff61ad8b5ad98ccd07be322f4e8d93d2276a206d82`、33554432 bytes、CRC32 `1D2DBFE7`。成功Actions `35710087058`、入力HEAD `d9f92e51826fbda4741c294635442a66cb777b64`。

初期技は該当level以下の末尾4行を既存GiveMoveToBoxMonへ渡す。既存の非空4技は変更しない。通常習得は同levelの複数行を順に通知し、満杯/既習得の戻り値とPPを維持する。進化専用/思い出し等の行を通常levelへ混ぜない。

真の初期技入口0x0803E14Cと別CFRU初期関数0x091145F0、通常QoL delegate0x09377728の3か所を接続。0x0803E174は関数途中でありC ABI入口ではない。P03進化dispatchと2つの進化LR分岐はbyte不変。旧2入口/PLR1/root/save構造は不変。

9代表条件でCreateMon・実PP・初期2入口・通常2入口・満杯通知・重複後継続・非学習owner保全を検証。ただしhost fixtureからの直接ROM callであり、野生遭遇/Bag/戦闘/習得画面/Save/Continueの実操作受入ではない。固定CFRU source configのrandomizer無効確認は全ビルドmacroの網羅検証ではない。

30host試験と318186照合は失敗run35709388462の成功部分を継承。ABI/配置検査失敗を成功へ改作しない。証拠/checkpointのhashとsource bindingから再開し、受入済みhost/ARM/nativeを重複しない。

## 次工程

Issue19: 保存済み初期技/通常level-up候補とPLR1/payloadを再利用し、進化・思い出し・egg/shared-egg・tutor等の条件consumerを個別に明示ownerへ接続。新候補Wikiを別pathへ生成し、Bag/戦闘/習得選択/Save/Continueの影響実操作E2Eを受入する。今回の直接ROM probeや30host試験を重複しない。
