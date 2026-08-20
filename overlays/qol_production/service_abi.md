# QOL production service ABI

`VegaQolProduction_Dispatch(service, a, b, c)` は、短いevent wrapperと既存UI adapterが
共有するStage 36の固定入口である。`service`は`qol_production.h`の
`VegaQolService`を使い、戻り値は原則`VegaQolStatus`とする。

- PC対象は`box` 0–13、`slot` 0–29の実80-byte `BoxPokemon`で指定する。
- 検索はEWRAM上の`VegaQolSearchFilter`を渡し、14箱を横断した選択bitへ反映する。
- move/release/item操作は全対象を先に検査し、失敗時はbox/bagを変更しない。
- unlock照会は既存badge/story/ledgerから導出し、Vegaのstory flagを書かない。
- field PC、auto battle、egg queueは同じdispatcherを通常UI adapterからも呼ぶ。

ABI versionは`VegaQolProduction_Probe(1)`、feature数は`Probe(2)`で取得できる。
