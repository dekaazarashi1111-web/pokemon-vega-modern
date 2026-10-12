# PR16: 661親証拠を保持する残参照root/consumer分類

## 正本と境界

`CHATGPT_RESUME.md` から固定再開MD/JSONを読む。受入正本は `content/modernization/pr16_dex_hof_remaining_references_checkpoint.json`。この実装guideだけで新しい候補や参照を受入したことにはしない。測定成功・全原本記録・終端確認後のcheckpointを使う。

対象候補は33554432 bytes / SHA-256 `0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583`。最新115 actual owner、52 save subowner、残804byteを保持する。正式ROM・Save101・donor lease・実controller配線は変更しない。

## 今回の有限範囲

旧874見かけ参照のうち661分類/213未知を親とし、追加33件だけを実根と型consumerへ束縛する。全て受入された場合は694分類/180未知、owner内1/外179となる。

- Stage36: summary hookから独立したbyte文字列consumerへ到達。TotalText末尾3byteとIV評価先頭1byteの跨ぎ。mode1・trained bit0・IV31でindex0となり、実appendまでの経路を確認する。
- Stage38: map31/1 object0→reception/enter/chooseの14command→実JP opcode35 consumer→CommitSelection。BLと次LDRの6byteだけを命令型とする。
- Stage55: map97/39 BG1→hidden-item script→goto_if。opcode・条件・pointer下位2byteの跨ぎであり、全pointer operandの型を転用しない。
- Stage70: current Stage75 icon表のspecies1645 slot。species変換hook、上限1670、gender leafのr4保持、異なる両gender経路で1645が保持されることを確認し、1024byte raw iconの先頭512byte frameだけを型付けする。
- engine6件: 実script/SPECIAL dispatch、CreateTaskの同callback field登録とRunTasks読出し、上限付きswitchから有限命令pathを検証する。MOV pc命令は2byteであり、4byteサイズ偽装を拒否する。関数名や範囲全体だけで分類しない。
- EasyChat16件: 実22group境界・group*8・word*12・左右独立slot・StringCopy/EOSへ束縛する。2個のundefined literalと選択wordの非一致も確認する。
- ability説明6件: current summary hook→getter/delegate→318上限→実pointer表→23byte copy。左右textのEOSが境界内にあり、names copy前後のr6保存とstack scratch非aliasを確認する。
- tileset1件: map7/5のlayout pointerとID12→selected layout slot→secondary compressed graphics。既受入JP consumerを固定参照し、厳密LZ消費4599byte/復号12288byteのpayload内だけを型付けする。

静的存在経路・歴史的型付けを、自然story到達・画面表示・音声再生の受入に昇格しない。T09上位wordは未分類である。current PLC2 readerを旧T09表のconsumerへ誤流用しない。

## 旧証拠を落とさないchain

`pr16_dex_hof_remaining_chain.py` の `parent` は次の全byte identityを検証して661を復元する。

1. 619分類の不変原本 `pr16_dex_hof_typed_recovery_evidence/egg-typed-audit.json`
2. 644分類の親 `pr16_dex_hof_reference_evidence/reference-delta.json`（149772byte、25 changes/22 witnesses）
3. 661分類の親 `pr16_dex_hof_reference_gaps_evidence/reference-chain.json`（95619byte、17 changes/16 witnesses）

新chainのmaterialize後も旧 `reference_delta` と旧 `reference_chain` 全体をそのまま保持し、新証拠は `remaining_reference_chain` へ追加する。旧acceptedと残unknownの全field、874件のaddress/target/kind/size/SHAを不変にする。4.1MB原本、旧delta、旧chainの複製を新公開証拠に含めない。

追加33件の分類はcurrent全ROM SHA・全115owner・全874hit・公開source全文/Git blob・全有限窓を確認してから行う。ローカル旧formalの有限窓診断は正式受入にならない。テストfixtureは同じActionsで一度復元したcurrentからメモリ上で注入し、ROM断片を公開testへ埋め込まない。

## 音声と役割競合

新しい音声根は採用しない。既存132モデルを新typed/root窓との非衝突確認に限って再モデル化する。以前の43 sample witnesses、644親追加4、661親追加2の49 distinct asset identityを全て保存し、1件の欠落・変更も拒否する。全132曲、finite root、engine、command/structureと新data/codeの役割競合を拒否する。

306/85/43/44の有限根調査は未解決だった。未知のまま残し、未発見を不存在証明にしない。旧US曲IDや表長をJP根の代用にしない。

## 実行と公開契約

新workflowは対象repo/固定branch/first attempt/限定source差分/空pendingを確認する。既存tokenを用い、新credentialや新しい永続アクセスを作らない。同branchへの非force pushのみ。全変更blobを読戻した後にrefを進める。

測定は一度のcurrent再構成、新拒否試験、追加型分類、chain記録で構成する。native/emulator、無変更heap受入、旧全ROM inventory scanを再実行しない。source/candidateが不変の既受入を全回帰しない。

公開はsourceと最小address-size-SHA/textのみ。ROM断片/rawhex/ROM/runtime/input save/runner/credentialを追加公開しない。producer/guard/upload/recordのpathを一致させ、非空・全10text・独立測定envelope・committed snapshot receiptを必須とする。hidden、symlink、未知file、部分成功の公開を拒否する。

## 次工程

残180件（予定）のactual root/consumerと、間接参照・旧egg退役完全性を閉じてから明示donor移管を行う。CFRU battle-script拡張opcode群と、現root未証明の旧learnset列は未知として残す。

その後、Ccontroller容量確保と実配置、全S61E/MDX writer/loader/Link exact-source/no-main/INITIAL、全mode/早期31/species9bit、heap-ready・同期非再入・全出口Freeを閉じる。heap13352byteを保存退避53300byteのコピー跨ぎで保持しない。正式候補切替後にtrainer131後半からシオウの通常回復・通常保存・独立coldContinueへ進む。雑魚戦ごとのcheckpoint保存は行わない。
