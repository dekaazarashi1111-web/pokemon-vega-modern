# Modernization Mega Stone BP shop

Stage 67を親に、追加Mega Stone 45種をクチバFactoryの独立BP店員へ接続する。

- 価格は全品16 BP、5件×9ページ。
- `ITEM_KEY_MEGA_RING`（canonical ID 580）をBagに持つ時だけ利用できる。
- 0x14A0..0x14CCのexpanded event flagをstable item-key順に割り当て、各品をsaveごとに一度だけ購入可能とする。
- 購入順序は`AddBagItem`、BP減算、claim flag設定、standard save、sector 31保存。保存失敗時はitem、BP、flagを補償rollbackする。
- 既存18品BPショップと同じ128-byte volatile menu領域を、同時に開かない別taskとして共有する。

新ItemはStage68で1044行Item表へ実体化する。一方、既存Codex対戦catalogはsafe item上限998、Mirage virtual item表は既存固定候補だけを受け付けるため、ID 999..1043は両入口へ流入させない。公開telemetryの10-bit fieldを黙って切り詰める経路は作らない。
