# PR16 event/battle境界の実根限定監査

## 範囲

`CHATGPT_RESUME.md`から固定再開MD/JSONを読む。直前のfield consumer batchは749分類・125未知。本工程は全16親delta、130changes、120witness、全874hitのidentityと既accepted/残unknownの全fieldを保持する。133曲と50assetは親原本への独立identityを保ち、原本本文を複製しない。

型の必要最小十分条件、自然play全到達、普遍IRQ/heap寿命、間接参照完全性、対象退役、owner移管は別々の証明義務。隣接配置、公開source名、有限producer一本の不達を全consumer根や全writerの不在へ一般化しない。

## 新battle最小型2件

### effect231のEmbargo/Powder境界

`0x09007271`を覆う4byteだけを分類する。既登録effect231のroot `0x090071BA`と実selector群を再利用し、公開固定macro serializerと現JP実operandからEmbargo13命令61byte（`0x09007236..0x09007273`）を結合する。左goto `0x0900726E`は完全4byte pointerを読み、右Powder `0x09007273`のFF09は第三selectorから登録される。goto後の物理隣接をruntime fallthroughと解釈しない。

### effect184のRecycle境界

`0x09005D94`を覆う4byteだけを分類する。現effect184の実slot→`0x09005D7F`、現Move表のeffect値、attackcanceler＋jumpifnotmove＋callasm＋gotoの23byte prefixを束縛する。実JP NOTEQUALS selectorのtaken/nextを分離し、Recycle FF09へ結合。GetBankForBattleScriptは実bank1 slotとattacker byte読取りまで実行し、bank0の値差替えで代用しない。

両hitは左gotoの完全pointer末尾と次のprimary/secondary opcodeを跨ぐ。crossing4byteをpointerとして読む経路ではない。完全pointer、opcode、operand役割は独立semantic encoderと実JP consumerで束縛する。attackcanceler/callasmの成功、全prefixの自然到達、全script領域の型を主張しない。

## event placeholder境界の未結合guard

`0x0818DD5D`は未知維持。候補として示された現object3/10:0→`0x0818D82A`とobject23/0:0→`0x0818D7F2`は、それぞれ別textをLOADWORD0へ渡し、CALLSTD2→標準2のmessage(NULL)とreturn→ENDで構造上閉じる。実return→END probeは標準2の完了とcontext/stack保持を条件とし、標準2の各helper自体は実行していない。両候補根から目的LOADWORD `0x0818DB31` / `0x0818DB50`へつながることを証明できない。

標準2のlock/faceplayer/message/wait/waitbutton/release/returnとENDは構造意味を固定するが、opaque helperのruntime効果や全game context不達は主張しない。目的textのplaceholder ID3の存在だけでは置換source、extent、EOS、実byte consumer、登録rootを結合した証拠にならない。Summaryの別placeholder機構で代用しない。

既有限登録一覧の探索では別root候補も調べたが、未対応grammarが残る。探索は全map/全caller/全writerの網羅証明ではなく、未知rootからの別経路を排除しない。guardは空の型領域だけを返し、型witness registryには登録しない。新しい正の登録rootと目的command pathが出た時だけ再開する。

## 親証拠・容量・runtime境界

- 全31入力は各全文size/SHA/LFを独立checkpointと照合し、全16namespaceを旧validatorのまま復元する。新deltaはbattle2件・計8byteだけ。event1件と以前のBag数量順2/Fishing1/追加Defog-Dive1を含む残unknownは全field不変。
- 最新generation_writerの115actual owner、52save owner、残804byteを束縛する。旧nominal suffixのowner hashを使わない。
- 不明な参照先最大アクセス範囲が残る間は旧egg15118byteを全保護。仮にunknown0になっても間接参照完全性・退役・owner移管が未証明なら安全容量0。
- global511＋save804の既知上限1315は単一controller6528に不足する。点targetだけの空隙は安全容量ではない。
- heap13352の同期非再入・全保存入口heap-ready・全出口Freeが未証明。stock保存退避53300の入口 `0x0804B85C`より前に解放し、退避を跨いで保持しない。
- 正式ROM0641、Save101、donor、controller配線は変更しない。修復完了後にtrainer131後半からシオウ通常回復/保存/独立coldContinueへ進む。全雑魚checkpoint禁止。

## 検証と公開

新moduleの局所診断は既回収診断入力を使うため、正式current0641測定と分離する。正式Actionsは現候補を一度だけ再構成し、全SHA/全115owner/全874hitと必要窓を束縛する。新scope unitを実行し、旧成功suite/native/heap・全ROM inventory scanは再走しない。公開sourceはsource-lockの固定commit、全文size/SHA/Git blobを必須とする。

独立new-source reviewは本工程のsourceだけを対象とし、未解決finding0と完全source bindingを要求する。以前拒否された旧独立最終source reviewは未実施のまま保持し、同操作を別経路で再現しない。

producer/guard/upload/consumerは同一の専用path・artifact名へ固定する。成功したclosed text setだけを公開し、非空、size上限、全量、LF、UTF-8、JSON、SHA、実commit blob、固定MDJSON/両ログの読戻しを検査する。hidden/symlink/未知file・拡張子、CR、NUL、欠けたsnapshotを拒否。公開はsource・最小address/size/SHA・textのみで、ROM断片/rawhex/ROM/runtime/入力save/runner/credentialsを含めない。

一般CIの既知QOL原本不一致、action_required/job0、Stage79旧cache復元とnative skippedは新scopeの受入と分ける。旧9月18日queued4件へ操作しない。closeoutは新測定結果を再利用し、起動条件だけmanual-onlyへ退役、全snapshot読戻し後pendingを解除する。
