# PR16 登録script producerと最小opcode領域の限定監査

## 範囲

`CHATGPT_RESUME.md`から固定再開MD/JSONを読む。直前のevent boundary batchは751分類・123未知。本工程は全17親delta、132changes、122witness、全874hitのidentityと既accepted/残unknownの全fieldを保持する。133曲と50assetは親原本への独立identityを保ち、原本本文を複製しない。

型の必要最小十分条件、自然play全到達、普遍IRQ/heap寿命、間接参照完全性、対象退役、owner移管は別々の証明義務。隣接配置、公開source名、有限graphに正のpathが見つからない結果を、全consumer根や全writerの不在へ一般化しない。

## 新battle最小型2件

### effect233のHealPulse opcode field群

`0x0900739D`を覆う4byteだけを分類する。現effect233 slot→`0x09007385`、現Move表、公開固定BS_233の36byte prefixとmacro serializerを束縛する。対象はFF26のsecondary opcode、ppreduceのprimary opcode、FF09のprimary/secondary opcodeという4個の完全なopcode byte群である。実primary/secondary dispatcherとtrampolineで各byteのLDRB、table slot、handler addressまでを独立Thumb意味で結合する。

各command入口条件下でのdispatch値流れであり、attackstringnoprotean/ppreduce/attackcancelerのhandler成功や連続自然到達は主張しない。FF09の完全pointer readは実consumerとbank0 resolverから別に束縛する。全script領域やdispatcher全体を型にしない。

### effect234のTopsyTurvy/Electrify境界

`0x09007432`を覆う4byteだけを分類する。現effect234 slot→`0x090073F9`、現Move表、公開固定BS_234と59byte prefixを束縛する。左goto `0x0900742F`の完全pointerと右Electrify `0x09007434`のFF09役割を、実selector taken/next、goto consumer、bank0/pointer readから結合する。

goto後の物理隣接をruntime fallthroughと解釈しない。Electrifyは実jumpifmoveのtaken側から構造上登録される。callasm、accuracycheck、attackcancelerや全prefixの成功は別義務である。

両hitは新data型2件・計8byteに限る。未知word size4を参照先のread幅として流用しない。

## event別登録2根の拡張grammarとplaceholder分岐guard

`0x0818DD5D`は未知維持。前回の確定guardであるOBJECT:3/10:0と23/0:0の2根の別message/END結果は再測定せず保持する。別途8根について保存された探索観測を正式guardへ昇格しない。前回未対応だったOBJECT:10/2:0 root `0x0818D4F2` とOBJECT:21/0:0 root `0x0818D143` だけを追加対象とする。

opcode34はcompare_var_to_var、opcode195はincrementgamestatに対応する。現JP dispatch/handler、登録chain、有限call/goto/CALLSTDの構造graphを束縛し、目的LOADWORD `0x0818DB31` / `0x0818DB50` への接続有無を限定的に検査する。未対応grammarを理由に不達扱いしない。CALLSTD/special/nativeやflag/field-effect等のopaque効果、自然完了、context維持は有限構造証明から分離する。GetVarPointerの現hookを旧stock実装として扱わない。

現GetExpandedPlaceholderのID3分岐が`gStringVar2`へ戻ることと、置換元を生成する実producer・有効extent・EOS・実text-byte消費は異なる義務である。前者の枝を束縛できても後者を自動承認しない。対象へ結合する正の登録root/完全consumerが閉じるまでは4byteも分類しない。全root不達、全script未使用、間接参照完全性を主張しない。guardは空の型領域だけを返し、型witness registryへ登録しない。

## 親証拠・容量・runtime境界

- 全33入力は各全文size/SHA/LFを独立checkpointと照合し、全17namespaceを旧validatorのまま復元する。新deltaはbattle2件・計8byteだけ。event1件と既Bag数量順2/Fishing1/追加Defog-Dive1を含む残unknownは全field不変。
- 最新generation_writerの115actual owner、52save owner、残804byteを束縛する。旧nominal suffixのowner hashを使わない。
- 不明な参照先最大アクセス範囲が残る間は旧egg15118byteを全保護。仮にunknown0になっても間接参照完全性・退役・owner移管が未証明なら安全容量0。
- global511＋save804の既知上限1315は単一controller6528に不足する。点targetだけの空隙は安全容量ではない。
- heap13352の同期非再入・全保存入口heap-ready・全出口Freeが未証明。stock保存退避53300の入口 `0x0804B85C`より前に解放し、退避を跨いで保持しない。
- 正式ROM0641、Save101、donor、controller配線は変更しない。修復完了後にtrainer131後半からシオウ通常回復/保存/独立coldContinueへ進む。全雑魚checkpoint禁止。

## 検証と公開

新moduleの局所診断は既回収診断入力を使うため、正式current0641測定と分離する。正式Actionsは現候補を一度だけ再構成し、全SHA/全115owner/全874hitと必要窓を束縛する。新scope unitを実行し、旧成功suite/native/heap・全ROM inventory scanは再走しない。公開sourceはsource-lockの固定commit、全文size/SHA/Git blobを必須とする。

独立new-source reviewは本工程のsourceだけを対象とし、未解決finding0と完全source bindingを要求する。以前拒否された旧独立最終source reviewは未実施のまま保持し、同操作を別経路で再現しない。

producer/guard/upload/consumerは同一の専用path・artifact名へ固定する。成功したclosed text setだけを公開し、非空、size上限、全量、LF、UTF-8、JSON、SHA、実commit blob、固定MDJSON/両ログの読戻しを検査する。hidden/symlink/未知file・拡張子、CR、NUL、欠けたsnapshotを拒否。公開はsource・最小address/size/SHA・textのみで、ROM断片/rawhex/ROM/runtime/入力save/runner/credentialsを含めない。

closeoutではreceipt全本文を実commit済みfixed-stateのrecording全fieldへ結合し、空pendingと各snapshotの実Git blob一致を必須とする。自己申告hashだけでreceipt改変を承認しない。一般CIの既知QOL原本不一致、action_required/job0、Stage79旧cache復元とnative skippedは新scopeの受入と分ける。旧9月18日queued4件へ操作しない。closeoutは新測定結果を再利用し、起動条件だけmanual-onlyへ退役、全snapshot読戻し後pendingを解除する。
