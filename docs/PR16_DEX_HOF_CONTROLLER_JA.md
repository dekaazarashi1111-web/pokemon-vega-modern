# HOF C controllerとsave owner後継配置

## 現在の実装境界

実32sectorのPython制御をCへ移した。HT_Resolve、HT_Recover、HT_Commit、HT_Normalは全mainのSHA-256、256byte journal、旧HOFのscratch／逆差分、署名最後のcommitを扱う。mainの既存S61E／MDX validator、全Save mode、HOF-only loader、INITIAL has-records判定への本番配線は未完である。

12host suiteは新CとPythonの全131072byte比較51shape、224中断後cold／通常Save、76部分erase、256journal破損、32復旧中断、55連続更新、42rotation／parity／wrap、14token継承を検査。署名前に全4096byteをreadbackし、対象外tailのprogram省略でも新main署名を確定しない。ARMはcodec込み6528byte、mutable0、未解決symbol0。初回ARM linkで構造体copyのmemcpy依存が見つかり、field-copyへ修正した。失敗runを成功へ読み替えない。

この6528byteを旧schedulerの残186byteへ追加できない。現在のsave専用枠は9560byteで、Stage61内7016、codec内1460、bridge1084。固定8入口128byteとmode3専用180byteを保護すると、後継bodyへ再配分可能なのは9252byteである。旧bridge最大1704byte以降の他ownerやROM末尾を空きとみなさない。

## 安全な後継source

新generatorは旧sourceを一意の関数境界で変換し、live image生成、footer検証、署名last書込、全世代readbackを共通化する。旧／新sourceの合成20caseずつと183差分caseで全flash、MDX、counter、rotation、damaged mask、callback件数を比較した。保存仕様は変更しない。

Linkは旧cを同じrotationのc+1へ先に退避し、RAMはcのままstockが0..4を更新する。次にcのid13で旧PCを保持してS61E／MDXを更新し、完全なcからc+1へcloneした後だけRAMを昇格する。HT_Normalの「最新を選んでcounter+1／rotation+1」をpost-stockへ単純流用するとc+2へ進むため禁止する。初回no-main生成とLinkFullの遅延署名も残す。

後継linkは現save-only窓だけを使い、固定8入口とmode3五section、115allocatorの境界、非save code、shared read32／rodata／libgccを保つ。新HJ codecの3関数には明示sectionを与える。実配置の可否と変更影響nativeは専用Actionsで判定し、この説明だけで配置済みとはしない。

## 検証の区別

- save後継nativeは再配置された8入口の変更影響19caseと、候補ROM上HJ validatorの新257caseを対象とする。旧ストーリー成功区間を再走しない。
- controller nativeは私有候補上の明示RAMへ新ARM codeを置く隔離probe。全flash／HOF／整数結果をhost oracleと比較し、非owner RAM、callee-saved register、stack、元ROM不変を検査する。これをROM保存経路への接続、ゲーム起動、実Save、cold Continueと呼ばない。
- selector／prepare callbackは合成モデルであり、本物のS61E／MDX ownerの代用品ではない。
- workspace本体＋4096＋7936byteの本番RAM／heap生存区間、INITIAL absence、全writer／clone／loader gateは別途必要。未証明の固定RAMやAlloc呼出しを有効化しない。

正式ROM／Save101の切替、species9bitの修復、共通SaveFailed、早期sector31、全cold owner、残typed consumerは未完。最終目標はシオウ通常回復・保存・独立cold Continue。雑魚ごとの保存checkpointを戻さない。公開成果はsourceと最小address／size／SHA／textのみで、ROM断片、rawhex、ROM、入力save、runtime、runner、credentialは含めない。
