# 全国図鑑の正規grant owner — 静的な限定照合

`PASS_NATIONAL_DEX_GRANT_OWNER_SCOPED`。実ROMのmap header→条件table→script CFG→special tableを読み、3本のroot/20nodesにdecode診断0。ROMやSaveを変更せず、ゲームによる全国図鑑解禁や進化成功を受入してはいない。

## Vega側の具体的な経路

map3/0のtype2条件 `var0x4072=9` がroot `0x08853824` を選ぶ。`0x0885387C`で同varを10へ更新し、`0x08853884`からmap4/3へwarp。研究所map4/3のtype2条件 `var0x4072=10` はroot `0x088538B0` を選び、`0x08853A5D`でvar11、`0x08853A68`でspecial367、`0x08853A6B`からmap30/0へ出る。9に至る通常進行はこの照合の外側であり、序盤ですぐ入れるとは推測しない。

special table `0x08163068` の367番は `0x0806DA21`、403番は判定関数 `0x0806DA51`。native有効化ownerはSaveBlock2+0x1Bのmagic0xB9、var0x404E=0x6258、flag0x840を扱う。既存進化guard `0x080CFA20` / `0x080D067C` とgrant/predicateの4範囲を候補hashとともに固定した。閾値やflagのhost書換えは行っていない。

## legacy経路との区別

同じ研究所には `var0x4055=7` → root `0x0817C61D` → special367（`0x0817C740`）の別経路も残る。この条件が早期通常進行で成立する証拠は得ておらず、rootがあることを現在の到達可能性へ昇格しない。VarGetにはCFRU側hookがあるため、単純なSave内offset読取からvar値を断定しない。

探索時にVega425mapの旧root走査でinvalid roots6とdecode診断1が出た。これは今回の3root限定証明とは別の探索結果で、全678map監査や全経路到達証明をPASSとしない。根拠は限定audit.jsonのroot/CFG/参照元であり、ROM全体の生byte検索だけではない。

## 保存原本と次工程

Maori Save16 artifact11006311891のROM06c5e85c…とSave5c4a03b9…を読取専用で再利用し、全国図鑑magic0を確認した。元progression/Save14は不変。追加native/compile/ROM・Save書換え/既受入case再実行0、新規のowner検査14件を実行した。マオリ完了記録run36504857429はpush/upload/postを含めcompleted/success、commit3af810957b9d86578c595b11b0a8a67a0276a289を継承する。

マオリSave16と全国図鑑grant ownerの限定照合は完了。story-fastはartifact11006311891のstory-fast.srm、map3/19(53,10)から通常storyを続ける。全国図鑑のVega側経路はmap3/0のvar0x4072=9→10→map4/3へwarp、同研究所のvar10イベント→special367→var11の保存状態。var9に至る通常進行と有効化後の自然進化は未受入。legacy var0x4055=7経路を序盤で到達済みと扱わず、flag/var注入やgate緩和はしない。元progression戦闘前Axewを保全し、正規解禁後の別境界で成長/進化/Lucky Egg対照/12ケース/Lv100soakへ進む。旧受入入力・44試験・このowner走査の無影響再実行は禁止。

本workflow自身の終端成功は自己予測せず、push/upload後の外部API照合で確認する。
