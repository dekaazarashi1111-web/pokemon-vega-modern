# 旧egg見かけ参照: 異種literal/code境界

## 目的と現在地

直前の正本は `pr16_dex_hof_runtime_closure_checkpoint.json`。732分類/142未知、現候補0641、115 actual owner、全874hitを保持する。本scopeはMystery Giftの `0x08142F5D` だけを専用の異種boundary型で検証する。現候補Actionsと独立measurement/終端照合が完了するまで、新分類の正式受入とはしない。

正式ROM・Save101を変更せず、旧egg全15118byte保護、安全容量0、C controller6528byte未配線を維持する。origin wordの4byteを参照先の最大access幅に転用しない。

## 最小の型根

実CB2初期化のsetup成功分岐からcallback2登録とconstructorが接続する。登録CB2はRunTasksを呼び、constructorは実CreateTaskへ当task entryを渡す。本scopeは空task listからrow0を選ぶ一つの十分な有限例を用い、選択されたtaskのactive/function/list所属を各dispatchまで維持する条件を明示する。全16task空は一般的な必要条件ではない。満杯時の戻り値0を成功と誤認しない。

taskは38状態の上限検査付きtable dispatchを行う。state11と23のslotは同helperへ入り、placement値はそれぞれ0と1。helperのtextState0が正常に戻って1を生成し、次回の同task/helper dispatchまで必要なfieldが保持される条件を固定する。constructor状態0から選択producer状態8/22までの全遷移は証明せず、選択producerの入力とtextState0保持を条件化する。ネットワーク状態全般、自然プレイによる全状態到達、全heapの生存、全IRQ非干渉は証明しない。

## 異種6byteの完全partition

- `0x08142F5C`から4byte: AND maskのliteral。32bit loadとANDの実consumerを検査する。
- `0x08142F60`から2byte: placement非zero側の完整Thumb LDR。
- 対象4byteは左の末尾3byteと右の先頭1byteに交差する。

両要素は隣接し、gap/overlap/欠けを認めない。literalをinstruction streamへ混ぜず、命令をpointerへ読み替えず、専用 `rooted_mask_literal_thumb_boundary` witnessを使う。既存chainの「同kind witnessがhit全4byteを完全包含」という規則は変更しない。

left/rightは相互排他的な2経路の型証明であり、一回の実行で両方を消費したという主張はしない。静的型分類、有限成功条件、自然到達、普遍runtime lifetime、donor退役安全を区別する。

## 親証拠と容量の保持

619原本と全9親deltaは全文size/SHAと独立checkpointへ束縛し、全17inputから732親を再構成する。旧113changes/103witnessを複製せず全namespaceを参照保持する。新deltaは追加1件だけを持ち、既分類行と残未知行を全field不変で保つ。

全133曲/50assetについて新窓との役割交差だけを確認する。以前の237試験、native gameplay、heap診断、独立最終song/battle/Surfレビューを再実施したとは記録しない。過去の独立最終レビュー拒否を別経路で再試行しない。

未知参照の最大access、間接参照完全性、対象退役、owner移管は未完。global511+save804=上限1315は単一controller6528に5213不足する。点targetだけの楽観空隙は安全容量ではない。最新actual owner/52save section基準を保持し、旧nominal/suffixで配置しない。heap13352を保存退避53300入口へ跨いで保持しない。

## 検証と公開

新scope専用unit/geometry反証、current候補全SHA、115owner/874hit/全親保持、独立measurement-envelope、閉じた公開path/全量size/SHA/LFを検査する。診断用旧候補06c5は現候補0641の受入に代用しない。

producer/guard/upload/recordは同じ専用dirを用いる。guard成功時だけ11個の非空textを公開し、hidden、symlink、未知拡張子、欠落、差替えを拒否する。ROM断片/rawhex/ROM/runtime/入力save/私有archive/memberpath/runner/credentialは新規公開しない。既存tokenは同branch/run/source/pendingへ限定し、credential追加、persistent access拡張、merge/release/force pushを行わない。

## 次工程

0x080A006FはGPU scalarとVBlank callbackの8byte境界候補だが、外側root0x0809FF00は未特定。既受入title有限窓で登録/BLは見つからず、新分類へ昇格しない。具体登録callsiteまたは既知dispatch table slotが得られる場合だけ再開する。

残参照の最小十分rootを順に閉じ、安全な容量が確保できた後にcontrollerを実配置する。全S61E/MDX writer/loader/Link exact-source/no-main/INITIAL、全mode/早期31/species9bit、全保存入口heap-ready/同期非再入/全出口Freeを接続する。正式切替後はtrainer131後半からシオウ通常回復/保存/独立coldContinueへ進む。雑魚毎checkpointは作らない。
