# Issue19 後継候補の技習得基準Wiki

候補 SHA-256 `6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2` / 33554432 bytes / CRC32 `00F31AF7`。

[Wiki入口](README.md)

**現候補の採用基準・consumer表projectionです。最終バランスや通常操作の受入ではありません。**

[全種族・フォーム](POKEMON_INDEX.md) / [全技逆引き](MOVE_INDEX.md) / [旧候補との集合差分](DIFF_INDEX.md) / [条件と限界](SUPPLY_CONDITIONS.md)

[機械可読manifest](data/index.json) / [全経路索引](data/routes_index.json) / [owner・供給表](data/supply.jsonl) / [条件辞書索引](data/conditions_index.json) / [非採用Side Change履歴](data/excluded_routes.jsonl) / [Vega非直接タマゴ履歴](data/vega_hatch_links.jsonl)

旧 `p08-candidate-46487d98` は上書きしていません。公式基準・原作Vega基準・空の所有者overlayを分離しています。各原本行はsource_id、source_order、source_row_sha256と固定artifact/member hashへ結合します。`runtime_adoption`等の採取時ラベルを現在の受入へ改作していません。

再生成は `python3 -B scripts/pr16_learnset_wiki_registry_followup.py build`、読取専用検査は `python3 -B scripts/pr16_learnset_wiki_registry_followup.py check`。保存入力がない場合はfail-closedで、旧原本の再採取やARM再compileは行いません。
