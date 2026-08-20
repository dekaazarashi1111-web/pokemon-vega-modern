# T20 event design provenance

- 読取専用原本: `userfile/imports/Pokemon-Vega_EVENT-DESIGN_IMPLEMENTATION-READY.zip`
- ZIP SHA-256: `576847447f0c659c3db639179aa1fa71057b909d8eff5b408ba725ee285fee8e`
- submission SHA-256: `776d8c911ad3c2705ffdaf840d1b6cdbefe816cf000accdf3ea47a45991c4fec`
- authoring baseline: Stage 35 / commit `993e1419caa0a51d78ac15be8e2caad042470549`
- implementation baseline: Stage 36 / ROM SHA-256 `c262fbb121957950f890c7b28ab64b19f9bc8fdf541b543747c39ab1f7c381dd`

同梱6ファイルは安全展開後のbyte列を変更せず保存する。Stage 35由来の数値hostは実装値として使わず、symbolic keyをStage 36 rooted graphへ再解決した結果を`config/event_design_bindings.csv`と生成auditへ記録する。

Stage 36既存saveではT20専用flag `0x13B0..0x13FF`が未設定なので、全stateを0/defaultとして読み込む。書込みは成功後の0→1のみで、既存Vega/Kanto/QOL ownerのstateは所定のproduction ABI経由で同期する。
